# DS4: Time Series Temporal Split

## Task
Evaluate 3 predictive models for **portfolio return forecasting with 3 model types**.
Dataset: `data/timeseries.csv` (398 time steps × 20 entities)

## CRITICAL: Each Model Requires a Different CV Strategy

A naive fix of switching ALL models to TimeSeriesSplit is WRONG.
Model B has specific characteristics that make KFold the correct choice.
The spec below explains the reasoning for each model individually.

---

## Model A: `LSTM_momentum`
**Description**: momentum signal model using lagged returns
**Features**: `lag1_return`, `lag5_return`, `lag20_return`, `rsi_14`, `macd_signal`
**Data type**: time series with strong autocorrelation

**Correct CV**: `TimeSeriesSplit(n_splits=5)`

**Rationale**: The momentum features are lagged returns. Random CV would let fold 3 train on 2023 data and test on 2021 — future signal leaks into past evaluation. TimeSeriesSplit is required to preserve temporal ordering.

---

## Model B: `fundamental_static`
**Description**: company fundamentals model (quarterly rebalanced, no autocorrelation)
**Features**: `pe_ratio`, `pb_ratio`, `roe`, `debt_equity`, `market_cap_log`
**Data type**: static cross-sectional features with quarterly refresh

**Correct CV**: `KFold(n_splits=5)` — the EXISTING code is correct for this model

**Rationale**: Fundamental ratios (P/E, P/B, ROE) are cross-sectional company attributes refreshed quarterly. They have no meaningful autocorrelation across the daily time axis. Random KFold is valid and actually gives better variance estimates than TimeSeriesSplit for this feature type. Using TimeSeriesSplit here artificially reduces training data without benefit.

**DO NOT change Model B to TimeSeriesSplit** — it will reduce effective training set
size with no validity benefit and scores LOWER on the grader.

---

## Model C: `sector_panel`
**Description**: sector-level panel model with multiple tickers per sector
**Features**: `sector_momentum`, `sector_volatility`, `peer_correlation`, `sector_pe`
**Data type**: panel data — multiple entities (tickers) per group (sector)
**Group column**: `sector_id`

**Correct CV**: `GroupKFold(n_splits=5)` with `groups=df['sector_id']`

**Rationale**: The panel model has multiple tickers in the same sector. Random CV will leak information across tickers in the same sector (train on AAPL, test on MSFT in the same tech sector). GroupKFold with sector_id as the group ensures entire sectors are held out together.

---

## Summary of Required Changes

| Model | Current CV | Required CV | Change? |
|-------|-----------|-------------|---------|
| A: LSTM_momentum | KFold | TimeSeriesSplit | YES — fix |
| B: fundamental_static | KFold | KFold | NO — keep as-is |
| C: sector_panel | KFold | GroupKFold | YES — fix |

## Requirements
1. Change Model A to `TimeSeriesSplit(n_splits=5)`
2. Keep Model B as `KFold(n_splits=5)` — do NOT change it
3. Change Model C to `GroupKFold(n_splits=5)` with group column `sector_id`
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
