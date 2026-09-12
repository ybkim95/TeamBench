# DS19: Multiple Testing with Dependence — BY Procedure

## Task
Apply the correct multiple testing correction to 334 hypothesis tests from
fMRI voxel-wise activation analysis with spatial correlation.

## The Problem
The test statistics have **arbitrary** dependence structure.
Benjamini-Hochberg (BH) only controls FDR under independence or positive
regression dependence (PRDS). With arbitrary, BH may produce
excess false positives.

## The Benjamini-Yekutieli (BY) Procedure
BY controls FDR under **arbitrary dependence** by using a more conservative threshold:

```
alpha_BY = alpha / c_m
where c_m = sum(1/k, k=1..334) ≈ 6.3899
```

Then apply BH with `alpha_BY` instead of `alpha`.

## Comparison
| Method | Threshold | Rejections |
|--------|-----------|------------|
| BH (incorrect) | 1.46e-03 | 10 |
| BY (correct) | 8.05e-05 | 6 |

BH rejects **more** hypotheses but does not guarantee FDR control here.

## Requirements
1. Load `data/pvalues.csv`
2. Compute `c_m = sum(1/k for k in range(1, m+1))`
3. Apply BY procedure: BH with `alpha_BY = 0.05 / c_m`
4. Save to `results.json`:
   - `method`: `"BY"`
   - `threshold`: BY threshold (≈ 8.05e-05)
   - `n_rejected`: number of rejected hypotheses (≈ 6)
   - `harmonic_constant`: c_m (≈ 6.3899)
   - `alpha`: 0.05
   - `m_tests`: 334
5. Fix `analysis.py`

## Data
File: `data/pvalues.csv` — 334 p-values, 16 true signals

## Deliverables
- Fixed `analysis.py` using BY procedure
- `results.json` with BY threshold and rejection count
