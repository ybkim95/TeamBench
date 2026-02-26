"""
Parameterized generator for O4: Fix Alerting Rules for Monitoring System.

TNI Pattern C,D — spec has complete SLA definitions but brief only says "fix the alerts."

Each seed produces:
  - Different set of services (2-4 services) with seed-specific names
  - Different SLA thresholds (p99 latency ms, error rate %, availability %)
  - Different alert routing (critical→PagerDuty, warning→Slack, info→log)
  - Different alert grouping window (3-10 min)
  - Misconfigured alert_rules.json (thresholds wrong, routing wrong)
  - Misconfigured routing.json (channels swapped/broken)
  - simulator.py that generates metrics and validates alert firing

The task: fix alert_rules.json and routing.json so that:
  1. Thresholds exactly match the SLA values in spec
  2. Routing maps severity→correct channel
  3. No false positives on normal traffic
  4. Alerts fire on SLA breach
  5. Grouping window deduplicates within the window
"""
from __future__ import annotations

import json

from generators.base import TaskGenerator, GeneratedTask
from generators.primitives import SeededRandom

# Service name pools
SERVICE_NAMES = [
    ["api-gateway", "auth-service", "payment-service", "notification-service"],
    ["user-service", "order-service", "inventory-service", "search-service"],
    ["web-frontend", "data-pipeline", "cache-service", "billing-service"],
    ["recommendation-engine", "analytics-service", "reporting-service", "export-service"],
    ["checkout-service", "product-catalog", "review-service", "shipping-service"],
]

# SLA threshold pools — (p99_latency_ms, error_rate_pct, availability_pct)
SLA_PROFILES = [
    (200, 1.0, 99.9),
    (150, 0.5, 99.95),
    (300, 2.0, 99.5),
    (100, 0.1, 99.99),
    (250, 1.5, 99.8),
    (180, 0.8, 99.9),
    (400, 3.0, 99.0),
    (120, 0.3, 99.95),
]

# Alert grouping window options (minutes)
GROUPING_WINDOWS = [3, 4, 5, 6, 8, 10]

# Routing channel names
PAGERDUTY_KEYS = ["pd-prod-critical", "pd-oncall-primary", "pd-sre-team", "pd-platform-alerts"]
SLACK_CHANNELS = ["#alerts-warning", "#ops-warnings", "#sre-warnings", "#platform-warnings"]
LOG_TARGETS = ["alertmanager.log", "ops-alerts.log", "monitoring.log", "sre-alerts.log"]


def _make_buggy_threshold(rng: SeededRandom, correct_value: float, kind: str) -> float:
    """Return an intentionally wrong threshold value."""
    # Choose bug type: too loose (misses real alerts) or too tight (false positives)
    bug_choice = rng.randint(0, 2)
    if kind == "latency":
        if bug_choice == 0:
            return round(correct_value * 2.0)          # too loose — misses real breaches
        elif bug_choice == 1:
            return round(correct_value * 0.3)          # too tight — constant false positives
        else:
            return round(correct_value + 500)          # wildly off
    elif kind == "error_rate":
        if bug_choice == 0:
            return round(correct_value * 5.0, 1)       # too loose
        elif bug_choice == 1:
            return round(max(0.01, correct_value * 0.1), 2)  # too tight
        else:
            return round(correct_value + 10.0, 1)      # wildly off
    else:  # availability
        if bug_choice == 0:
            return round(correct_value - 5.0, 2)       # too loose
        elif bug_choice == 1:
            return round(min(100.0, correct_value + 0.09), 2)  # too tight
        else:
            return round(correct_value - 10.0, 2)      # wildly off


