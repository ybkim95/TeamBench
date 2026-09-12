# DS6: Simpson's Paradox

## Task
Analyze the relationship between `platform` and `conversion_rate` in the **e-commerce platform conversion rate study**.
Dataset: `data/study_data.csv` (2115 rows)

## CRITICAL: Simpson's Paradox Present

### The Question
Which platform has higher conversion rate?

### Aggregate Statistics (MISLEADING)
- mobile: 0.4347
- desktop: 0.5736
Naive conclusion: `desktop` wins.

### Subgroup Statistics (CORRECT)
- mobile|new_user: 0.7121
- mobile|returning_user: 0.3858
- desktop|new_user: 0.6161
- desktop|returning_user: 0.3327
True conclusion: `mobile` wins in BOTH subgroups.

### Why the Paradox Occurs
Mobile attracts more new users (lower base conversion). Desktop used more by returning users (high base conversion). Mobile actually converts better within both segments but appears worse in aggregate.

### Confounding Variable
`customer_segment` (values: `new_user` and `returning_user`) is the confounding variable.
Analysis MUST be stratified by `customer_segment` to reach the correct conclusion.

## Requirements
1. Compute both aggregate AND subgroup statistics (stratified by `customer_segment`)
2. Correct conclusion must identify `mobile` as winner
3. Save to `analysis_results.json`: `subgroup_analysis` must not be null, `confound_checked` must be `true`, `conclusion` must be `"mobile"`
4. Script: `analyze.py`

## Deliverables
- Fixed `analyze.py`
- `analysis_results.json` with correct subgroup analysis and conclusion
