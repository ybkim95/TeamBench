# DS6: Simpson's Paradox

## Task
Analyze the relationship between `treatment` and `recovery_rate` in the **drug treatment efficacy study**.
Dataset: `data/study_data.csv` (2788 rows)

## CRITICAL: Simpson's Paradox Present

### The Question
Which treatment has better recovery rate?

### Aggregate Statistics (MISLEADING)
- drug_a: 0.4497
- drug_b: 0.5776
Naive conclusion: `drug_b` wins.

### Subgroup Statistics (CORRECT)
- drug_a|mild: 0.7782
- drug_a|severe: 0.3917
- drug_b|mild: 0.6263
- drug_b|severe: 0.3016
True conclusion: `drug_a` wins in BOTH subgroups.

### Why the Paradox Occurs
Drug A is used more on severe cases (lower baseline recovery), Drug B on mild cases (higher baseline). Aggregate favors B but within each severity group, A is better.

### Confounding Variable
`severity` (values: `mild` and `severe`) is the confounding variable.
Analysis MUST be stratified by `severity` to reach the correct conclusion.

## Requirements
1. Compute both aggregate AND subgroup statistics (stratified by `severity`)
2. Correct conclusion must identify `drug_a` as winner
3. Save to `analysis_results.json`: `subgroup_analysis` must not be null, `confound_checked` must be `true`, `conclusion` must be `"drug_a"`
4. Script: `analyze.py`

## Deliverables
- Fixed `analyze.py`
- `analysis_results.json` with correct subgroup analysis and conclusion
