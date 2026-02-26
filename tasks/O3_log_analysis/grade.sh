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

# ── Load seed-specific expected values ───────────────────────────────────────
EXPECTED_JSON="$REPORTS/expected.json"
if [ -f "$EXPECTED_JSON" ]; then
  BUG_TYPE=$(python3 -c "import json; print(json.load(open('$EXPECTED_JSON'))['bug_type'])")
  FIX_FILE=$(python3 -c "import json; print(json.load(open('$EXPECTED_JSON'))['fix_file'])")
  FIX_FIELD=$(python3 -c "import json; print(json.load(open('$EXPECTED_JSON'))['fix_field'])")
  SIGNAL_A=$(python3 -c "import json; print(json.load(open('$EXPECTED_JSON'))['signal_error_a'])")
  SIGNAL_B=$(python3 -c "import json; print(json.load(open('$EXPECTED_JSON'))['signal_error_b'])")
  SUBSYSTEM=$(python3 -c "import json; print(json.load(open('$EXPECTED_JSON'))['subsystem'])")
  PORT=$(python3 -c "import json; print(json.load(open('$EXPECTED_JSON'))['port'])")
  ROOT_CAUSE=$(python3 -c "import json; print(json.load(open('$EXPECTED_JSON'))['root_cause'])")
  BUGGY_CONFIG_KEY=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('buggy_config_key') or '')")
  BUGGY_CONFIG_VALUE=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('buggy_config_value') or '')")
  CORRECT_CONFIG_VALUE=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('correct_config_value') or '')")
else
  echo "ERROR: expected.json not found at $EXPECTED_JSON" >&2
  BUG_TYPE="unknown"
  PORT=8080
  FIX_FILE="config/service.yaml"
  FIX_FIELD=""
  SIGNAL_A="ERR-0000"
  SIGNAL_B="ERR-0001"
  SUBSYSTEM="unknown"
  ROOT_CAUSE=""
  BUGGY_CONFIG_KEY=""
  BUGGY_CONFIG_VALUE=""
  CORRECT_CONFIG_VALUE=""
fi

cd "$WORKSPACE"

# ── CHECK 1: submission/root_cause.txt exists and is non-empty ────────────────
check "[ -s '$SUBMISSION/root_cause.txt' ]" "missing_root_cause_file"

# ── CHECK 2: root_cause.txt mentions the correct primary error code ───────────
check "grep -qi '${SIGNAL_A}' '$SUBMISSION/root_cause.txt'" "root_cause_missing_signal_a"

# ── CHECK 3: root_cause.txt mentions the correct secondary error code ─────────
check "grep -qi '${SIGNAL_B}' '$SUBMISSION/root_cause.txt'" "root_cause_missing_signal_b"

# ── CHECK 4: root_cause.txt mentions the subsystem ───────────────────────────
check "grep -qi '${SUBSYSTEM}' '$SUBMISSION/root_cause.txt'" "root_cause_missing_subsystem"

# ── CHECK 5: root_cause.txt mentions what file was changed ───────────────────
# Accept either the full path or just the filename component
FIX_BASENAME=$(basename "${FIX_FILE}")
check "grep -qi '${FIX_BASENAME}' '$SUBMISSION/root_cause.txt'" "root_cause_missing_fix_file"

# ── CHECK 6: the fix file actually exists and was modified ───────────────────
# Compare against the .orig snapshot saved in setup.sh
if [ "$FIX_FILE" = "config/service.yaml" ]; then
  ORIG="$WORKSPACE/.service.yaml.orig"
else
  ORIG="$WORKSPACE/.server.py.orig"
fi
check "[ -f '$WORKSPACE/$FIX_FILE' ]" "fix_file_missing"

DIFF_LINES=0
if [ -f "$ORIG" ] && [ -f "$WORKSPACE/$FIX_FILE" ]; then
  DIFF_LINES=$(diff "$ORIG" "$WORKSPACE/$FIX_FILE" | grep -c '^[<>]' || true)
fi

# ── CHECK 7: fix was actually applied (file changed) ─────────────────────────
check "[ $DIFF_LINES -gt 0 ]" "fix_not_applied"

# ── CHECK 8: fix is minimal (<=10 diff lines) ────────────────────────────────
check "[ $DIFF_LINES -le 10 ]" "excessive_diff"

# ── CHECK 9: config-level bugs — correct value is present ────────────────────
# Only meaningful when the fix is in config/service.yaml and has a known field+value
if [ -n "$BUGGY_CONFIG_KEY" ] && [ "$FIX_FILE" = "config/service.yaml" ]; then
  case "$BUG_TYPE" in
    connection_pool_exhaustion)
      check "python3 -c \"
import yaml
cfg = yaml.safe_load(open('config/service.yaml'))
v = cfg.get('max_connections', 0)
assert int(v) >= 20, f'max_connections={v} < 20'
print('CONFIG_OK')
\"" "config_value_not_fixed"
      ;;
    cache_stampede)
      check "python3 -c \"
import yaml
cfg = yaml.safe_load(open('config/service.yaml'))
v = cfg.get('cache_lock_enabled', False)
assert v is True or str(v).lower() == 'true', f'cache_lock_enabled={v}'
print('CONFIG_OK')
\"" "config_value_not_fixed"
      ;;
    config_drift)
      check "python3 -c \"
import yaml
cfg = yaml.safe_load(open('config/service.yaml'))
v = cfg.get('rate_limit_rps', 0)
assert int(v) >= 100, f'rate_limit_rps={v} < 100'
print('CONFIG_OK')
\"" "config_value_not_fixed"
      ;;
    *)
      # No config fix expected — give a free pass on this check
      check "true" "config_value_not_fixed"
      ;;
  esac
