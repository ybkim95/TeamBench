# DS19: Multiple Testing with Dependence — BY Procedure

## Task
Apply the correct multiple testing correction to 107 hypothesis tests from
factor significance testing across correlated economic variables.

## The Problem
The test statistics have **negative_correlation** dependence structure.
Benjamini-Hochberg (BH) only controls FDR under independence or positive
regression dependence (PRDS). With negative_correlation, BH may produce
excess false positives.

## The Benjamini-Yekutieli (BY) Procedure
BY controls FDR under **arbitrary dependence** by using a more conservative threshold:

```
alpha_BY = alpha / c_m
where c_m = sum(1/k, k=1..107) ≈ 5.2547
```

Then apply BH with `alpha_BY` instead of `alpha`.

## Comparison
| Method | Threshold | Rejections |
|--------|-----------|------------|
| BH (incorrect) | 2.79e-03 | 9 |
| BY (correct) | 4.37e-04 | 5 |

BH rejects **more** hypotheses but does not guarantee FDR control here.

## Requirements
1. Load `data/pvalues.csv`
2. Compute `c_m = sum(1/k for k in range(1, m+1))`
3. Apply BY procedure: BH with `alpha_BY = 0.05 / c_m`
4. Save to `results.json`:
   - `method`: `"BY"`
   - `threshold`: BY threshold (≈ 4.37e-04)
   - `n_rejected`: number of rejected hypotheses (≈ 5)
   - `harmonic_constant`: c_m (≈ 5.2547)
   - `alpha`: 0.05
   - `m_tests`: 107
5. Fix `analysis.py`

## Data
File: `data/pvalues.csv` — 107 p-values, 12 true signals

## Deliverables
- Fixed `analysis.py` using BY procedure
- `results.json` with BY threshold and rejection count
