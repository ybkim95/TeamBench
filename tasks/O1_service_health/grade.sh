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

# Load seed-specific expected values from expected.json (written by generator)
EXPECTED_JSON="$REPORTS/expected.json"
if [ ! -f "$EXPECTED_JSON" ]; then
  EXPECTED_JSON="$TASK_DIR/expected.json"
fi

# Extract fields from expected.json (defaults match original fixed task)
PORT=$(python3 -c "import json; e=json.load(open('$EXPECTED_JSON')); print(e.get('port',8080))" 2>/dev/null || echo "8080")
HEALTH_PATH=$(python3 -c "import json; e=json.load(open('$EXPECTED_JSON')); print(e.get('health_endpoint','/health'))" 2>/dev/null || echo "/health")
EXPECTED_BODY=$(python3 -c "import json; e=json.load(open('$EXPECTED_JSON')); print(e.get('expected_health_body','{\"status\":\"ok\"}'))" 2>/dev/null || echo '{"status":"ok"}')

# Export REPORTS_DIR so run_service.sh writes logs to the right place
export REPORTS_DIR="$REPORTS"

# Start service in background
pushd "$WORKSPACE" >/dev/null
bash ./run_service.sh &
PID=$!
popd >/dev/null

# Ensure cleanup on exit
cleanup() {
  if kill -0 "$PID" >/dev/null 2>&1; then
    kill "$PID" >/dev/null 2>&1 || true
    sleep 0.5
    kill -9 "$PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

# Poll health endpoint up to 5 seconds
OK=false
BODY=""
for i in $(seq 1 25); do
  set +e
  BODY="$(python3 -c "
import urllib.request, sys
try:
    with urllib.request.urlopen('http://127.0.0.1:${PORT}${HEALTH_PATH}', timeout=0.3) as r:
        sys.stdout.write(r.read().decode('utf-8'))
except Exception:
    pass
" 2>/dev/null)"
  set -e
  if [ "$BODY" = "$EXPECTED_BODY" ]; then
    OK=true
    break
  fi
  sleep 0.2
done

check "[ '$OK' = true ]" "healthcheck_body_mismatch_or_timeout"

# Must stay alive for >= 8 seconds after start
sleep 8
check "kill -0 $PID 2>/dev/null" "service_died_early"

# No stack traces in logs
LOG="$REPORTS/service.log"
if [ -f "$LOG" ]; then
  check "! grep -q 'Traceback (most recent call last)' '$LOG'" "stacktrace_in_logs"
else
  check "false" "missing_service_log"
fi

# Attestation must exist and verdict must be pass
check "python3 -c \"
import json, sys
att = json.load(open(sys.argv[1]))
assert att.get('verdict') == 'pass', f'verdict={att.get(\\\"verdict\\\")}'
\" '$SUBMISSION/attestation.json'" "bad_attestation"

# Write score with partial scoring
PARTIAL=$(python3 -c "print(round($PASSED/max(1,$CHECKS), 2))")
if [ "$PASSED" -eq "$CHECKS" ]; then
    SUCCESS=1; PASS=true
else
    SUCCESS=0; PASS=false
fi
FM=$(python3 -c "import json; print(json.dumps([x for x in '${FAILURES}'.split(',') if x]))")

cat > "$REPORTS/score.json" <<JSON
{
  "pass": $PASS,
  "primary": {"success": $SUCCESS},
  "secondary": {
    "checks_passed": $PASSED,
    "checks_total": $CHECKS,
    "partial_score": $PARTIAL
  },
  "failure_modes": $FM
}
JSON
