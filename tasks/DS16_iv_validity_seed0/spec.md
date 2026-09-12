# DS16: Instrumental Variable Validity — Exclusion Restriction

## Task
Estimate the causal effect of `education_years` on `log_wage`
using 2SLS in a returns to education (Card 1995 design) dataset (597 observations).

## The Instruments
Two candidate instruments are available:

**Valid instrument**: `distance_to_college`
- distance to college affects education but not wages directly
- Satisfies exclusion restriction ✓

**Invalid instrument**: `parents_education`
- parents education affects wages directly through networks
- VIOLATES exclusion restriction ✗ — has direct effect on outcome

## Requirements
1. **First-stage F-statistic**: Regress `education_years` on each instrument separately.
   A valid instrument should have F > 10 (Stock-Yogo rule of thumb).
2. **Use only the valid instrument** (`distance_to_college`) for 2SLS estimation:
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
   - `instruments_used`: `["distance_to_college"]` (only valid)
   - `first_stage_f`: first-stage F-statistic (should be > 10)
   - `exclusion_violation`: `true` for `parents_education`
   - `method`: `"2sls_valid_instrument_only"`
4. Fix `analysis.py`

## Data
File: `data/iv_data.csv`
Variables: `log_wage`, `education_years`, `distance_to_college`, `parents_education`

## Expected
True effect ≈ 0.164 (your 2SLS estimate should be in range [0.025, 0.5])
First-stage F > 10

## Deliverables
- Fixed `analysis.py` using only the valid instrument
- `results.json` with IV estimate and diagnostic statistics
