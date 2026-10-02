import os
import unittest

import app as application


class LocalTrustApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_db = application.DB
        application.DB = os.path.join(os.path.dirname(__file__), ".test_novacart.db")
        application.app.config.update(TESTING=True)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(application.DB):
            os.remove(application.DB)
        application.DB = cls.original_db

    def setUp(self):
        if os.path.exists(application.DB):
            os.remove(application.DB)
        application.init_db()
        self.client = application.app.test_client()

    def test_products_expose_a_trust_signal(self):
        response = self.client.get("/api/products?q=milk")
        self.assertEqual(response.status_code, 200)
        product = response.get_json()[0]
        self.assertGreater(product["confidence"], 0)
        self.assertIn("age_hours", product)

    def test_order_reduces_stock_and_creates_order(self):
        before = self.client.get("/api/products?q=milk").get_json()[0]["stock"]
        response = self.client.post("/api/orders", json={"product_ids": [1, 2]})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["ok"])
        after = self.client.get("/api/products?q=milk").get_json()[0]["stock"]
        self.assertEqual(after, before - 1)

    def test_order_rejects_invalid_or_cross_store_baskets(self):
        self.assertEqual(self.client.post("/api/orders", json={"product_ids": [1, 4]}).status_code, 400)

    def test_order_allows_multiple_units_of_the_same_product(self):
        before = self.client.get("/api/products?q=milk").get_json()[0]["stock"]
        response = self.client.post("/api/orders", json={"product_ids": [1, 1]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["ok"], True)
        after = self.client.get("/api/products?q=milk").get_json()[0]["stock"]
        self.assertEqual(after, before - 2)

    def test_status_requires_a_valid_transition(self):
        created = self.client.post("/api/orders", json={"product_ids": [1]}).get_json()["order_id"]
        self.assertEqual(self.client.post(f"/api/orders/{created}/status", json={"status": "Picking"}).status_code, 400)
        self.assertEqual(self.client.post(f"/api/orders/{created}/status", json={"status": "Accepted"}).status_code, 200)

    def test_reset_requires_explicit_confirmation(self):
        self.assertEqual(self.client.post("/api/reset", json={}).status_code, 400)
        self.assertEqual(self.client.post("/api/reset", json={"confirm": True}).status_code, 200)


if __name__ == "__main__":
    unittest.main()
