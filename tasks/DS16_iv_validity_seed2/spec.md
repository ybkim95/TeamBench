# DS16: Instrumental Variable Validity — Exclusion Restriction

## Task
Estimate the causal effect of `ad_spend` on `log_sales`
using 2SLS in a effect of advertising on sales dataset (428 observations).

## The Instruments
Two candidate instruments are available:

**Valid instrument**: `competitor_ad_spend`
- competitor ad spend shifts own ad spend via competitive response
- Satisfies exclusion restriction ✓

**Invalid instrument**: `ceo_tenure`
- CEO tenure affects both ad strategy and sales culture directly
- VIOLATES exclusion restriction ✗ — has direct effect on outcome

## Requirements
1. **First-stage F-statistic**: Regress `ad_spend` on each instrument separately.
   A valid instrument should have F > 10 (Stock-Yogo rule of thumb).
2. **Use only the valid instrument** (`competitor_ad_spend`) for 2SLS estimation:
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
   - `instruments_used`: `["competitor_ad_spend"]` (only valid)
   - `first_stage_f`: first-stage F-statistic (should be > 10)
   - `exclusion_violation`: `true` for `ceo_tenure`
   - `method`: `"2sls_valid_instrument_only"`
4. Fix `analysis.py`

## Data
File: `data/iv_data.csv`
Variables: `log_sales`, `ad_spend`, `competitor_ad_spend`, `ceo_tenure`

## Expected
True effect ≈ 0.064 (your 2SLS estimate should be in range [0.025, 0.5])
First-stage F > 10

## Deliverables
- Fixed `analysis.py` using only the valid instrument
- `results.json` with IV estimate and diagnostic statistics
