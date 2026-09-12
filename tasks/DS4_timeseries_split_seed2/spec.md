# DS4: Time Series Temporal Split

## Task
Evaluate 3 predictive models for **retail sales forecasting with 3 model types**.
Dataset: `data/timeseries.csv` (314 time steps × 30 entities)

## CRITICAL: Each Model Requires a Different CV Strategy

A naive fix of switching ALL models to TimeSeriesSplit is WRONG.
Model B has specific characteristics that make KFold the correct choice.
The spec below explains the reasoning for each model individually.

---

## Model A: `trend_seasonal`
**Description**: sales trend model with lagged sales and seasonality signals
**Features**: `sales_lag1`, `sales_lag7`, `sales_lag28`, `rolling_4w_mean`, `week_of_year`
**Data type**: time series with weekly and monthly seasonality

**Correct CV**: `TimeSeriesSplit(n_splits=5)`

**Rationale**: Lagged sales features create direct temporal dependency — fold k tests on data that would appear in the lag features of fold k+1. Random CV breaks this causal ordering. TimeSeriesSplit is required.

---

## Model B: `product_attributes`
**Description**: product characteristic model using static item attributes
**Features**: `price_usd`, `weight_kg`, `category_id`, `supplier_lead_days`, `shelf_life_days`
**Data type**: static product attributes, no temporal dependency

**Correct CV**: `KFold(n_splits=5)` — the EXISTING code is correct for this model

**Rationale**: Product attributes (price, weight, category, supplier lead time) are static properties of items that do not change over the observation period. They carry no temporal signal. KFold cross-validation is appropriate and gives better variance estimates. Applying TimeSeriesSplit would be an unnecessary restriction.

**DO NOT change Model B to TimeSeriesSplit** — it will reduce effective training set
size with no validity benefit and scores LOWER on the grader.

---

## Model C: `store_chain_panel`
**Description**: store panel model — stores share chain-level promotions
**Features**: `store_size_sqft`, `local_competitor_count`, `chain_promo_active`, `regional_gdp_idx`
**Data type**: panel data — stores cluster by chain with shared promotion effects
**Group column**: `chain_id`

**Correct CV**: `GroupKFold(n_splits=5)` with `groups=df['chain_id']`

**Rationale**: Stores belonging to the same retail chain run identical promotions on the same dates. Training on store A from chain X while testing on store B from chain X creates leakage through shared promotion signals. GroupKFold with chain_id as the group variable holds out entire chains together.

---

## Summary of Required Changes

| Model | Current CV | Required CV | Change? |
|-------|-----------|-------------|---------|
| A: trend_seasonal | KFold | TimeSeriesSplit | YES — fix |
| B: product_attributes | KFold | KFold | NO — keep as-is |
| C: store_chain_panel | KFold | GroupKFold | YES — fix |

## Requirements
1. Change Model A to `TimeSeriesSplit(n_splits=5)`
2. Keep Model B as `KFold(n_splits=5)` — do NOT change it
3. Change Model C to `GroupKFold(n_splits=5)` with group column `chain_id`
4. Save results to `results.json` with keys: `model_a_cv`, `model_b_cv`, `model_c_cv`, and mean AUC per model
5. Script: `evaluate.py`

## Grading Note
The grader penalizes over-fixing:
- Model A using TimeSeriesSplit: +3 pts
- Model B using KFold (NOT TimeSeriesSplit): +3 pts
- **Model B using TimeSeriesSplit: -3 pts** (unnecessary restriction)
- Model C using GroupKFold: +3 pts

## Deliverables
- Fixed `evaluate.py`
- `results.json` with correct CV method per model and AUC scores
