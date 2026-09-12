# DS34: Polynomial Feature Degree Selection

## Task
Apply **selective** polynomial expansion for **solar panel power output with temperature-efficiency curve** (494 samples).
Only expand features that actually exhibit nonlinear relationships.

## The Problem
The buggy script applies `PolynomialFeatures(degree=3)` to all 4 features,
generating ~34 polynomial features. Most are noise from linear features.

## Correct Approach: Test Each Feature First
For each feature `f`:
1. Fit **linear model**: `y ~ intercept + f`  → get `SS_res_linear`
2. Fit **quadratic model**: `y ~ intercept + f + f²`  → get `SS_res_quad`
3. Partial F-test:
   ```python
   F = (SS_res_linear - SS_res_quad) / 1 / (SS_res_quad / (n - 3))
   from scipy.stats import f as fdist
   p_value = fdist.sf(F, 1, n - 3)
   ```
4. If `p_value < 0.05`: feature is **nonlinear** → add `f²` term
5. If `p_value >= 0.05`: feature is **linear** → keep as-is

## Data
File: `data/features.csv`
- Target: `power_kwh`
- Features: `['panel_area', 'tilt_angle', 'irradiance', 'temperature']`

## Requirements
1. Test each feature for nonlinearity with partial F-test
2. For nonlinear features: add degree-2 polynomial (`f²` only, no cross-terms)
3. For linear features: keep as original
4. Fit final model with selective features
5. Save to `results.json`:
   - `degree_used`: `"selective"`
   - `expansion_method`: `"selective"`
   - `n_poly_features`: total features in final model
   - `nonlinear_features_detected`: list of features flagged as nonlinear (p < 0.05)
   - `linear_features_kept`: list of features kept as linear
   - `r2`: R² of final model
   - `n_samples`: 494
   - `nonlinearity_test_applied`: `true`
6. Fix `analysis.py`

## Expected
Features `['irradiance', 'temperature']` should be flagged as nonlinear.
Features `['panel_area', 'tilt_angle']` should be kept linear.

## Deliverables
- Fixed `analysis.py` with selective polynomial expansion
- `results.json` with nonlinearity test results