else
  # Fix is in src/server.py — check the relevant code fix
  case "$BUG_TYPE" in
    deadlock)
      # lock_a must be acquired before lock_b in process_order
      check "python3 -c \"
with open('src/server.py') as f:
    src = f.read()
# In process_order, lock_a should appear before lock_b
order_fn_start = src.find('def process_order')
order_fn_end   = src.find('def process_payment')
if order_fn_start == -1 or order_fn_end == -1:
    raise AssertionError('functions not found')
order_fn = src[order_fn_start:order_fn_end]
pos_a = order_fn.find('lock_a')
pos_b = order_fn.find('lock_b')
assert pos_a < pos_b and pos_a != -1, 'lock_a not acquired before lock_b in process_order'
print('LOCK_ORDER_OK')
\"" "code_fix_not_applied"
      ;;
    race_condition)
      # threading.Lock must be used to guard the counter
      check "python3 -c \"
with open('src/server.py') as f:
    src = f.read()
assert 'threading.Lock' in src or 'Lock()' in src, 'No Lock around counter'
# Also check the counter increment is inside a with-lock block
assert 'with ' in src, 'No with-lock block found'
print('LOCK_OK')
\"" "code_fix_not_applied"
      ;;
    *)
      check "true" "code_fix_not_applied"
      ;;
  esac
fi

# ── CHECK 10: service starts and /health returns 200 ─────────────────────────
python3 src/server.py &
SVC_PID=$!
cleanup() { kill "$SVC_PID" 2>/dev/null || true; kill -9 "$SVC_PID" 2>/dev/null || true; }
trap cleanup EXIT
sleep 1.5

HEALTH_OK=false
for i in $(seq 1 20); do
  set +e
  HTTP_CODE=$(python3 -c "
import urllib.request, sys
try:
    with urllib.request.urlopen('http://127.0.0.1:${PORT}/health', timeout=0.8) as r:
        sys.stdout.write(str(r.status))
except Exception:
    pass
" 2>/dev/null)
  set -e
  if [ "$HTTP_CODE" = "200" ]; then HEALTH_OK=true; break; fi
  sleep 0.3
done

check "[ '$HEALTH_OK' = 'true' ]" "health_endpoint_not_200"

# ── CHECK 11: /health body is {"status":"ok"} ─────────────────────────────────
if [ "$HEALTH_OK" = "true" ]; then
  HEALTH_BODY=$(python3 -c "
import urllib.request, sys
try:
    with urllib.request.urlopen('http://127.0.0.1:${PORT}/health', timeout=0.8) as r:
        sys.stdout.write(r.read().decode())
except Exception:
    pass
" 2>/dev/null)
  check "python3 -c \"
import json, sys
body = sys.argv[1]
obj = json.loads(body)
assert obj.get('status') == 'ok', f'status={obj.get(\\\"status\\\")}'
print('HEALTH_BODY_OK')
\" '$HEALTH_BODY'" "health_body_wrong"
fi

# ── CHECK 12: primary endpoint returns 200 after fix ─────────────────────────
ENDPOINT_OK=false
case "$BUG_TYPE" in
  connection_pool_exhaustion)  PRIMARY_PATH="/api/process" ;;
  deadlock)                    PRIMARY_PATH="/api/order"   ;;
  cache_stampede)              PRIMARY_PATH="/api/resource/test" ;;
  race_condition)              PRIMARY_PATH="/api/job"     ;;
  config_drift)                PRIMARY_PATH="/api/data"    ;;
  *)                           PRIMARY_PATH="/api/data"    ;;
esac

for i in $(seq 1 5); do
  set +e
  PRIMARY_CODE=$(python3 -c "
import urllib.request, sys
try:
    with urllib.request.urlopen('http://127.0.0.1:${PORT}${PRIMARY_PATH}', timeout=1.0) as r:
        sys.stdout.write(str(r.status))
except urllib.error.HTTPError as e:
    sys.stdout.write(str(e.code))
except Exception:
    pass
" 2>/dev/null)
  set -e
  if [ "$PRIMARY_CODE" = "200" ]; then ENDPOINT_OK=true; break; fi
  sleep 0.2
done

check "[ '$ENDPOINT_OK' = 'true' ]" "primary_endpoint_not_200"

# ── CHECK 13: service stays alive for 5 seconds (no crash on startup) ─────────
sleep 5
check "kill -0 '$SVC_PID' 2>/dev/null" "service_crashed_after_start"

# ── Scoring ───────────────────────────────────────────────────────────────────
PARTIAL=$(python3 -c "print(round($PASSED/max(1,$CHECKS), 2))")
if [ "$PASSED" -eq "$CHECKS" ]; then SUCCESS=1; PASS=true; else SUCCESS=0; PASS=false; fi
FM=$(python3 -c "import json; print(json.dumps([x for x in '${FAILURES}'.split(',') if x]))")

cat > "$REPORTS/score.json" <<JSON
{
  "pass": $PASS,
  "primary": {"success": $SUCCESS},
  "secondary": {
    "checks_passed": $PASSED,
    "checks_total": $CHECKS,
    "partial_score": $PARTIAL,
    "diff_lines": $DIFF_LINES,
    "bug_type": "${BUG_TYPE}",
    "fix_file": "${FIX_FILE}"
  },
  "failure_modes": $FM
}
JSON
