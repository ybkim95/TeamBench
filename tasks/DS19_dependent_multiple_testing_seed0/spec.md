# DS19: Multiple Testing with Dependence — BY Procedure

## Task
Apply the correct multiple testing correction to 298 hypothesis tests from
genome-wide association study (GWAS) with block LD structure.

## The Problem
The test statistics have **negative_correlation** dependence structure.
Benjamini-Hochberg (BH) only controls FDR under independence or positive
regression dependence (PRDS). With negative_correlation, BH may produce
excess false positives.

## The Benjamini-Yekutieli (BY) Procedure
BY controls FDR under **arbitrary dependence** by using a more conservative threshold:

```
alpha_BY = alpha / c_m
where c_m = sum(1/k, k=1..298) ≈ 6.2760
```

Then apply BH with `alpha_BY` instead of `alpha`.

## Comparison
| Method | Threshold | Rejections |
|--------|-----------|------------|
| BH (incorrect) | 2.89e-03 | 21 |
| BY (correct) | 3.16e-04 | 12 |

BH rejects **more** hypotheses but does not guarantee FDR control here.

## Requirements
1. Load `data/pvalues.csv`
2. Compute `c_m = sum(1/k for k in range(1, m+1))`
3. Apply BY procedure: BH with `alpha_BY = 0.05 / c_m`
4. Save to `results.json`:
   - `method`: `"BY"`
   - `threshold`: BY threshold (≈ 3.16e-04)
   - `n_rejected`: number of rejected hypotheses (≈ 12)
   - `harmonic_constant`: c_m (≈ 6.2760)
   - `alpha`: 0.05
   - `m_tests`: 298
5. Fix `analysis.py`

## Data
File: `data/pvalues.csv` — 298 p-values, 23 true signals

## Deliverables
- Fixed `analysis.py` using BY procedure
- `results.json` with BY threshold and rejection count
