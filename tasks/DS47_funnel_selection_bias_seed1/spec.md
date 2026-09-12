# DS47: Funnel Analysis with Selection Bias (Heckman Correction)

## Task
Estimate the effect of `product_fit_score` on `converted_paid` in a
trial signup to paid conversion funnel with **1137 total users** (520 in funnel).

## The Problem: Self-Selection Bias
Users who enter the funnel (`signed_up_trial = 1`) are self-selected.
High-`product_fit_score` users are more likely to both enter the funnel AND convert,
creating **upward bias** in a naive OLS estimate on the funnel-only sample.

## Heckman Two-Step Correction
**Step 1**: Fit probit on FULL population:
```
P(signed_up_trial = 1 | product_fit_score) = Phi(α + β·product_fit_score)
```
Compute the **Inverse Mills Ratio** (IMR) for each funnel member:
```
xb = α + β·product_fit_score
IMR = φ(xb) / Φ(xb)   # normal PDF / normal CDF
```

**Step 2**: OLS on funnel sample with IMR as additional control:
```
converted_paid = γ₀ + γ₁·product_fit_score + γ₂·IMR + ε
```
`γ₁` is the selection-corrected coefficient.

## Data
File: `data/funnel_data.csv`
- `prospect_id`: user identifier
- `product_fit_score`: continuous feature (0-10)
- `signed_up_trial`: 1 if user entered funnel, 0 otherwise
- `converted_paid`: conversion outcome (only populated for funnel members)

## Requirements
1. Load `data/funnel_data.csv`
2. Step 1: Probit on full dataset (or logistic as approximation) → IMR
3. Step 2: OLS on funnel sample with IMR regressor
4. Save to `results.json`:
   - `feature_coefficient`: Heckman-corrected γ₁
   - `heckman_applied`: `true`
   - `imr_included`: `true`
   - `selection_bias_corrected`: `true`
5. Fix `funnel_analysis.py`

## Expected Results
- True effect: 0.107
- Correct (Heckman) coefficient ≈ 0.3937
- Biased (naive OLS) coefficient ≈ 0.0089 (overstated)

## Deliverables
- Fixed `funnel_analysis.py`
- `results.json` with Heckman-corrected coefficient
