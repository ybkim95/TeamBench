# DS20: Regression Discontinuity — IK Bandwidth + McCrary Test

## Task
Estimate the **regression discontinuity (RD) effect** at the cutoff of 51.7
for regression discontinuity at welfare eligibility threshold (737 observations).

## Why Bandwidth Matters
- Too wide: includes units far from cutoff where the linearity assumption fails
- Too narrow: too few observations, high variance
- **IK-optimal bandwidth** balances bias and variance optimally

## IK Bandwidth Formula
```
h_IK = 2.702 × std(income_percentile) × n^(-1/5)
     ≈ 5.6165  (for this dataset)
```

## McCrary Density Test
Note: there may be manipulation (heaping) at the cutoff — the McCrary test may flag this.
Check if the density of `income_percentile` is continuous at 51.7:
- Compare histogram bin counts just below vs just above cutoff
- A large discontinuity in density suggests manipulation (sorting/heaping)
- Use bins of width ≈ h_IK/2 on each side

## Requirements
1. Compute IK bandwidth: `h = 2.702 * np.std(income_percentile) * (n ** (-0.2))`
2. Run McCrary test: count observations in bins [cutoff-h, cutoff) and [cutoff, cutoff+h)
   and report the ratio (should be ≈ 1.0 if no manipulation)
3. Fit **local linear regression** within [cutoff ± h]:
   - `y ~ intercept + (x - cutoff) + treatment + (x - cutoff) * treatment`
   - RD estimate = coefficient on `treatment`
4. Save to `results.json`:
   - `rd_effect`: local linear RD estimate
   - `bandwidth`: IK bandwidth (should be ≈ 5.6165 ± 1.68)
   - `bandwidth_method`: `"IK_optimal"`
   - `n_in_window`: number of observations within bandwidth
   - `cutoff`: 51.7
   - `mccrary_ratio`: density ratio above/below cutoff
   - `method`: `"local_linear"`
5. Fix `analysis.py`

## Data
File: `data/rd_data.csv`
- `income_percentile`: running variable (determines treatment)
- `employment_rate`: outcome of interest
- `received_benefits`: 1 if above cutoff, 0 otherwise

## Expected
True RD effect ≈ 0.1263
Your estimate should be in range [0.0379, 0.3789]

## Deliverables
- Fixed `analysis.py` with IK bandwidth and local linear regression
- `results.json` with RD estimate, bandwidth, and McCrary test result
