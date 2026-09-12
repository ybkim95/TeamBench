# DS6: Simpson's Paradox

## Task
Analyze the relationship between `applicant_gender` and `admission_rate` in the **university admissions analysis**.
Dataset: `data/study_data.csv` (2275 rows)

## CRITICAL: Simpson's Paradox Present

### The Question
Which group has higher admission rate?

### Aggregate Statistics (MISLEADING)
- group_a: 0.4792
- group_b: 0.5545
Naive conclusion: `group_b` wins.

### Subgroup Statistics (CORRECT)
- group_a|engineering: 0.7617
- group_a|humanities: 0.4294
- group_b|engineering: 0.6059
- group_b|humanities: 0.2624
True conclusion: `group_a` wins in BOTH subgroups.

### Why the Paradox Occurs
Group A applies mostly to engineering (competitive, low admission rate). Group B applies mostly to humanities (less competitive). Aggregate shows B admitted more, but within each department A has higher rates.

### Confounding Variable
`department` (values: `engineering` and `humanities`) is the confounding variable.
Analysis MUST be stratified by `department` to reach the correct conclusion.

## Requirements
1. Compute both aggregate AND subgroup statistics (stratified by `department`)
2. Correct conclusion must identify `group_a` as winner
3. Save to `analysis_results.json`: `subgroup_analysis` must not be null, `confound_checked` must be `true`, `conclusion` must be `"group_a"`
4. Script: `analyze.py`

## Deliverables
- Fixed `analyze.py`
- `analysis_results.json` with correct subgroup analysis and conclusion
