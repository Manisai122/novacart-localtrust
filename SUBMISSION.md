# NOVA CART LocalTrust — Submission Pack

## 1. Problem diagnosis

NOVA CART's primary problem is a broken fulfilment-trust loop, not insufficient acquisition. Product unavailability causes 35% of cancellations; cancellations rose from 6% to 11%; delivery time rose from 29 to 37 minutes; and repeat purchase fell from 41% to 27%. Maintaining inventory is burdensome for 39% of partner stores, while 29% of customers have seen an available item become unavailable after ordering.

This deserves priority because 61% of churned customers had previously rated NOVA CART at least four stars. The service is losing customers after acquisition. NOVA CART's local-store assortment becomes a defensible advantage only when customers can trust it.

## 2. Prompt journey

1. Given the NOVA CART case, distinguish root causes from surface metrics and rank interventions by retention impact, cost, and feasibility under the INR 25 lakh limit.
2. Challenge the acquisition-first hypothesis using the churn, cancellation, inventory, and partner evidence. What single product loop has the strongest causal link to repeat orders?
3. Design the smallest functional product that makes local-store availability trustworthy for customers while reducing manual partner effort. Define inputs, decision logic, and measurable outputs.

These prompts directed the product toward reliable local inventory rather than more acquisition promotions.

## 3. Solution

**LocalTrust** is a two-sided local-commerce reliability layer.

- Customers search nearby products, see fulfilment confidence and delivery estimates, build a single-store basket, and receive a server-validated order outcome.
- Partner stores update stock in a fast console, see a demand-prioritised watchlist, and advance orders through valid fulfilment states.
- Confidence combines stock state, stock-update age, store reliability, and busy status. It is recalculated during checkout rather than trusted from the UI.

The Flask and SQLite application uses seeded data for four local stores, nine products, and operational orders. It has a clean reset flow for repeatable demos and automated tests for the critical API paths.

## 4. Functional demo

1. Add Milk and Bananas from Green Basket, then create an order.
2. In Partner Console, update stock and accept/advance the incoming order.
3. In Impact, show live inventory-risk metrics and explain the intended business outcomes.

## 5. Business impact and measurement

| Outcome | Target | Measurement |
| --- | --- | --- |
| Unavailable-product cancellations | 30% reduction | Cancellation reason by month |
| Related support tickets | 20% reduction | Missing/unavailable-product ticket volume |
| Second order within 30 days | +5 percentage points | Customer cohort analysis |
| Inventory freshness | >90% of active SKUs updated within 24 hours | Partner inventory timestamps |

The intervention uses existing application, partner-dashboard, order/customer, delivery, and coupon systems. It needs no warehouses, mass hiring, or deeper discounts, so it fits the six-month ₹25 lakh implementation constraint.