class Generator(TaskGenerator):
    task_id = "O4_monitoring"
    domain = "operations"
    difficulty = "hard"
    languages = ["python", "json"]

    def generate(self, seed: int) -> GeneratedTask:
        rng = SeededRandom(seed)

        # Pick services (2-4)
        service_pool = rng.choice(SERVICE_NAMES)
        n_services = rng.randint(2, 4)
        services = service_pool[:n_services]

        # Pick SLA profile (same for all services in this instance — simplifies grading)
        p99_latency_ms, error_rate_pct, availability_pct = rng.choice(SLA_PROFILES)

        # Grouping window
        grouping_window_min = rng.choice(GROUPING_WINDOWS)

        # Routing channels
        pd_key = rng.choice(PAGERDUTY_KEYS)
        slack_channel = rng.choice(SLACK_CHANNELS)
        log_target = rng.choice(LOG_TARGETS)

        # Correct routing config
        correct_routing = {
            "routes": {
                "critical": {"type": "pagerduty", "key": pd_key},
                "warning":  {"type": "slack",     "channel": slack_channel},
                "info":     {"type": "log",        "target": log_target},
            }
        }

        # Correct alert rules
        correct_rules = {
            "grouping_window_minutes": grouping_window_min,
            "services": {}
        }
        for svc in services:
            correct_rules["services"][svc] = {
                "p99_latency_ms": {
                    "warning":  p99_latency_ms,
                    "critical": round(p99_latency_ms * 1.5),
                    "comparison": "gt"
                },
                "error_rate_pct": {
                    "warning":  error_rate_pct,
                    "critical": round(error_rate_pct * 2.0, 2),
                    "comparison": "gt"
                },
                "availability_pct": {
                    "warning":  round(availability_pct - 0.1, 2),
                    "critical": round(availability_pct - 0.5, 2),
                    "comparison": "lt"
                },
            }

        # --- Build BUGGY alert_rules.json ---
        # Bug 1: wrong thresholds for each service metric
        # Bug 2: wrong grouping window (too large or too small)
        buggy_window = rng.choice([w for w in GROUPING_WINDOWS if w != grouping_window_min])
        buggy_rules: dict = {
            "grouping_window_minutes": buggy_window,
            "services": {}
        }
        for svc in services:
            buggy_lat_warn = _make_buggy_threshold(rng, p99_latency_ms, "latency")
            buggy_lat_crit = round(buggy_lat_warn * 1.5)
            buggy_err_warn = _make_buggy_threshold(rng, error_rate_pct, "error_rate")
            buggy_err_crit = round(buggy_err_warn * 2.0, 2)
            buggy_avail_warn = _make_buggy_threshold(rng, availability_pct, "availability")
            buggy_avail_crit = round(buggy_avail_warn - 0.5, 2)
            buggy_rules["services"][svc] = {
                "p99_latency_ms": {
                    "warning":  buggy_lat_warn,
                    "critical": buggy_lat_crit,
                    "comparison": "gt"
                },
                "error_rate_pct": {
                    "warning":  buggy_err_warn,
                    "critical": buggy_err_crit,
                    "comparison": "gt"
                },
                "availability_pct": {
                    "warning":  buggy_avail_warn,
                    "critical": buggy_avail_crit,
                    "comparison": "lt"
                },
            }

        # --- Build BUGGY routing.json ---
        # Bug: severity channels are swapped (critical→Slack, warning→PagerDuty, info→wrong)
        buggy_routing = {
            "routes": {
                "critical": {"type": "slack",     "channel": slack_channel},   # WRONG: should be PD
                "warning":  {"type": "pagerduty", "key": pd_key},             # WRONG: should be Slack
                "info":     {"type": "pagerduty", "key": pd_key},             # WRONG: should be log
            }
        }

        alert_rules_json = json.dumps(buggy_rules, indent=2)
        routing_json = json.dumps(buggy_routing, indent=2)
        simulator_py = self._generate_simulator(
            services, p99_latency_ms, error_rate_pct, availability_pct, grouping_window_min
        )

        workspace_files = {
            "alert_rules.json": alert_rules_json,
            "routing.json": routing_json,
            "simulator.py": simulator_py,
        }

        expected = {
            "services": services,
            "p99_latency_ms_warning": p99_latency_ms,
            "p99_latency_ms_critical": round(p99_latency_ms * 1.5),
            "error_rate_pct_warning": error_rate_pct,
            "error_rate_pct_critical": round(error_rate_pct * 2.0, 2),
            "availability_pct_warning": round(availability_pct - 0.1, 2),
            "availability_pct_critical": round(availability_pct - 0.5, 2),
            "grouping_window_minutes": grouping_window_min,
            "routing_critical_type": "pagerduty",
            "routing_critical_key": pd_key,
            "routing_warning_type": "slack",
            "routing_warning_channel": slack_channel,
            "routing_info_type": "log",
            "routing_info_target": log_target,
        }

        spec_md = self._generate_spec(
            services, p99_latency_ms, error_rate_pct, availability_pct,
            grouping_window_min, pd_key, slack_channel, log_target
        )
        brief_md = self._generate_brief(services)

        return GeneratedTask(
            task_id=self.task_id,
            seed=seed,
            spec_md=spec_md,
            brief_md=brief_md,
            expected=expected,
            workspace_files=workspace_files,
        )

    def _generate_simulator(
        self,
        services: list[str],
        p99_latency_ms: float,
        error_rate_pct: float,
        availability_pct: float,
        grouping_window_min: int,
    ) -> str:
        services_json = json.dumps(services)
        return f'''#!/usr/bin/env python3
"""
Alert rule simulator for O4_monitoring.

Loads alert_rules.json and routing.json from the current directory,
then runs a series of checks:

  1. No false positives: normal metrics should NOT trigger alerts.
  2. Latency breach fires warning then critical alert.
  3. Error rate breach fires warning then critical alert.
  4. Availability breach fires warning then critical alert.
  5. Grouping window deduplicates repeated alerts within the window.
  6. Routing: critical alerts go to PagerDuty, warning→Slack, info→log.

Exits 0 if all checks pass, 1 otherwise.
Writes results to check_results.json.
"""
import json
import sys
import os
from datetime import datetime, timedelta

SERVICES = {services_json}
SLA_P99_LATENCY_MS = {p99_latency_ms}
SLA_ERROR_RATE_PCT = {error_rate_pct}
SLA_AVAILABILITY_PCT = {availability_pct}
GROUPING_WINDOW_MIN = {grouping_window_min}


def load_json(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: {{path}} not found", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: {{path}} is not valid JSON: {{e}}", file=sys.stderr)
        sys.exit(1)


def check_threshold(rules, service, metric, value, expected_comparison):
    """
    Given a metric value, determine which severity the rules would fire.
    Returns the highest severity fired ("critical", "warning", "none").
    """
    svc_rules = rules.get("services", {{}}).get(service, {{}})
    metric_rule = svc_rules.get(metric, {{}})
    comparison = metric_rule.get("comparison", "gt")

    def fires(threshold):
        if comparison == "gt":
            return value > threshold
        elif comparison == "lt":
            return value < threshold
        return False

    critical_thresh = metric_rule.get("critical")
    warning_thresh = metric_rule.get("warning")

    if critical_thresh is not None and fires(critical_thresh):
        return "critical"
    if warning_thresh is not None and fires(warning_thresh):
        return "warning"
    return "none"


def simulate_grouping(rules, service, metric, value, n_events=3):
    """
    Fires n_events alerts for the same metric within the grouping window.
    Returns how many unique alerts would be sent (should be 1 if grouping works).
    """
    window_min = rules.get("grouping_window_minutes", 5)
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    alert_times = []
    sent_count = 0
    last_sent = None

    for i in range(n_events):
        t = base_time + timedelta(minutes=i * (window_min // max(1, n_events - 1)))
        severity = check_threshold(rules, service, metric, value, "gt")
        if severity == "none":
            continue
        # Group: only send if outside window or first alert
        if last_sent is None or (t - last_sent).total_seconds() > window_min * 60:
            sent_count += 1
            last_sent = t
        alert_times.append(t.isoformat())

    return sent_count


def run_checks():
    rules = load_json("alert_rules.json")
    routing = load_json("routing.json")

    results = []
    passed = 0
    failed = 0

    def record(name, ok, detail=""):
        nonlocal passed, failed
        results.append({{"check": name, "pass": ok, "detail": detail}})
        if ok:
            passed += 1
            print(f"  PASS  {{name}}")
        else:
            failed += 1
            print(f"  FAIL  {{name}}: {{detail}}")

    print("=== O4 Monitoring Alert Simulator ===")
    print()

    # ── CHECK 1: Schema validation ──────────────────────────────────────────
    has_grouping = "grouping_window_minutes" in rules
    record("schema_has_grouping_window", has_grouping,
           "" if has_grouping else "alert_rules.json missing grouping_window_minutes")

    has_services = "services" in rules and isinstance(rules["services"], dict)
    record("schema_has_services", has_services,
           "" if has_services else "alert_rules.json missing services dict")

    has_routes = "routes" in routing and isinstance(routing["routes"], dict)
    record("schema_has_routes", has_routes,
           "" if has_routes else "routing.json missing routes dict")

    # ── CHECK 2: Grouping window correct ───────────────────────────────────
    actual_window = rules.get("grouping_window_minutes", -1)
    window_ok = actual_window == GROUPING_WINDOW_MIN
    record("grouping_window_correct",
           window_ok,
           f"expected={{GROUPING_WINDOW_MIN}}, got={{actual_window}}")

    # ── CHECK 3: Threshold correctness per service ─────────────────────────
    for svc in SERVICES:
        svc_rules = rules.get("services", {{}}).get(svc, {{}})

        # p99 latency thresholds
        lat_warn = svc_rules.get("p99_latency_ms", {{}}).get("warning")
        lat_crit = svc_rules.get("p99_latency_ms", {{}}).get("critical")
        record(f"threshold_{{svc}}_latency_warning",
               lat_warn == SLA_P99_LATENCY_MS,
               f"expected={{SLA_P99_LATENCY_MS}}, got={{lat_warn}}")
        expected_lat_crit = round(SLA_P99_LATENCY_MS * 1.5)
        record(f"threshold_{{svc}}_latency_critical",
               lat_crit == expected_lat_crit,
               f"expected={{expected_lat_crit}}, got={{lat_crit}}")

        # error rate thresholds
        err_warn = svc_rules.get("error_rate_pct", {{}}).get("warning")
        err_crit = svc_rules.get("error_rate_pct", {{}}).get("critical")
        record(f"threshold_{{svc}}_error_rate_warning",
               err_warn == SLA_ERROR_RATE_PCT,
               f"expected={{SLA_ERROR_RATE_PCT}}, got={{err_warn}}")
        expected_err_crit = round(SLA_ERROR_RATE_PCT * 2.0, 2)
        record(f"threshold_{{svc}}_error_rate_critical",
               err_crit == expected_err_crit,
               f"expected={{expected_err_crit}}, got={{err_crit}}")

        # availability thresholds
        avail_warn = svc_rules.get("availability_pct", {{}}).get("warning")
        avail_crit = svc_rules.get("availability_pct", {{}}).get("critical")
        expected_avail_warn = round(SLA_AVAILABILITY_PCT - 0.1, 2)
        expected_avail_crit = round(SLA_AVAILABILITY_PCT - 0.5, 2)
        record(f"threshold_{{svc}}_availability_warning",
               avail_warn == expected_avail_warn,
               f"expected={{expected_avail_warn}}, got={{avail_warn}}")
        record(f"threshold_{{svc}}_availability_critical",
               avail_crit == expected_avail_crit,
               f"expected={{expected_avail_crit}}, got={{avail_crit}}")

    # ── CHECK 4: No false positives on normal data ─────────────────────────
    # Normal: latency well below threshold, error rate near 0, availability 100%
    test_svc = SERVICES[0]
    normal_latency = SLA_P99_LATENCY_MS * 0.5   # 50% of threshold → should not alert
    normal_error   = SLA_ERROR_RATE_PCT * 0.1    # 10% of threshold → should not alert
    normal_avail   = 100.0                        # perfect → should not alert

    lat_sev   = check_threshold(rules, test_svc, "p99_latency_ms", normal_latency, "gt")
    err_sev   = check_threshold(rules, test_svc, "error_rate_pct", normal_error, "gt")
    avail_sev = check_threshold(rules, test_svc, "availability_pct", normal_avail, "lt")

    record("no_false_positive_latency",
           lat_sev == "none",
           f"normal latency {{normal_latency}}ms triggered {{lat_sev}}")
    record("no_false_positive_error_rate",
           err_sev == "none",
           f"normal error rate {{normal_error}}% triggered {{err_sev}}")
    record("no_false_positive_availability",
           avail_sev == "none",
           f"perfect availability triggered {{avail_sev}}")

    # ── CHECK 5: Alerts fire on SLA breach ────────────────────────────────
    # Breach: just over warning threshold
    breach_latency  = SLA_P99_LATENCY_MS + 1
    breach_error    = SLA_ERROR_RATE_PCT + 0.01
    breach_avail    = round(SLA_AVAILABILITY_PCT - 0.15, 3)  # between warning and critical

    lat_sev_breach   = check_threshold(rules, test_svc, "p99_latency_ms", breach_latency, "gt")
    err_sev_breach   = check_threshold(rules, test_svc, "error_rate_pct", breach_error, "gt")
    avail_sev_breach = check_threshold(rules, test_svc, "availability_pct", breach_avail, "lt")

    record("alert_fires_on_latency_breach",
           lat_sev_breach in ("warning", "critical"),
           f"latency {{breach_latency}}ms did not trigger alert (got: {{lat_sev_breach}})")
    record("alert_fires_on_error_rate_breach",
           err_sev_breach in ("warning", "critical"),
           f"error rate {{breach_error}}% did not trigger alert (got: {{err_sev_breach}})")
    record("alert_fires_on_availability_breach",
           avail_sev_breach in ("warning", "critical"),
           f"availability {{breach_avail}}% did not trigger alert (got: {{avail_sev_breach}})")

    # Critical breach fires critical severity
    crit_latency = round(SLA_P99_LATENCY_MS * 1.5) + 1
    crit_error   = round(SLA_ERROR_RATE_PCT * 2.0, 2) + 0.01
    crit_avail   = round(SLA_AVAILABILITY_PCT - 0.5, 2) - 0.1

    lat_sev_crit   = check_threshold(rules, test_svc, "p99_latency_ms", crit_latency, "gt")
    err_sev_crit   = check_threshold(rules, test_svc, "error_rate_pct", crit_error, "gt")
    avail_sev_crit = check_threshold(rules, test_svc, "availability_pct", crit_avail, "lt")

    record("critical_fires_on_latency_crit_breach",
           lat_sev_crit == "critical",
           f"latency {{crit_latency}}ms got {{lat_sev_crit}} instead of critical")
    record("critical_fires_on_error_rate_crit_breach",
           err_sev_crit == "critical",
           f"error rate {{crit_error}}% got {{err_sev_crit}} instead of critical")
    record("critical_fires_on_availability_crit_breach",
           avail_sev_crit == "critical",
           f"availability {{crit_avail}}% got {{avail_sev_crit}} instead of critical")

    # ── CHECK 6: Grouping deduplicates within window ───────────────────────
    # Fire 3 events within the grouping window — only 1 alert should be sent
    crit_lat_value = crit_latency
    sent = simulate_grouping(rules, test_svc, "p99_latency_ms", crit_lat_value, n_events=3)
    record("grouping_deduplicates_within_window",
           sent == 1,
           f"expected 1 alert sent within window, got {{sent}}")

    # ── CHECK 7: Routing correctness ──────────────────────────────────────
    routes = routing.get("routes", {{}})

    crit_route = routes.get("critical", {{}})
    record("routing_critical_to_pagerduty",
           crit_route.get("type") == "pagerduty",
           f"critical routes to {{crit_route.get('type')}} instead of pagerduty")

    warn_route = routes.get("warning", {{}})
    record("routing_warning_to_slack",
           warn_route.get("type") == "slack",
           f"warning routes to {{warn_route.get('type')}} instead of slack")

    info_route = routes.get("info", {{}})
    record("routing_info_to_log",
           info_route.get("type") == "log",
           f"info routes to {{info_route.get('type')}} instead of log")

    # ── Summary ───────────────────────────────────────────────────────────
    print()
    print(f"Results: {{passed}} passed, {{failed}} failed out of {{passed + failed}} checks")

    output = {{
        "passed": passed,
        "failed": failed,
        "total": passed + failed,
        "checks": results,
        "simulator_ok": failed == 0,
    }}
    with open("check_results.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"Written check_results.json")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_checks())
'''

    def _generate_spec(
        self,
        services: list[str],
        p99_latency_ms: float,
        error_rate_pct: float,
        availability_pct: float,
        grouping_window_min: int,
        pd_key: str,
        slack_channel: str,
        log_target: str,
    ) -> str:
        services_bullet = "\n".join(f"  - `{s}`" for s in services)
        lat_crit = round(p99_latency_ms * 1.5)
        err_crit = round(error_rate_pct * 2.0, 2)
        avail_warn = round(availability_pct - 0.1, 2)
        avail_crit = round(availability_pct - 0.5, 2)

        return f"""# O4: Fix Alerting Rules for Monitoring System

## Background

The monitoring system is generating too many false alerts and missing real issues.
The alert_rules.json and routing.json files are misconfigured.
Your job is to fix both files so the alerting system behaves correctly.

## Monitored Services

{services_bullet}

## SLA Definitions (Source of Truth)

All services share the same SLA contract:

| Metric | Warning Threshold | Critical Threshold | Comparison |
|--------|-------------------|--------------------|------------|
| `p99_latency_ms` | `> {p99_latency_ms}` ms | `> {lat_crit}` ms | greater-than |
| `error_rate_pct` | `> {error_rate_pct}%` | `> {err_crit}%` | greater-than |
| `availability_pct` | `< {avail_warn}%` | `< {avail_crit}%` | less-than |

## Alert Grouping Rules

- No duplicate alerts for the same service+metric combination within a **{grouping_window_min}-minute** window.
- The `grouping_window_minutes` field in `alert_rules.json` must be exactly `{grouping_window_min}`.

## Alert Routing Rules

| Severity | Destination | Details |
|----------|-------------|---------|
| `critical` | PagerDuty | key: `{pd_key}` |
| `warning`  | Slack      | channel: `{slack_channel}` |
| `info`     | Log file   | target: `{log_target}` |

## Files to Fix

1. **`alert_rules.json`** — thresholds and grouping window are wrong. Fix all values to match SLA above.
2. **`routing.json`** — severity routing is swapped. Fix so critical→PagerDuty, warning→Slack, info→log.

## Validation

Run `python3 simulator.py` from the workspace directory. It must exit 0 with all checks passing.
Results are written to `check_results.json`.

## Hard Requirements

1. All threshold values must exactly match the SLA table above.
2. `grouping_window_minutes` must be `{grouping_window_min}`.
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
"""

    def _generate_brief(self, services: list[str]) -> str:
        svc_list = ", ".join(f"`{s}`" for s in services)
        return f"""# O4: Fix Alerting Rules (Brief)

The monitoring system is generating too many false alerts and missing real issues.
Fix the alerting configuration for services: {svc_list}.

Two files need fixing: `alert_rules.json` and `routing.json`.

The Planner has the full spec with SLA thresholds, routing rules, and grouping requirements.

After fixing, run `python3 simulator.py` — it must exit 0 with all checks passing.
"""
