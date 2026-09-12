# DS47: Funnel Analysis with Selection Bias (Heckman Correction)

## Task
Estimate the effect of `engagement_score` on `converted` in a
ad click-to-conversion funnel analysis with **1864 total users** (857 in funnel).

## The Problem: Self-Selection Bias
Users who enter the funnel (`clicked_ad = 1`) are self-selected.
High-`engagement_score` users are more likely to both enter the funnel AND convert,
creating **upward bias** in a naive OLS estimate on the funnel-only sample.

## Heckman Two-Step Correction
**Step 1**: Fit probit on FULL population:
```
P(clicked_ad = 1 | engagement_score) = Phi(α + β·engagement_score)
```
Compute the **Inverse Mills Ratio** (IMR) for each funnel member:
```
xb = α + β·engagement_score
IMR = φ(xb) / Φ(xb)   # normal PDF / normal CDF
```

**Step 2**: OLS on funnel sample with IMR as additional control:
```
converted = γ₀ + γ₁·engagement_score + γ₂·IMR + ε
```
`γ₁` is the selection-corrected coefficient.

## Data
File: `data/funnel_data.csv`
- `user_id`: user identifier
- `engagement_score`: continuous feature (0-10)
- `clicked_ad`: 1 if user entered funnel, 0 otherwise
- `converted`: conversion outcome (only populated for funnel members)

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
- True effect: 0.089
- Correct (Heckman) coefficient ≈ 0.3347
- Biased (naive OLS) coefficient ≈ 0.0149 (overstated)

## Deliverables
- Fixed `funnel_analysis.py`
- `results.json` with Heckman-corrected coefficient
