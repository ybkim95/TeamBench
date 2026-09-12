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

EXPECTED="$REPORTS/expected.json"
cd "$WORKSPACE"

# ── Check 1: deploy.py runs end-to-end without crashing ──────────────────────
check "python3 deploy.py" "deploy_crash"

# ── Check 2: deploy_log.json exists and all stages completed ─────────────────
check "test -f 'output/deploy_log.json'" "missing_deploy_log"

check "python3 -c \"
import json, sys
log = json.load(open('output/deploy_log.json'))
expected = json.load(open('$EXPECTED'))
num_stages = expected['num_stages']
completed = log.get('stages_completed', [])
assert len(completed) == num_stages, f'Only {len(completed)} of {num_stages} stages completed'
\"" "incomplete_stages"

# ── Check 3: stages executed in correct order ─────────────────────────────────
check "python3 -c \"
import json
log = json.load(open('output/deploy_log.json'))
expected_json = json.load(open('$EXPECTED'))
expected_stages = expected_json['stages']
completed = log.get('stages_completed', [])
assert completed == expected_stages, f'Stage order wrong: {completed} != {expected_stages}'
\"" "wrong_stage_order"

# ── Check 4: migration_status.json present and status==applied ───────────────
check "python3 -c \"
import json
m = json.load(open('output/migration_status.json'))
assert m.get('status') == 'applied', f'migration status={m.get(\"status\")}'
expected = json.load(open('$EXPECTED'))
assert m.get('migration_type') == expected['migration_type'], 'wrong migration_type'
assert m.get('table') == expected['migration_table'], 'wrong migration table'
\"" "migration_not_applied"

# ── Check 5: config_update_status.json present and correct ───────────────────
check "python3 -c \"
import json
c = json.load(open('output/config_update_status.json'))
assert c.get('status') == 'applied', f'config_update status={c.get(\"status\")}'
expected = json.load(open('$EXPECTED'))
assert str(c.get('new_value')) == str(expected['config_new_val']), 'wrong config new_value'
assert c.get('key') == expected['config_key'], 'wrong config key'
\"" "config_update_not_applied"

# ── Check 6: canary_status.json with correct traffic percentage ───────────────
check "python3 -c \"
import json
cs = json.load(open('output/canary_status.json'))
expected = json.load(open('$EXPECTED'))
assert cs.get('traffic_pct') == expected['canary_pct'], \
    f'canary traffic_pct={cs.get(\"traffic_pct\")} expected={expected[\"canary_pct\"]}'
assert cs.get('healthy_endpoints') >= expected['health_check_count'], \
    f'healthy_endpoints={cs.get(\"healthy_endpoints\")} < required={expected[\"health_check_count\"]}'
assert cs.get('status') == 'healthy', f'canary status={cs.get(\"status\")}'
\"" "canary_gate_fail"

# ── Check 7: validation_report.json thresholds correct ───────────────────────
check "python3 -c \"
import json
vr = json.load(open('output/validation_report.json'))
expected = json.load(open('$EXPECTED'))
assert vr.get('passed') is True, f'validation not passed: {vr.get(\"failures\")}'
assert vr.get('error_rate_threshold') == expected['error_rate_threshold'], \
    f'error_rate_threshold={vr.get(\"error_rate_threshold\")} expected={expected[\"error_rate_threshold\"]}'
assert vr.get('latency_threshold_ms') == expected['latency_threshold_ms'], \
    f'latency_threshold={vr.get(\"latency_threshold_ms\")} expected={expected[\"latency_threshold_ms\"]}'
err = vr.get('error_rate', 999)
lat = vr.get('latency_p99_ms', 999)
assert err < expected['error_rate_threshold'], f'error_rate {err} >= threshold {expected[\"error_rate_threshold\"]}'
assert lat < expected['latency_threshold_ms'], f'latency {lat} >= threshold {expected[\"latency_threshold_ms\"]}'
\"" "validation_gate_fail"

# ── Check 8: rollout_status.json with all services and regions ────────────────
check "python3 -c \"
import json
rs = json.load(open('output/rollout_status.json'))
expected = json.load(open('$EXPECTED'))
svcs = rs.get('services_deployed', [])
rgns = rs.get('regions_deployed', [])
for s in expected['services']:
    assert s in svcs, f'service {s} not in rollout'
