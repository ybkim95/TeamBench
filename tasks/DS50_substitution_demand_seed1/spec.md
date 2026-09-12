# DS50: Inventory Demand Forecasting with Stockout Censoring (Tobit)

## Task
Forecast total demand for **19 accessorys** over **96 days**
in electronics accessories demand with stockout censoring.

## The Problem: Censored Observations
On stockout days (`is_stockout = 1`), `observed_sales` does NOT equal true demand —
the product sold out and additional demand went unmet. These are **left-censored**
observations: true demand ≥ observed sales.

Including stockout days as `demand = 0` in an OLS average **understates true demand**
by approximately 20.4%.

## Tobit Correction (Simple Approximation)
For each product:
1. Compute `avg_clean_demand` from non-stockout days only
2. For stockout days, impute demand as `avg_clean_demand × (1 + stockout_rate)`
   (stockouts correlate with high-demand periods)
3. Total demand = n_normal_days × avg_clean_demand + n_stockout_days × imputed_demand

## Data
File: `data/sales_inventory.csv`
- `sku_id`: product identifier
- `day`: day number (1 to 96)
- `observed_sales`: sales observed (may be censored on stockout days)
- `is_stockout`: 1 if product stocked out that day, 0 otherwise
- `stock_level`: inventory level at start of day

## Requirements
1. Load `data/sales_inventory.csv`
2. For each product:
   - Compute `avg_clean_demand` from days where `is_stockout = 0`
   - Impute stockout days: `imputed = avg_clean_demand × (1 + stockout_rate)`
   - `total_forecast = n_clean × avg_clean + n_stockout × imputed`
3. Save to `results.json`:
   - `stockout_censoring_handled`: `true`
   - `tobit_applied`: `true`
   - `total_forecast_demand`: corrected total forecast
   - `forecast_by_product`: dict product_id -> corrected forecast
4. Use `stockout_rate = 0.227` as the imputation adjustment
5. Fix `demand_forecast.py`

## Expected Results
- Correct (Tobit) total forecast ≈ 118,375.02
- Biased (OLS with stockouts) forecast ≈ 94,230.70
- Understatement: 24,144.32 (20.4%)
- Stockout observations in dataset: 407

## Deliverables
- Fixed `demand_forecast.py`
- `results.json` with Tobit-corrected demand forecast
