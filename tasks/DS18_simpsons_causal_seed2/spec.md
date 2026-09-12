# DS18: Simpson's Paradox — Confounder vs Collider

## Task
Estimate the **causal average treatment effect (ATE)** of `full_adherence`
on `symptom_reduction` for effect of medication adherence on symptom reduction (989 observations).

## Causal DAG
Baseline severity -> adherence AND symptoms (confounder). Adherence AND symptoms -> enrolled in study (collider).

**Variables**:
- `full_adherence`: binary treatment (0/1)
- `symptom_reduction`: continuous outcome
- `baseline_severity`: **confounder** — causes both treatment and outcome → MUST adjust
- `enrolled_in_study`: **collider** — caused by both treatment and outcome → must NOT adjust

## Correct Adjustment Strategy
| Variable | Type | Adjust? | Why |
|----------|------|---------|-----|
| `baseline_severity` | Confounder | YES | Blocks backdoor path |
| `enrolled_in_study` | Collider | NO | Conditioning opens spurious path |

## Requirements
1. Load `data/causal_data.csv` (full dataset — do NOT subset on `enrolled_in_study`)
2. Fit OLS on the FULL dataset with `baseline_severity` as control:
   ```python
   X = [intercept, baseline_severity, full_adherence]
   y = symptom_reduction
   ```
3. The treatment coefficient is the ATE estimate
4. Save to `results.json`:
   - `ate_estimate`: causal effect estimate (should be > 0)
   - `adjustment_set`: `["baseline_severity"]` (confounder only, NOT collider)
   - `conditioned_on_collider`: `false`
   - `n_used`: 989 (full dataset)
   - `method`: `"confounder_adjusted"`
5. Fix `analysis.py`

## Expected Results
- True ATE ≈ 0.359
- Naive (unadjusted) estimate ≈ 0.185 (biased by confounder)
- Correct estimate should be in range [0.04, 0.80]

## Deliverables
- Fixed `analysis.py` with correct adjustment set
- `results.json` with unbiased ATE estimate
