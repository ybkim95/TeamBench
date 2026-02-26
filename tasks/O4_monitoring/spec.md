# O4: Fix Alerting Rules for Monitoring System

## Background

The monitoring system is generating too many false alerts and missing real issues.
The alert_rules.json and routing.json files are misconfigured.
Your job is to fix both files so the alerting system behaves correctly.

## Monitored Services

  - `recommendation-engine`
  - `analytics-service`
  - `reporting-service`

## SLA Definitions (Source of Truth)

All services share the same SLA contract:

| Metric | Warning Threshold | Critical Threshold | Comparison |
|--------|-------------------|--------------------|------------|
| `p99_latency_ms` | `> 200` ms | `> 300` ms | greater-than |
| `error_rate_pct` | `> 1.0%` | `> 2.0%` | greater-than |
| `availability_pct` | `< 99.8%` | `< 99.4%` | less-than |

## Alert Grouping Rules

- No duplicate alerts for the same service+metric combination within a **5-minute** window.
- The `grouping_window_minutes` field in `alert_rules.json` must be exactly `5`.

## Alert Routing Rules

| Severity | Destination | Details |
|----------|-------------|---------|
| `critical` | PagerDuty | key: `pd-platform-alerts` |
| `warning`  | Slack      | channel: `#platform-warnings` |
| `info`     | Log file   | target: `monitoring.log` |

## Files to Fix

1. **`alert_rules.json`** — thresholds and grouping window are wrong. Fix all values to match SLA above.
2. **`routing.json`** — severity routing is swapped. Fix so critical→PagerDuty, warning→Slack, info→log.

## Validation

Run `python3 simulator.py` from the workspace directory. It must exit 0 with all checks passing.
Results are written to `check_results.json`.

## Hard Requirements

1. All threshold values must exactly match the SLA table above.
2. `grouping_window_minutes` must be `5`.
3. Routing types must be: critical→`pagerduty`, warning→`slack`, info→`log`.
4. No false positives: normal metrics (latency at 50% of threshold, error rate at 10% of threshold, 100% availability) must NOT trigger any alert.
5. Alerts must fire when thresholds are breached by even 1 unit.
6. Critical breach (above critical threshold) must fire `critical` severity, not just `warning`.
7. `simulator.py` must not be modified — it is the acceptance test.

## Trap Design (TNI Pattern C+D)

The brief only says "fix the alerts" — the full SLA definitions, routing rules, and grouping requirements are only in this spec.
A naive fix might:
- Adjust only one file (alert_rules.json) and leave routing.json swapped.
- Fix thresholds approximately but not exactly match spec values.
- Miss the grouping window fix.
- Fix routing type but leave wrong channel/key names.

The Planner must read this full spec. The Verifier must check all 10+ grade.sh checks.
