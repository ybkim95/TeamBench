# DS48: Revenue Forecasting with Price Elasticity

## Task
Forecast total revenue after a **12% price increase** across
**23 hotel rooms** in hotel room pricing and revenue optimization.

## The Bug
The script assumes demand is **constant** after a price change:
```python
new_demand = old_demand   # WRONG: ignores demand response
revenue = new_demand * new_price
```

## Price Elasticity of Demand
The correct formula accounts for demand change:
```
new_demand = old_demand × (new_price / old_price)^elasticity
revenue = new_demand × new_price
```

Where `elasticity` is the price elasticity (typically negative):
- Elastic (elasticity < -1): price ↑ → revenue ↓
- Inelastic (-1 < elasticity < 0): price ↑ → revenue ↑
- Mean elasticity for this dataset: -1.708

## Data
File: `data/product_pricing.csv`
- `property_id`: product identifier
- `old_price`: current price
- `old_demand`: current demand (bookings)
- `elasticity`: price elasticity of demand (negative)
- `new_price`: proposed new price

## Requirements
1. Load `data/product_pricing.csv`
2. For each product: `new_demand = old_demand * (new_price / old_price) ^ elasticity`
3. Compute `forecast_revenue = new_demand * new_price` per product
4. Save to `results.json`:
   - `elasticity_applied`: `true`
   - `total_forecast_revenue`: sum of forecast revenues
   - `revenue_change_pct`: `(total_new - total_old) / total_old`
   - `avg_demand_change_pct`: average percentage change in demand
5. Fix `revenue_forecast.py`

## Expected Results
- Correct forecast revenue ≈ 923,274.94
- Buggy (constant demand) revenue ≈ 1,120,836.29 (overstated by 197,561.35)

## Deliverables
- Fixed `revenue_forecast.py`
- `results.json` with elasticity-adjusted revenue forecast
