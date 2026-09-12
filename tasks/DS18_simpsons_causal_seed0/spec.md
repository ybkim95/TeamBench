# DS18: Simpson's Paradox — Confounder vs Collider

## Task
Estimate the **causal average treatment effect (ATE)** of `received_treatment`
on `health_score` for causal effect of medical treatment on health (932 observations).

## Causal DAG
Disease severity -> treatment AND health_score (confounder). Treatment AND health_score -> hospitalized (collider).

**Variables**:
- `received_treatment`: binary treatment (0/1)
- `health_score`: continuous outcome
- `disease_severity`: **confounder** — causes both treatment and outcome → MUST adjust
- `hospitalized`: **collider** — caused by both treatment and outcome → must NOT adjust

## Correct Adjustment Strategy
| Variable | Type | Adjust? | Why |
|----------|------|---------|-----|
| `disease_severity` | Confounder | YES | Blocks backdoor path |
| `hospitalized` | Collider | NO | Conditioning opens spurious path |

## Requirements
1. Load `data/causal_data.csv` (full dataset — do NOT subset on `hospitalized`)
2. Fit OLS on the FULL dataset with `disease_severity` as control:
   ```python
   X = [intercept, disease_severity, received_treatment]
   y = health_score
   ```
3. The treatment coefficient is the ATE estimate
4. Save to `results.json`:
   - `ate_estimate`: causal effect estimate (should be > 0)
   - `adjustment_set`: `["disease_severity"]` (confounder only, NOT collider)
   - `conditioned_on_collider`: `false`
   - `n_used`: 932 (full dataset)
   - `method`: `"confounder_adjusted"`
5. Fix `analysis.py`

## Expected Results
- True ATE ≈ 0.216
- Naive (unadjusted) estimate ≈ -0.005 (biased by confounder)
- Correct estimate should be in range [0.04, 0.80]

## Deliverables
- Fixed `analysis.py` with correct adjustment set
- `results.json` with unbiased ATE estimate
