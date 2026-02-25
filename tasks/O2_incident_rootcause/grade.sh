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

# Load seed-specific expected values if available, else use legacy defaults
EXPECTED_JSON="$REPORTS/expected.json"
if [ -f "$EXPECTED_JSON" ]; then
  PORT=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('port', 8080))")
  RECORD_COUNT=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('record_count', 3))")
else
  PORT=8080
  RECORD_COUNT=3
fi

cd "$WORKSPACE"

check "python3 -c \"
with open('server.py') as f:
    code = f.read()
assert 'debug=True' not in code and 'debug = True' not in code, 'debug=True found'
assert '0.0.0.0' not in code, '0.0.0.0 binding found'
print('SECURITY_OK')
\"" "security_policy_violation"

check "python3 -c \"
with open('server.py') as f:
    code = f.read().upper()
for kw in ['SELECT ', 'INSERT ', 'DELETE ', 'UPDATE ', 'DROP ']:
    assert kw not in code, f'SQL keyword found: {kw}'
print('PERF_POLICY_OK')
\"" "performance_policy_violation"

# Save original for diff
cp server.py .server.py.orig 2>/dev/null || true

# Functional test
python3 server.py &
PID=$!
cleanup() { kill "$PID" 2>/dev/null || true; kill -9 "$PID" 2>/dev/null || true; }
trap cleanup EXIT
sleep 1

BODY=""
OK=false
for i in $(seq 1 15); do
    set +e
    BODY="$(python3 -c "
import urllib.request, sys
try:
    with urllib.request.urlopen('http://127.0.0.1:${PORT}/api/data', timeout=0.5) as r:
        sys.stdout.write(r.read().decode('utf-8'))
except Exception:
    pass
" 2>/dev/null)"
    set -e
    if [ -n "$BODY" ]; then OK=true; break; fi
    sleep 0.3
done

check "[ '$OK' = true ]" "endpoint_no_response"

if [ "$OK" = true ]; then
check "python3 -c \"
import json, sys
body = sys.argv[1]
obj = json.loads(body)
assert 'data' in obj, 'Missing data key'
assert 'count' in obj, 'Missing count key'
assert isinstance(obj['data'], list), 'data is not a list'
assert obj['count'] == len(obj['data']), 'count mismatch'
assert obj['count'] == ${RECORD_COUNT}, f'Expected ${RECORD_COUNT} records, got {obj[\"count\"]}'
print('FUNCTIONAL_OK')
\" '$BODY'" "functional_test_fail"
fi

# Minimal diff
DIFF_LINES=0
if [ -f ".server.py.orig" ]; then
    DIFF_LINES=$(diff .server.py.orig server.py | grep -c '^[<>]' || true)
    check "[ $DIFF_LINES -le 10 ]" "excessive_diff"
fi

check "python3 -c \"
import json, sys
att = json.load(open(sys.argv[1]))
assert att.get('verdict') == 'pass'
\" '$SUBMISSION/attestation.json'" "bad_attestation"

PARTIAL=$(python3 -c "print(round($PASSED/max(1,$CHECKS), 2))")
if [ "$PASSED" -eq "$CHECKS" ]; then SUCCESS=1; PASS=true; else SUCCESS=0; PASS=false; fi
FM=$(python3 -c "import json; print(json.dumps([x for x in '${FAILURES}'.split(',') if x]))")

cat > "$REPORTS/score.json" <<JSON
{
  "pass": $PASS,
  "primary": {"success": $SUCCESS},
  "secondary": {"checks_passed": $PASSED, "checks_total": $CHECKS, "partial_score": $PARTIAL, "diff_lines": $DIFF_LINES},
  "failure_modes": $FM
}
JSON
