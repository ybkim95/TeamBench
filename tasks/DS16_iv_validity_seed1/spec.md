# DS16: Instrumental Variable Validity — Exclusion Restriction

## Task
Estimate the causal effect of `cigarettes_per_day` on `fev1_score`
using 2SLS in a effect of smoking on lung function dataset (468 observations).

## The Instruments
Two candidate instruments are available:

**Valid instrument**: `cigarette_tax`
- cigarette tax affects smoking but not lung function directly
- Satisfies exclusion restriction ✓

**Invalid instrument**: `stress_score`
- stress affects both smoking and lung function directly
- VIOLATES exclusion restriction ✗ — has direct effect on outcome

## Requirements
1. **First-stage F-statistic**: Regress `cigarettes_per_day` on each instrument separately.
   A valid instrument should have F > 10 (Stock-Yogo rule of thumb).
2. **Use only the valid instrument** (`cigarette_tax`) for 2SLS estimation:
   ```python
   import statsmodels.api as sm
   # First stage
   first_stage = sm.OLS(endog, sm.add_constant(z_valid)).fit()
   x_hat = first_stage.fittedvalues
   # Second stage
   second_stage = sm.OLS(y, sm.add_constant(x_hat)).fit()
   ```
3. Save to `results.json`:
   - `iv_effect`: 2SLS estimate using valid instrument only
   - `instruments_used`: `["cigarette_tax"]` (only valid)
   - `first_stage_f`: first-stage F-statistic (should be > 10)
   - `exclusion_violation`: `true` for `stress_score`
   - `method`: `"2sls_valid_instrument_only"`
4. Fix `analysis.py`

## Data
File: `data/iv_data.csv`
Variables: `fev1_score`, `cigarettes_per_day`, `cigarette_tax`, `stress_score`

## Expected
True effect ≈ 0.135 (your 2SLS estimate should be in range [0.025, 0.5])
First-stage F > 10

## Deliverables
- Fixed `analysis.py` using only the valid instrument
- `results.json` with IV estimate and diagnostic statistics
