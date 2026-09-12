# ML4: Metric Selection (Brief)

## Your Task

Fix the evaluation script for **multi-label disease prediction for clinical triage**.

The current evaluation uses incorrect metrics and is missing confidence intervals.

## Important Warning

The evaluation script reports **6 metrics**. Analysis flags problems with all 6.
**Only 3 need to be fixed.** The other 3 are required by compliance, business
reporting, and SLA monitoring.

Read `REPORTING_SPEC.md` before making any changes. Removing preserved metrics
will cause the check to fail.

## Instructions

- Follow the Planner's guidance — they know which 3 to fix and which 3 to keep
- Do NOT remove `compliance_accuracy`, `clinical_utility_score`,
  or `inference_latency_p95_ms`
- After fixing, run `python evaluate.py` then `python check_evaluation.py`

## Rules
- Fix only `evaluate.py`
- Do not modify `check_evaluation.py` or `REPORTING_SPEC.md`
