# DS18: Simpson's Paradox — Confounder vs Collider

## Task
Estimate the **causal average treatment effect (ATE)** of `top_university`
on `job_performance` for effect of university prestige on job performance (568 observations).

## Causal DAG
SES -> top_university AND performance (confounder). University AND performance -> hired (collider).

**Variables**:
- `top_university`: binary treatment (0/1)
- `job_performance`: continuous outcome
- `socioeconomic_status`: **confounder** — causes both treatment and outcome → MUST adjust
- `hired`: **collider** — caused by both treatment and outcome → must NOT adjust

## Correct Adjustment Strategy
| Variable | Type | Adjust? | Why |
|----------|------|---------|-----|
| `socioeconomic_status` | Confounder | YES | Blocks backdoor path |
| `hired` | Collider | NO | Conditioning opens spurious path |

## Requirements
1. Load `data/causal_data.csv` (full dataset — do NOT subset on `hired`)
2. Fit OLS on the FULL dataset with `socioeconomic_status` as control:
   ```python
   X = [intercept, socioeconomic_status, top_university]
   y = job_performance
   ```
3. The treatment coefficient is the ATE estimate
4. Save to `results.json`:
   - `ate_estimate`: causal effect estimate (should be > 0)
   - `adjustment_set`: `["socioeconomic_status"]` (confounder only, NOT collider)
   - `conditioned_on_collider`: `false`
   - `n_used`: 568 (full dataset)
   - `method`: `"confounder_adjusted"`
5. Fix `analysis.py`

## Expected Results
- True ATE ≈ 0.271
- Naive (unadjusted) estimate ≈ 0.017 (biased by confounder)
- Correct estimate should be in range [0.04, 0.80]

## Deliverables
- Fixed `analysis.py` with correct adjustment set
- `results.json` with unbiased ATE estimate