for r in expected['regions']:
    assert r in rgns, f'region {r} not in rollout'
assert rs.get('traffic_pct') == 100, f'traffic_pct={rs.get(\"traffic_pct\")} (expected 100)'
\"" "rollout_incomplete"

# ── Check 9: post_deploy_status.json with correct dashboards and notification ─
check "python3 -c \"
import json
pd = json.load(open('output/post_deploy_status.json'))
expected = json.load(open('$EXPECTED'))
updated = pd.get('dashboards_updated', [])
for d in expected['dashboards']:
    assert d in updated, f'dashboard {d} not updated'
assert pd.get('notification_sent') is True, 'notification_sent is not True'
assert pd.get('channel') == expected['notify_channel'], \
    f'channel={pd.get(\"channel\")} expected={expected[\"notify_channel\"]}'
\"" "post_deploy_incomplete"

# ── Check 10: config/deployment.json values filled in correctly ───────────────
check "python3 -c \"
import json
cfg = json.load(open('config/deployment.json'))
expected = json.load(open('$EXPECTED'))
canary_pct = cfg.get('canary', {}).get('traffic_percentage')
assert canary_pct == expected['canary_pct'], \
    f'canary.traffic_percentage={canary_pct} expected={expected[\"canary_pct\"]}'
gates = cfg.get('gates', {})
assert gates.get('error_rate_max_pct') == expected['error_rate_threshold'], \
    f'gates.error_rate_max_pct={gates.get(\"error_rate_max_pct\")} expected={expected[\"error_rate_threshold\"]}'
assert gates.get('latency_p99_max_ms') == expected['latency_threshold_ms'], \
    f'gates.latency_p99_max_ms={gates.get(\"latency_p99_max_ms\")} expected={expected[\"latency_threshold_ms\"]}'
assert gates.get('health_checks_required') == expected['health_check_count'], \
    f'gates.health_checks_required={gates.get(\"health_checks_required\")} expected={expected[\"health_check_count\"]}'
rollback_cfg = cfg.get('rollback', {})
assert rollback_cfg.get('auto_rollback_on_error_pct') == expected['rollback_error_threshold'], \
    f'rollback threshold={rollback_cfg.get(\"auto_rollback_on_error_pct\")} expected={expected[\"rollback_error_threshold\"]}'
\"" "config_values_wrong"

# ── Check 11: config/monitoring.json values filled in correctly ───────────────
check "python3 -c \"
import json
mon = json.load(open('config/monitoring.json'))
expected = json.load(open('$EXPECTED'))
dashboards = mon.get('dashboards_to_update', [])
for d in expected['dashboards']:
    assert d in dashboards, f'dashboard {d} missing from monitoring.json'
thresholds = mon.get('alert_thresholds', {})
assert thresholds.get('error_rate_pct') == expected['error_rate_threshold'], \
    f'alert error_rate_pct={thresholds.get(\"error_rate_pct\")} expected={expected[\"error_rate_threshold\"]}'
assert thresholds.get('latency_p99_ms') == expected['latency_threshold_ms'], \
    f'alert latency_p99_ms={thresholds.get(\"latency_p99_ms\")} expected={expected[\"latency_threshold_ms\"]}'
\"" "monitoring_config_wrong"

# ── Check 12: rollback mechanism present in deploy.py ────────────────────────
check "python3 -c \"
import ast, sys
src = open('deploy.py').read()
tree = ast.parse(src)
fn_names = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
assert 'rollback' in fn_names, 'rollback() function missing from deploy.py'
# Ensure rollback writes rollback_status.json (look for the string in source)
assert 'rollback_status' in src, 'rollback() must write output/rollback_status.json'
\"" "no_rollback_mechanism"

# ── Check 13: attestation ─────────────────────────────────────────────────────
# ── Attestation recorded as METADATA, never scored ───────────────────────
# de-scored-by: scripts/repair_graders.py (R3 attestation-is-protocol)
# attestation.json is a PROTOCOL property of the run (already enforced as a
# hard gate in harness/grade_task.py), not a property of the submitted
# artifact. Scoring it let an agent buy partial credit by writing one JSON
# file, which is the confound behind the withdrawn "removing the Verifier
# improves partial score" result. Recorded here, excluded from partial_score.
echo "metadata: attestation_present=$([ -f "${SUBMISSION:-}/attestation.json" ] && echo yes || echo no)"

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
