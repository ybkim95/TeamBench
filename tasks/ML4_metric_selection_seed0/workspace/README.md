# ML4: Metric Selection — Multi-Label Disease Prediction For Clinical Triage

The evaluation script reports 6 metrics. Analysis flags problems with all 6.
**Only 3 are genuine bugs.** The other 3 are required by compliance, business,
and SLA monitoring.

## Important

Read `REPORTING_SPEC.md` before making any changes. Removing preserved metrics
will fail the check.

## Workflow

1. Read `REPORTING_SPEC.md` (documents required preserved fields)
2. Get the Planner's guidance (they have the spec)
3. Fix only the 3 broken metrics in `evaluate.py`
4. Run `python evaluate.py` then `python check_evaluation.py`
