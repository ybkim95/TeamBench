# DS47: Funnel Analysis with Selection Bias (Heckman Correction)

## Task
Estimate the effect of `intent_score` on `closed_deal` in a
demo request to deal close funnel analysis with **1978 total users** (893 in funnel).

## The Problem: Self-Selection Bias
Users who enter the funnel (`requested_demo = 1`) are self-selected.
High-`intent_score` users are more likely to both enter the funnel AND convert,
creating **upward bias** in a naive OLS estimate on the funnel-only sample.

## Heckman Two-Step Correction
**Step 1**: Fit probit on FULL population:
```
P(requested_demo = 1 | intent_score) = Phi(α + β·intent_score)
```
Compute the **Inverse Mills Ratio** (IMR) for each funnel member:
```
xb = α + β·intent_score
IMR = φ(xb) / Φ(xb)   # normal PDF / normal CDF
```

**Step 2**: OLS on funnel sample with IMR as additional control:
```
closed_deal = γ₀ + γ₁·intent_score + γ₂·IMR + ε
```
`γ₁` is the selection-corrected coefficient.

## Data
File: `data/funnel_data.csv`
- `lead_id`: user identifier
- `intent_score`: continuous feature (0-10)
- `requested_demo`: 1 if user entered funnel, 0 otherwise
- `closed_deal`: conversion outcome (only populated for funnel members)

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
- True effect: 0.136
- Correct (Heckman) coefficient ≈ 0.1672
- Biased (naive OLS) coefficient ≈ 0.0199 (overstated)

## Deliverables
- Fixed `funnel_analysis.py`
- `results.json` with Heckman-corrected coefficient
