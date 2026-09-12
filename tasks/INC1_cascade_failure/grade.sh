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
  SVC_A=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d['svc_a'])")
  SVC_B=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d['svc_b'])")
  SVC_C=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d['svc_c'])")
  BUG_ID=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d['root_cause_bug'])")
else
  SVC_A="api_gateway"
  SVC_B="user_service"
  SVC_C="order_service"
  BUG_ID="bad_timeout"
fi

cd "$WORKSPACE"

# ── 1. All service files import cleanly ──────────────────────────────────────
check "python3 -c \"
import importlib.util, sys, os
for svc in ['${SVC_A}', '${SVC_B}', '${SVC_C}']:
    path = os.path.join('.', svc + '.py')
    spec = importlib.util.spec_from_file_location(svc, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
print('IMPORTS_OK')
\"" "services_fail_to_import"

# ── 2. svc_a health_check() returns {status:ok} ─────────────────────────────
check "python3 -c \"
import importlib.util, os
spec = importlib.util.spec_from_file_location('${SVC_A}', './${SVC_A}.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
result = mod.health_check()
assert result.get('status') == 'ok', f'svc_a health={result}'
assert result.get('service') == '${SVC_A}', f'svc_a service field={result}'
print('SVC_A_HEALTH_OK')
\"" "svc_a_health_fail"

# ── 3. svc_b health_check() returns {status:ok} ─────────────────────────────
check "python3 -c \"
import importlib.util, os
spec = importlib.util.spec_from_file_location('${SVC_B}', './${SVC_B}.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
result = mod.health_check()
assert result.get('status') == 'ok', f'svc_b health={result}'
assert result.get('service') == '${SVC_B}', f'svc_b service field={result}'
print('SVC_B_HEALTH_OK')
\"" "svc_b_health_fail"

# ── 4. svc_c health_check() returns {status:ok} ─────────────────────────────
check "python3 -c \"
import importlib.util, os
spec = importlib.util.spec_from_file_location('${SVC_C}', './${SVC_C}.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
result = mod.health_check()
assert result.get('status') == 'ok', f'svc_c health={result}'
assert result.get('service') == '${SVC_C}', f'svc_c service field={result}'
print('SVC_C_HEALTH_OK')
\"" "svc_c_health_fail"

# ── 5. svc_a root-cause bug is fixed ────────────────────────────────────────
check "python3 -c \"
bug_id = '${BUG_ID}'
with open('${SVC_A}.py') as f:
    code = f.read()
if bug_id == 'bad_timeout':
    # timeout_ms must not be used raw when config value is 0
    # check that either timeout is corrected in config or code guards against 0
    import json
    cfg = json.load(open('config.json'))
    t = cfg.get('timeouts', {}).get('upstream_ms', -1)
    assert t > 0, f'upstream_ms still 0 in config: {t}'
elif bug_id == 'bad_connection_string':
    import json
    cfg = json.load(open('config.json'))
    # find any service entry that was 'localhost' — must now be 127.0.0.1
    for svc_cfg in cfg.get('services', {}).values():
        assert svc_cfg.get('host') != 'localhost', 'host still localhost in config'
elif bug_id == 'missing_retry':
    assert 'range(3)' in code or 'retry' in code.lower() or 'attempt' in code.lower(), \
        'No retry logic found in svc_a'
elif bug_id == 'wrong_port':
    import json
    cfg = json.load(open('config.json'))
    from generators.base import TaskGenerator  # not available in grader; use expected
    import sys; sys.path.insert(0, '${REPORTS}/..')
    expected = json.load(open('${REPORTS}/expected.json'))
    correct_port = expected['port_b']
    actual_port = cfg['services'].get(expected['svc_b'], {}).get('port', -1)
    assert actual_port == correct_port, f'port still wrong: {actual_port} != {correct_port}'
elif bug_id == 'disabled_healthcheck':
    # health_check must not return status=error when _service_ok is True
    import importlib.util
    spec = importlib.util.spec_from_file_location('svc_a_mod', '${SVC_A}.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    r = mod.health_check()
    assert r.get('status') == 'ok', f'health still returns error: {r}'
print('ROOT_CAUSE_FIXED')
\"" "root_cause_not_fixed"

# ── 6. svc_b has retry/circuit-breaker guard ────────────────────────────────
check "python3 -c \"
with open('${SVC_B}.py') as f:
    code = f.read()
has_retry = (
    'range(3)' in code or 'range(2)' in code or
    'retry' in code.lower() or
    'attempt' in code.lower() or
    'circuit' in code.lower() or
    'for attempt' in code or
    'for i in range' in code
)
assert has_retry, 'No retry/circuit-breaker pattern found in svc_b'
print('SVC_B_RETRY_OK')
\"" "svc_b_no_retry"

# ── 7. svc_c has atomic write guard ─────────────────────────────────────────
check "python3 -c \"
with open('${SVC_C}.py') as f:
    code = f.read()
# Either raises on incomplete record, or builds entry atomically before append
has_guard = (
    'raise' in code or
    'ValueError' in code or
    'atomic' in code.lower() or
    'if any' in code or
    'if None' in code or
    'is None' in code
)
assert has_guard, 'No partial-write guard found in svc_c'
# Also verify store() doesn't append before all fields are set
# Simple heuristic: _STORE.append must come after entry is fully built
lines = code.splitlines()
append_idx = next((i for i, l in enumerate(lines) if '_STORE.append' in l), -1)
if append_idx >= 0:
    pre = '\n'.join(lines[:append_idx])
    assert 'entry[\"checksum\"]' in pre or 'checksum' in pre, \
        'checksum may not be set before append'
print('SVC_C_GUARD_OK')
\"" "svc_c_no_atomic_guard"

# ── 8. Fix order: svc_c modified before svc_b, svc_b before svc_a ───────────
check "python3 -c \"
import os
ta = os.path.getmtime('${SVC_A}.py')
tb = os.path.getmtime('${SVC_B}.py')
tc = os.path.getmtime('${SVC_C}.py')
# Allow any of them to be equal (modified in same second); strict: tc <= tb <= ta
# We check that svc_a was not modified BEFORE svc_c (that would be wrong order)
# If all were modified at the same time (bulk edit), we skip order check
if ta != tc:
    assert tc <= ta, f'svc_a fixed before svc_c (wrong order): tc={tc:.3f} ta={ta:.3f}'
if tb != tc:
    assert tc <= tb, f'svc_b fixed before svc_c (wrong order): tc={tc:.3f} tb={tb:.3f}'
print('FIX_ORDER_OK')
\"" "wrong_fix_order"

# ── 9. Diff size not excessive ───────────────────────────────────────────────
check "python3 -c \"
import os
total_lines = 0
for svc in ['${SVC_A}', '${SVC_B}', '${SVC_C}']:
    path = svc + '.py'
    if os.path.isfile(path):
        with open(path) as f:
            total_lines += len(f.readlines())
# Heuristic: total line count of all 3 files should stay reasonable (< 250)
assert total_lines < 250, f'Files appear over-extended: {total_lines} lines total'
print('DIFF_SIZE_OK')
\"" "excessive_changes"

# ── 10. Attestation ──────────────────────────────────────────────────────────
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
