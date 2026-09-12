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
if [ -f "$EXPECTED_JSON" ]; then
  SVC_NAME=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d['service_name'])")
  OLD_VER=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d['old_version'])")
  NEW_VER=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d['new_version'])")
  CFG_KEY=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d['config_key'])")
  CFG_OLD=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d['config_old_value'])")
  SCHEMA_CHANGED=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(str(d['schema_changed']).lower())")
  MIGRATION_ID=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('migration_id') or '')")
  PRESERVE_CAT=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d['preserve_category'])")
  DISCARD_CAT=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d['discard_category'])")
  PRESERVE_IDS=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(json.dumps(d['preserve_ids']))")
  DISCARD_IDS=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(json.dumps(d['discard_ids']))")
  HEALTH_ENDPOINT=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d['health_endpoint'])")
  HEALTH_INDICATOR=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d['health_indicator'])")
else
  SVC_NAME="frontend"
  OLD_VER="2.4.1"
  NEW_VER="2.5.0"
  CFG_KEY="max_connections"
  CFG_OLD="100"
  SCHEMA_CHANGED="true"
  MIGRATION_ID="m_20240615_001"
  PRESERVE_CAT="payment_events"
  DISCARD_CAT="failed_sessions"
  PRESERVE_IDS='["rec_00001","rec_00002","rec_00003"]'
  DISCARD_IDS='["tmp_00001","tmp_00002"]'
  HEALTH_ENDPOINT="http://localhost:8080/health"
  HEALTH_INDICATOR="healthy"
fi

cd "$WORKSPACE"

# ── 1. rollback.py runs without error ────────────────────────────────────────
check "python3 rollback.py" "rollback_script_failed"

# ── 2. deploy_state.json status=rolled_back ───────────────────────────────────
check "python3 -c \"
import json
state = json.load(open('deploy_state.json'))
assert state.get('status') == 'rolled_back', f'status={state.get(\"status\")}'
print('STATUS_OK')
\"" "deploy_state_not_rolled_back"

# ── 3. deploy_state.json current_version reverted to old version ─────────────
check "python3 -c \"
import json
state = json.load(open('deploy_state.json'))
assert state.get('current_version') == '${OLD_VER}', \
    f'current_version={state.get(\"current_version\")} (expected ${OLD_VER})'
print('VERSION_REVERTED')
\"" "version_not_reverted"

# ── 4. deploy_state.json traffic_paused=false (traffic resumed) ───────────────
check "python3 -c \"
import json
state = json.load(open('deploy_state.json'))
assert state.get('traffic_paused') == False, \
    f'traffic_paused={state.get(\"traffic_paused\")} (should be False after rollback)'
print('TRAFFIC_RESUMED')
\"" "traffic_not_resumed"

# ── 5. Rollback step order correct ────────────────────────────────────────────
check "python3 -c \"
import json
log = json.load(open('rollback_log.json'))
steps = [e['step'] for e in log]
EXPECTED_ORDER = [
    'pause_traffic',
    'revert_app_code',
    'rollback_database',
    'restore_config',
    'resume_traffic',
    'verify_health',
]
# All 6 steps must appear
for s in EXPECTED_ORDER:
    assert s in steps, f'Missing step: {s}'
# Check ordering: pause_traffic must come before revert_app_code
pi = steps.index('pause_traffic')
ri = steps.index('revert_app_code')
assert pi < ri, f'pause_traffic ({pi}) must precede revert_app_code ({ri})'
# revert_app_code before rollback_database
dbi = steps.index('rollback_database')
assert ri < dbi, f'revert_app_code ({ri}) must precede rollback_database ({dbi})'
# rollback_database before restore_config
rci = steps.index('restore_config')
assert dbi < rci, f'rollback_database ({dbi}) must precede restore_config ({rci})'
# restore_config before resume_traffic
resi = steps.index('resume_traffic')
assert rci < resi, f'restore_config ({rci}) must precede resume_traffic ({resi})'
# resume_traffic before verify_health
vhi = steps.index('verify_health')
assert resi < vhi, f'resume_traffic ({resi}) must precede verify_health ({vhi})'
print('STEP_ORDER_OK')
\"" "wrong_step_order"

