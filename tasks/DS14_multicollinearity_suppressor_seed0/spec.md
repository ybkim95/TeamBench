# DS14: Multicollinearity — Suppressor Variable Effect

## Task
Investigate multicollinearity in a housing price prediction dataset (497 observations)
and determine whether removing high-VIF features actually improves the model.

## The Suppressor Variable Problem
The standard advice "remove features with VIF > 10" is **wrong** here.

Variables `sqft` and `garage_sqft` are highly collinear (VIF ≈ 13.9).
However, both contribute to predicting `sale_price`:
- `garage_sqft` acts as a **suppressor variable** — it removes noise variance from `sqft`
- Removing it based on VIF alone **reduces R^2** significantly

## Requirements
1. Compute VIF for all predictors in `['sqft', 'age_years', 'bedrooms', 'lot_size', 'garage_sqft']`
2. Fit the **full model** (all predictors) and record R^2
3. Fit the **reduced model** (drop features with VIF > 10) and record R^2
4. Report which approach gives better R^2
5. Save to `results.json`:
   - `vif`: dict of VIF values per feature
   - `features_kept`: features in the model you recommend
   - `r2`: R^2 of the FULL model (should be ≥ 0.739)
   - `r2_full`: full model R^2
   - `r2_reduced`: reduced model R^2 (should be lower than full)
   - `method`: `"full_model"` (use all features despite high VIF)
6. Fix `analysis.py`

## Data
File: `data/dataset.csv` — 497 observations, outcome: `sale_price`

## Key Insight
High VIF does not always mean a feature should be dropped.
Always compare model performance with and without the collinear features.

## Deliverables
- Fixed `analysis.py` that fits full model and reports both R^2 values
- `results.json` with VIF values and correct R^2
