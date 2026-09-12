# DS33: Interaction Feature Selection with Bonferroni Correction

## Task
Select significant pairwise interaction features for **credit risk scoring with interaction terms**
(368 samples, 5 base features → 10 candidate interactions).

## The Problem
The buggy script includes ALL 10 pairwise interactions.
With 368 samples and 10 extra features, most interactions are noise
that overfits the training data.

## Fix: Partial F-Test with Bonferroni Correction
For each candidate interaction `f_i × f_j`:
1. Fit **base model**: `y ~ intercept + loan_amount + income + debt_ratio + credit_age + num_accounts`
2. Fit **extended model**: `y ~ base + f_i × f_j`
3. Compute **partial F-statistic**:
   ```
   F = (SS_res_base - SS_res_ext) / 1 / (SS_res_ext / (n - p_ext - 1))
   ```
4. Get p-value from `scipy.stats.f.sf(F, 1, n - p_ext - 1)`
5. Select interaction if `p_value < 0.005000` (Bonferroni: 0.05 / 10)

## Data
File: `data/features.csv`
- Target: `default_prob`
- Features: `['loan_amount', 'income', 'debt_ratio', 'credit_age', 'num_accounts']`

## Requirements
1. Fit base model (no interactions)
2. Test each of the 10 candidate interactions
3. Apply Bonferroni correction: `alpha = 0.05 / 10`
4. Select interactions where partial F-test p-value < Bonferroni alpha
5. Save to `results.json`:
   - `n_interactions_used`: count of selected (Bonferroni-significant) interactions
   - `selected_interactions`: list of selected interaction names (e.g., `"sqft_x_school_rating"`)
   - `bonferroni_alpha`: 0.005
   - `r2`: R² of final model with selected interactions
   - `method`: `"bonferroni_selected"`
   - `n_samples`: 368
   - `n_features_base`: 5
6. Fix `analysis.py`

## Expected True Interactions
The data-generating process has real interactions at: `[('loan_amount', 'income'), ('debt_ratio', 'credit_age')]`.
Your selection should include at least one of these.

## Deliverables
- Fixed `analysis.py` with partial F-test + Bonferroni selection
- `results.json` with selected interactions
