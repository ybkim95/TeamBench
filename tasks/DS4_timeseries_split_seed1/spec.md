# DS4: Time Series Temporal Split

## Task
Evaluate 3 predictive models for **power grid demand forecasting with 3 model types**.
Dataset: `data/timeseries.csv` (334 time steps × 15 entities)

## CRITICAL: Each Model Requires a Different CV Strategy

A naive fix of switching ALL models to TimeSeriesSplit is WRONG.
Model B has specific characteristics that make KFold the correct choice.
The spec below explains the reasoning for each model individually.

---

## Model A: `ARIMA_demand`
**Description**: hourly demand model with strong temporal autocorrelation
**Features**: `hour_lag1`, `hour_lag24`, `hour_lag168`, `rolling_7d_mean`, `trend_index`
**Data type**: time series with strong seasonal autocorrelation

**Correct CV**: `TimeSeriesSplit(n_splits=5)`

**Rationale**: Lag features (lag1, lag24, lag168) create strong autocorrelation. Random CV would train on summer data while testing on winter, mixing temporal contexts. TimeSeriesSplit maintains the temporal ordering required for valid evaluation.

---

## Model B: `weather_static`
**Description**: weather snapshot model — temperature/humidity at query time only
**Features**: `temperature_c`, `humidity_pct`, `cloud_cover_pct`, `wind_speed_ms`
**Data type**: independent weather measurements, no autocorrelation

**Correct CV**: `KFold(n_splits=5)` — the EXISTING code is correct for this model

**Rationale**: Weather snapshot features (temperature, humidity, cloud cover) are independent readings with no meaningful temporal autocorrelation — tomorrow's temperature measurement does not 'remember' yesterday's in this feature encoding. Standard KFold provides unbiased CV; TimeSeriesSplit would only reduce effective training set size unnecessarily.

**DO NOT change Model B to TimeSeriesSplit** — it will reduce effective training set
size with no validity benefit and scores LOWER on the grader.

---

## Model C: `zone_panel`
**Description**: multi-zone panel model — correlated zones share regional confounders
**Features**: `zone_capacity_pct`, `neighbour_demand`, `grid_frequency`, `import_export_mw`
**Data type**: panel data — multiple zones share regional dependencies
**Group column**: `region_id`

**Correct CV**: `GroupKFold(n_splits=5)` with `groups=df['region_id']`

**Rationale**: Zones within the same region have correlated demand due to shared weather and industrial patterns. Random CV leaks information across zones in the same region. GroupKFold with region_id as the grouping variable prevents data leakage across regional zone clusters.

---

## Summary of Required Changes

| Model | Current CV | Required CV | Change? |
|-------|-----------|-------------|---------|
| A: ARIMA_demand | KFold | TimeSeriesSplit | YES — fix |
| B: weather_static | KFold | KFold | NO — keep as-is |
| C: zone_panel | KFold | GroupKFold | YES — fix |

## Requirements
1. Change Model A to `TimeSeriesSplit(n_splits=5)`
2. Keep Model B as `KFold(n_splits=5)` — do NOT change it
3. Change Model C to `GroupKFold(n_splits=5)` with group column `region_id`
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
