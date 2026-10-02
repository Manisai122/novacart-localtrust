from datetime import datetime, timedelta
import os
import sqlite3

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
DB = os.path.join(os.path.dirname(__file__), "novacart.db")


def conn():
    connection = sqlite3.connect(DB, timeout=5)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def query(sql, args=(), one=False):
    connection = conn()
    try:
        rows = connection.execute(sql, args).fetchall()
        data = [dict(row) for row in rows]
        return (data[0] if data else None) if one else data
    finally:
        connection.close()


def init_db():
    connection = conn()
    try:
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS stores(id INTEGER PRIMARY KEY, name TEXT NOT NULL, area TEXT NOT NULL, score INTEGER NOT NULL CHECK(score BETWEEN 0 AND 100), update_hours INTEGER NOT NULL, busy INTEGER NOT NULL DEFAULT 0 CHECK(busy IN (0,1)));
            CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY, name TEXT NOT NULL, category TEXT NOT NULL, price REAL NOT NULL CHECK(price >= 0), store_id INTEGER NOT NULL, stock INTEGER NOT NULL CHECK(stock >= 0), last_updated TEXT NOT NULL, demand INTEGER NOT NULL DEFAULT 0 CHECK(demand BETWEEN 0 AND 100), FOREIGN KEY(store_id) REFERENCES stores(id));
            CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY AUTOINCREMENT, customer TEXT NOT NULL, store_id INTEGER NOT NULL, items INTEGER NOT NULL CHECK(items > 0), total REAL NOT NULL CHECK(total >= 0), status TEXT NOT NULL, created_at TEXT NOT NULL, eta INTEGER NOT NULL, confidence INTEGER NOT NULL, issue TEXT DEFAULT '', FOREIGN KEY(store_id) REFERENCES stores(id));
            CREATE TABLE IF NOT EXISTS inventory_log(id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER NOT NULL, action TEXT NOT NULL, created_at TEXT NOT NULL, FOREIGN KEY(product_id) REFERENCES products(id));
        """)
        if not connection.execute("SELECT 1 FROM stores LIMIT 1").fetchone():
            now = datetime.now().isoformat()
            connection.executemany("INSERT INTO stores VALUES (?,?,?,?,?,?)", [(1, "Green Basket", "Indiranagar", 94, 2, 0), (2, "HealthHub Pharmacy", "Indiranagar", 88, 8, 0), (3, "Daily Needs", "Koramangala", 72, 31, 1), (4, "Baker Street", "Indiranagar", 91, 4, 0)])
            connection.executemany("INSERT INTO products VALUES (?,?,?,?,?,?,?,?)", [(1, "Amul Taaza Milk 1L", "Dairy", 62, 1, 18, now, 74), (2, "Farm Fresh Bananas", "Fresh produce", 48, 1, 7, now, 91), (3, "Aashirvaad Atta 5kg", "Staples", 285, 1, 4, now, 48), (4, "Paracetamol 500mg", "Pharmacy", 28, 2, 31, now, 62), (5, "Vitamin C Tablets", "Pharmacy", 199, 2, 0, now, 39), (6, "Sourdough Loaf", "Bakery", 120, 4, 9, now, 80), (7, "Chocolate Croissant", "Bakery", 85, 4, 3, now, 66), (8, "Basmati Rice 5kg", "Staples", 540, 3, 2, (datetime.now() - timedelta(days=2)).isoformat(), 58), (9, "Tomatoes 500g", "Fresh produce", 36, 3, 0, (datetime.now() - timedelta(days=2)).isoformat(), 96)])
            connection.executemany("INSERT INTO orders(customer,store_id,items,total,status,created_at,eta,confidence,issue) VALUES (?,?,?,?,?,?,?,?,?)", [("Asha", 1, 3, 395, "Delivered", now, 26, 94, ""), ("Ravi", 3, 2, 576, "Store review", now, 42, 54, "Stock requires confirmation"), ("Mira", 2, 1, 28, "Delivered", now, 24, 88, ""), ("Dev", 1, 2, 110, "Picking", now, 28, 91, "")])
        connection.commit()
    finally:
        connection.close()


def product_signal(product):
    age = max(0, (datetime.now() - datetime.fromisoformat(product["last_updated"])).total_seconds() / 3600)
    confidence = 0 if product["stock"] == 0 else max(35, min(98, product["score"] - int(age * 1.1) - (18 if product["busy"] else 0) + (5 if product["stock"] > 5 else 0)))
    return round(age, 1), confidence, 22 + (100 - product["score"]) // 3 + (10 if product["busy"] else 0)


@app.get("/")
def index(): return render_template("index.html")


@app.get("/api/summary")
def summary():
    connection = conn()
    try:
        total = connection.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        risky = connection.execute("SELECT COUNT(*) FROM products WHERE stock=0 OR julianday('now')-julianday(last_updated)>1").fetchone()[0]
        fresh = connection.execute("SELECT COUNT(*) FROM products WHERE stock>0 AND julianday('now')-julianday(last_updated)<=1").fetchone()[0]
    finally: connection.close()
    return jsonify(orders=total, fresh=fresh, risky=risky, cancellation_risk=round(risky / (fresh + risky) * 100) if fresh + risky else 0, insight="Prioritize high-demand products with stale stock: this prevents the largest source of cancellations.")


@app.get("/api/products")
def products():
    term, category = request.args.get("q", "").strip().lower(), request.args.get("category", "").strip()
    rows = query("""SELECT p.*,s.name store,s.area,s.score,s.busy FROM products p JOIN stores s ON p.store_id=s.id WHERE lower(p.name) LIKE ? AND (?='' OR p.category=?) ORDER BY s.score DESC,p.demand DESC""", (f"%{term}%", category, category))
    for row in rows:
        age, confidence, eta = product_signal(row)
        row.update(age_hours=age, confidence=confidence, eta=eta)
    return jsonify(rows)


@app.get("/api/partner/overview")
def partner_overview():
    return jsonify(products=query("SELECT p.*,s.name store,round((julianday('now')-julianday(p.last_updated))*24,1) age_hours FROM products p JOIN stores s ON p.store_id=s.id WHERE p.store_id=1 ORDER BY p.demand DESC"), orders=query("SELECT o.*,s.name store FROM orders o JOIN stores s ON o.store_id=s.id WHERE o.store_id=1 AND o.status NOT IN ('Delivered','Cancelled') ORDER BY o.id DESC"), watchlist=query("SELECT p.name,p.demand,p.stock FROM products p WHERE p.store_id=1 ORDER BY p.demand DESC LIMIT 3"))


@app.post("/api/inventory/<int:pid>")
def inventory(pid):
    try: stock = int((request.get_json(silent=True) or {}).get("stock"))
    except (TypeError, ValueError): return jsonify(error="Stock must be a whole number."), 400
    if stock < 0: return jsonify(error="Stock cannot be negative."), 400
    connection = conn()
    try:
        if not connection.execute("SELECT 1 FROM products WHERE id=?", (pid,)).fetchone(): return jsonify(error="Product not found."), 404
        now = datetime.now().isoformat()
        connection.execute("UPDATE products SET stock=?,last_updated=? WHERE id=?", (stock, now, pid))
        connection.execute("INSERT INTO inventory_log(product_id,action,created_at) VALUES (?,?,?)", (pid, f"Updated to {stock}", now))
        connection.commit()
    finally: connection.close()
    return jsonify(ok=True, message="Inventory updated. Shopper confidence recalculated instantly.")


@app.post("/api/orders")
def create_order():
    ids = (request.get_json(silent=True) or {}).get("product_ids")
    if not isinstance(ids, list) or not ids: return jsonify(error="Choose at least one product."), 400
    if not all(isinstance(i, int) and not isinstance(i, bool) for i in ids): return jsonify(error="Product IDs must be whole numbers."), 400
    if len(ids) > 20: return jsonify(error="A demo order can contain at most 20 products."), 400
    quantities = {pid: ids.count(pid) for pid in set(ids)}
    connection, marks = conn(), ",".join("?" * len(quantities))
    try:
        connection.execute("BEGIN IMMEDIATE")
        selected = connection.execute(f"SELECT p.*,s.score,s.busy FROM products p JOIN stores s ON p.store_id=s.id WHERE p.id IN ({marks})", tuple(quantities)).fetchall()
        if len(selected) != len(quantities) or any(p["stock"] < quantities[p["id"]] for p in selected):
            connection.rollback(); return jsonify(error="One or more products are no longer confirmed available. Refresh your basket."), 409
        if len({p["store_id"] for p in selected}) != 1:
            connection.rollback(); return jsonify(error="Choose products from one store for a reliable single-store delivery."), 400
        age = max((datetime.now() - datetime.fromisoformat(p["last_updated"])).total_seconds() / 3600 for p in selected)
        confidence = max(45, min(98, selected[0]["score"] - int(age) - (15 if selected[0]["busy"] else 0) + 5))
        eta, now = 22 + (100 - selected[0]["score"]) // 3 + (10 if selected[0]["busy"] else 0), datetime.now().isoformat()
        cursor = connection.execute("INSERT INTO orders(customer,store_id,items,total,status,created_at,eta,confidence) VALUES (?,?,?,?,?,?,?,?)", ("Demo Customer", selected[0]["store_id"], len(ids), sum(p["price"] * quantities[p["id"]] for p in selected), "Store review", now, eta, confidence))
        connection.executemany("UPDATE products SET stock=stock-? WHERE id=? AND stock>=?", [(quantities[p["id"]], p["id"], quantities[p["id"]]) for p in selected])
        store = connection.execute("SELECT name FROM stores WHERE id=?", (selected[0]["store_id"],)).fetchone()
        connection.commit()
    except Exception:
        connection.rollback(); raise
    finally: connection.close()
    return jsonify(ok=True, order_id=cursor.lastrowid, eta=eta, confidence=confidence, message=f"Order sent to {store['name']} for quick confirmation.")


@app.post("/api/orders/<int:oid>/status")
def status(oid):
    action = (request.get_json(silent=True) or {}).get("status")
    transitions = {"Store review": {"Accepted", "Cancelled"}, "Accepted": {"Picking", "Cancelled"}, "Picking": {"Out for delivery", "Cancelled"}, "Out for delivery": {"Delivered", "Cancelled"}}
    connection = conn()
    try:
        order = connection.execute("SELECT status FROM orders WHERE id=?", (oid,)).fetchone()
        if not order: return jsonify(error="Order not found."), 404
        if action not in transitions.get(order["status"], set()): return jsonify(error="That order cannot move to the requested status."), 400
        connection.execute("UPDATE orders SET status=? WHERE id=?", (action, oid)); connection.commit()
    finally: connection.close()
    return jsonify(ok=True, status=action)


@app.post("/api/reset")
def reset():
    if (request.get_json(silent=True) or {}).get("confirm") is not True: return jsonify(error="Send confirm: true to reset the demo data."), 400
    if os.path.exists(DB): os.remove(DB)
    init_db()
    return jsonify(ok=True, message="Demo data restored to its original state.")


if __name__ == "__main__":
    init_db()
    app.run(debug=os.getenv("FLASK_DEBUG") == "1", port=5000)
