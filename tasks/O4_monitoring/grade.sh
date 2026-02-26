#!/usr/bin/env bash
set -o pipefail
WORKSPACE="$1"
REPORTS="$2"
SUBMISSION="$3"
TASK_DIR="$4"

mkdir -p "$REPORTS"

CHECKS=0; PASSED=0; FAILURES=""
check() {
  CHECKS=$((CHECKS + 1))
  if eval "$1" 2>/dev/null; then
    PASSED=$((PASSED + 1))
  else
    FAILURES="${FAILURES:+${FAILURES},}$2"
  fi
}

# Load seed-specific expected values
EXPECTED_JSON="$REPORTS/expected.json"
if [ ! -f "$EXPECTED_JSON" ]; then
  echo "ERROR: expected.json not found at $EXPECTED_JSON" >&2
  exit 1
fi

# Extract expected values via python3
read_expected() {
  python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('$1', ''))"
}
read_expected_float() {
  python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(float(d.get('$1', 0)))"
}

P99_LATENCY_WARN=$(read_expected_float "p99_latency_ms_warning")
P99_LATENCY_CRIT=$(read_expected_float "p99_latency_ms_critical")
ERROR_RATE_WARN=$(read_expected_float "error_rate_pct_warning")
ERROR_RATE_CRIT=$(read_expected_float "error_rate_pct_critical")
AVAIL_WARN=$(read_expected_float "availability_pct_warning")
AVAIL_CRIT=$(read_expected_float "availability_pct_critical")
GROUPING_WINDOW=$(read_expected "grouping_window_minutes")
ROUTING_CRIT_TYPE=$(read_expected "routing_critical_type")
ROUTING_CRIT_KEY=$(read_expected "routing_critical_key")
ROUTING_WARN_TYPE=$(read_expected "routing_warning_type")
ROUTING_WARN_CHAN=$(read_expected "routing_warning_channel")
ROUTING_INFO_TYPE=$(read_expected "routing_info_type")
ROUTING_INFO_TARGET=$(read_expected "routing_info_target")
SERVICES=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d['services'][0])")

cd "$WORKSPACE"

# ── CHECK 1: alert_rules.json is valid JSON ──────────────────────────────
check "python3 -c \"import json; json.load(open('alert_rules.json')); print('OK')\"" \
  "alert_rules_invalid_json"

# ── CHECK 2: routing.json is valid JSON ──────────────────────────────────
check "python3 -c \"import json; json.load(open('routing.json')); print('OK')\"" \
  "routing_invalid_json"

# ── CHECK 3: grouping_window_minutes correct ──────────────────────────────
check "python3 -c \"
import json
rules = json.load(open('alert_rules.json'))
w = rules.get('grouping_window_minutes')
assert w == ${GROUPING_WINDOW}, f'grouping_window_minutes: expected ${GROUPING_WINDOW}, got {w}'
print('OK')
\"" "grouping_window_wrong"

# ── CHECK 4: p99 latency warning threshold correct for first service ──────
check "python3 -c \"
import json
rules = json.load(open('alert_rules.json'))
svc = '${SERVICES}'
v = rules['services'][svc]['p99_latency_ms']['warning']
assert v == ${P99_LATENCY_WARN}, f'latency warning: expected ${P99_LATENCY_WARN}, got {v}'
print('OK')
\"" "latency_warning_threshold_wrong"

# ── CHECK 5: p99 latency critical threshold correct ───────────────────────
check "python3 -c \"
import json
rules = json.load(open('alert_rules.json'))
svc = '${SERVICES}'
v = rules['services'][svc]['p99_latency_ms']['critical']
assert v == ${P99_LATENCY_CRIT}, f'latency critical: expected ${P99_LATENCY_CRIT}, got {v}'
print('OK')
\"" "latency_critical_threshold_wrong"

# ── CHECK 6: error_rate warning threshold correct ─────────────────────────
check "python3 -c \"
import json
rules = json.load(open('alert_rules.json'))
svc = '${SERVICES}'
v = rules['services'][svc]['error_rate_pct']['warning']
assert abs(float(v) - ${ERROR_RATE_WARN}) < 0.001, f'error_rate warning: expected ${ERROR_RATE_WARN}, got {v}'
print('OK')
\"" "error_rate_warning_threshold_wrong"

