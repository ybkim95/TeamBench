# DS11: Survival Analysis — Censoring Bias

## Task
Compute the correct **median survival time** for a oncology clinical trial measuring patient survival dataset
using Kaplan-Meier estimation. The dataset contains **298 patients**.

## The Problem with Naive Median
The naive approach computes `median(days_to_event)` over all observations.
This is **statistically incorrect** when censored observations are present.

**Why**: Censored subjects are still alive/active at their last observation time.
Their true survival time is *longer* than observed. Including them in a naive
median computation biases the result **downward**.

With ~36% censoring in this dataset, the naive median significantly
underestimates the true median survival.

## Data
File: `data/survival_data.csv`
- `days_to_event`: observed time until event or censoring
- `event_observed`: 1 = event occurred, 0 = censored (subject still alive/active at last observation)

## Requirements
1. Load `data/survival_data.csv`
2. Fit a Kaplan-Meier survival curve using `lifelines.KaplanMeierFitter`
   - `kmf.fit(durations=df['days_to_event'], event_observed=df['event_observed'])`
3. Extract the KM median: `kmf.median_survival_time_`
4. Save results to `results.json` with keys:
   - `median_survival`: KM median (float)
   - `method`: `"kaplan_meier"`
   - `n_subjects`: number of rows
   - `event_rate`: fraction of subjects with event=1
5. Fix `analysis.py` (currently uses naive median — wrong)

## Expected KM Median
Approximately **123.89 days** (±8% tolerance for KM estimator variance).

## Deliverables
- Fixed `analysis.py`
- `results.json` with KM median survival time
