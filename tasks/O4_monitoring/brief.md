# O4: Fix Alerting Rules (Brief)

The monitoring system is generating too many false alerts and missing real issues.
Fix the alerting configuration for services: `recommendation-engine`, `analytics-service`, `reporting-service`.

Two files need fixing: `alert_rules.json` and `routing.json`.

The Planner has the full spec with SLA thresholds, routing rules, and grouping requirements.

After fixing, run `python3 simulator.py` — it must exit 0 with all checks passing.