# ── 6. Database rollback correct (conditional on schema_changed) ──────────────
check "python3 -c \"
import json
schema_changed = '${SCHEMA_CHANGED}' == 'true'
migration_id = '${MIGRATION_ID}'
migrations = json.load(open('database/migrations.json'))
applied = migrations.get('applied', [])
if schema_changed and migration_id:
    # Must find the migration with status rolled_back
    migration_entry = next(
        (m for m in applied if m.get('id') == migration_id), None
    )
    assert migration_entry is not None, f'Migration {migration_id} not found in applied list'
    assert migration_entry.get('status') == 'rolled_back', \
        f'Migration {migration_id} status={migration_entry.get(\"status\")} (expected rolled_back)'
else:
    # No schema change — applied list should remain empty (no extra entries added)
    assert len(applied) == 0 or all(
        m.get('status') != 'rolled_back' or m.get('id') != migration_id
        for m in applied
    ), 'DB rollback performed but schema_changed=False'
print('DB_ROLLBACK_OK')
\"" "db_rollback_incorrect"

# ── 7. Config restored: active_config.json matches old_config.json ────────────
check "python3 -c \"
import json
old_cfg = json.load(open('config/old_config.json'))
act_cfg = json.load(open('config/active_config.json'))
assert act_cfg == old_cfg, \
    f'active_config does not match old_config: {act_cfg} vs {old_cfg}'
print('CONFIG_RESTORED')
\"" "config_not_restored"

# ── 8. Specific config key restored to old value ──────────────────────────────
check "python3 -c \"
import json
act_cfg = json.load(open('config/active_config.json'))
key = '${CFG_KEY}'
expected_val = json.loads('${CFG_OLD}')
actual_val = act_cfg.get(key)
assert actual_val == expected_val, \
    f'{key}={actual_val!r} (expected {expected_val!r})'
print('CONFIG_KEY_OK')
\"" "config_key_not_restored"

# ── 9. Preserved data present in preserved_data.json ─────────────────────────
check "python3 -c \"
import json
exp = json.load(open('${EXPECTED_JSON}'))
preserve_cat = exp['preserve_category']
preserve_ids = exp['preserve_ids']
data = json.load(open('preserved_data.json'))
records = data.get(preserve_cat, [])
actual_ids = {r.get('id') for r in records}
for pid in preserve_ids:
    assert pid in actual_ids, f'Preserved record {pid} missing from preserved_data.json'
print('PRESERVED_DATA_OK')
\"" "preserved_data_missing"

# ── 10. Discarded data absent from preserved_data.json ───────────────────────
check "python3 -c \"
import json
exp = json.load(open('${EXPECTED_JSON}'))
discard_cat = exp['discard_category']
discard_ids = exp['discard_ids']
data = json.load(open('preserved_data.json'))
records = data.get(discard_cat, [])
actual_ids = {r.get('id') for r in records}
for did in discard_ids:
    assert did not in actual_ids, f'Discarded record {did} must not appear in preserved_data.json'
print('DISCARDED_DATA_ABSENT')
\"" "discarded_data_present"

# ── 11. Health check result file correct ─────────────────────────────────────
check "python3 -c \"
import json
result = json.load(open('health_check_result.json'))
assert result.get('health_status') == 'ok', \
    f'health_status={result.get(\"health_status\")} (expected ok)'
assert result.get('version') == '${OLD_VER}', \
    f'health version={result.get(\"version\")} (expected ${OLD_VER})'
print('HEALTH_CHECK_OK')
\"" "health_check_failed"

# ── 12. Attestation with verdict=pass ─────────────────────────────────────────
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