# ── CHECK 7: error_rate critical threshold correct ────────────────────────
check "python3 -c \"
import json
rules = json.load(open('alert_rules.json'))
svc = '${SERVICES}'
v = rules['services'][svc]['error_rate_pct']['critical']
assert abs(float(v) - ${ERROR_RATE_CRIT}) < 0.001, f'error_rate critical: expected ${ERROR_RATE_CRIT}, got {v}'
print('OK')
\"" "error_rate_critical_threshold_wrong"

# ── CHECK 8: availability warning threshold correct ───────────────────────
check "python3 -c \"
import json
rules = json.load(open('alert_rules.json'))
svc = '${SERVICES}'
v = rules['services'][svc]['availability_pct']['warning']
assert abs(float(v) - ${AVAIL_WARN}) < 0.001, f'availability warning: expected ${AVAIL_WARN}, got {v}'
print('OK')
\"" "availability_warning_threshold_wrong"

# ── CHECK 9: availability critical threshold correct ──────────────────────
check "python3 -c \"
import json
rules = json.load(open('alert_rules.json'))
svc = '${SERVICES}'
v = rules['services'][svc]['availability_pct']['critical']
assert abs(float(v) - ${AVAIL_CRIT}) < 0.001, f'availability critical: expected ${AVAIL_CRIT}, got {v}'
print('OK')
\"" "availability_critical_threshold_wrong"

# ── CHECK 10: routing critical→pagerduty ─────────────────────────────────
check "python3 -c \"
import json
routing = json.load(open('routing.json'))
r = routing['routes']['critical']
assert r.get('type') == 'pagerduty', f'critical type: expected pagerduty, got {r.get(\"type\")}'
assert r.get('key') == '${ROUTING_CRIT_KEY}', f'critical key: expected ${ROUTING_CRIT_KEY}, got {r.get(\"key\")}'
print('OK')
\"" "routing_critical_wrong"

# ── CHECK 11: routing warning→slack ──────────────────────────────────────
check "python3 -c \"
import json
routing = json.load(open('routing.json'))
r = routing['routes']['warning']
assert r.get('type') == 'slack', f'warning type: expected slack, got {r.get(\"type\")}'
assert r.get('channel') == '${ROUTING_WARN_CHAN}', f'warning channel: expected ${ROUTING_WARN_CHAN}, got {r.get(\"channel\")}'
print('OK')
\"" "routing_warning_wrong"

# ── CHECK 12: routing info→log ────────────────────────────────────────────
check "python3 -c \"
import json
routing = json.load(open('routing.json'))
r = routing['routes']['info']
assert r.get('type') == 'log', f'info type: expected log, got {r.get(\"type\")}'
assert r.get('target') == '${ROUTING_INFO_TARGET}', f'info target: expected ${ROUTING_INFO_TARGET}, got {r.get(\"target\")}'
print('OK')
\"" "routing_info_wrong"

# ── CHECK 13: simulator passes (no false positives, alerts fire, grouping) ─
check "python3 simulator.py && python3 -c \"
import json
r = json.load(open('check_results.json'))
assert r.get('simulator_ok') == True, f'simulator failed: {r.get(\"failed\")} checks failed'
print('OK')
\"" "simulator_failed"

# ── CHECK 14: simulator.py not modified ──────────────────────────────────
if [ -f "$TASK_DIR/workspace/simulator.py" ]; then
  check "diff -q '$TASK_DIR/workspace/simulator.py' simulator.py > /dev/null" \
    "simulator_modified"
fi

# ── CHECK 15: check_results.json written ─────────────────────────────────
check "[ -f check_results.json ]" "check_results_missing"

PARTIAL=$(python3 -c "print(round($PASSED/max(1,$CHECKS), 2))")
if [ "$PASSED" -eq "$CHECKS" ]; then SUCCESS=1; PASS=true; else SUCCESS=0; PASS=false; fi
FM=$(python3 -c "import json; print(json.dumps([x for x in '${FAILURES}'.split(',') if x]))")

cat > "$REPORTS/score.json" <<JSON
{
  "pass": $PASS,
  "primary": {"success": $SUCCESS},
  "secondary": {"checks_passed": $PASSED, "checks_total": $CHECKS, "partial_score": $PARTIAL},
  "failure_modes": $FM
}
JSON
