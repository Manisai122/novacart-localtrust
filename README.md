# NOVA CART LocalTrust

LocalTrust is a functional Flask + SQLite prototype for the PromptWars Business Rescue Challenge. It tackles NOVA CART's fulfilment-trust loop: product unavailability drives 35% of cancellations, partner inventory upkeep is burdensome, and repeat purchase fell from 41% to 27%.

## What works

- Customers search nearby products, compare fulfilment confidence, keep a one-store basket, and place a server-validated order.
- Partners update stock, see high-demand products, and advance orders through a controlled fulfilment flow.
- The confidence signal uses stock, recency of the stock update, store reliability, and busy status. It is recalculated by the server at checkout.
- The Impact view connects the intervention to the case evidence and six-month measures.

## Run

```powershell
python -m pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

## Deploy to Render

1. Create a GitHub repository and push this project to it.
2. In Render, choose **New +** → **Blueprint** and connect the repository.
3. Render reads `render.yaml`, installs the dependencies, and starts the app with Gunicorn.
4. Open the public URL supplied by Render after the deployment completes.

The app uses SQLite demo data. On hosting plans without persistent storage, the data can reset when the service restarts; use **Reset demo data** to restore the presentation state.

## Verify

```powershell
python -m unittest -v
```

The tests use an isolated temporary database and do not change `novacart.db`.

## Demo script

1. In **Shop confidently**, add Milk and Bananas from Green Basket, then place the order. Note the confidence score and ETA.
2. In **Partner Console**, update a stock count and accept/advance the new order.
3. In **Impact**, explain how inventory freshness prevents unavailable-product cancellations. Use **Reset demo data** before a fresh presentation.

## Prompt journey

1. Given the NOVA CART case, distinguish root causes from surface metrics and rank interventions by likely retention impact, cost, and feasibility under INR 25 lakh.
2. Challenge the acquisition-first hypothesis using the churn, cancellation, inventory, and partner evidence. What single product loop has the strongest causal link to repeat orders?
3. Design the smallest functional product that makes local-store availability more trustworthy for customers while reducing manual partner effort. Define user inputs, decision logic, and measurable outputs.

## Target impact

Within six months, LocalTrust targets a 30% reduction in unavailable-product cancellations, 20% fewer related support tickets, a 5-point lift in second-order conversion, and more than 90% of active SKUs updated within 24 hours. It builds on existing systems without warehouses, mass hiring, or deeper discounts.
