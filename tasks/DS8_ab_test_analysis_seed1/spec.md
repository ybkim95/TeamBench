# DS8: A/B Test Multiple Comparisons

## Task
Analyze results of the **email marketing subject line test** experiment.
Dataset: `data/experiment_results.csv` (12200 rows, 6100 per group)

## CRITICAL: Multiple Comparison Problem

### The Problem
Testing 5 metrics at α=0.05 independently:
- Expected false positives = 5 × 0.05 = 0.2 per experiment
- Running 20 such experiments produces ~5 false discoveries

### Metric Classification
**Primary metric** (pre-registered, hypothesis-driven): `open_rate`
- Test at α=0.05
- This is the ONLY metric that can be declared significant without correction

**Exploratory metrics** (post-hoc, discovery): `click_rate`, `unsubscribe_rate`, `revenue_per_email`, `forward_rate`
- Must apply Bonferroni correction: α_corrected = 0.05 / 5 = 0.01
- Findings here are hypothesis-generating only

### Bonferroni Correction
`bonferroni_alpha = 0.05 / 5 = 0.01`
Apply this threshold when evaluating all exploratory metrics.

## Requirements
1. Test primary metric `open_rate` at α=0.05
2. Test ALL exploratory metrics at bonferroni_alpha=0.01
3. Save to `analysis_results.json`:
   - `bonferroni_correction_applied`: `true`
   - `bonferroni_alpha`: `0.01`
   - `n_comparisons`: `5`
   - Per-metric `p_value`, `significant` (using corrected threshold for exploratory)
4. Script: `analyze.py`

## Deliverables
- Fixed `analyze.py`
- `analysis_results.json` with correct correction applied
