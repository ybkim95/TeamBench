#!/usr/bin/env bash
set -o pipefail
WORKSPACE="$1"
REPORTS="$2"
SUBMISSION="$3"
TASK_DIR="$4"

mkdir -p "$REPORTS"

CHECKS=0; PASSED=0; FAILURES=""

cd "$WORKSPACE"

# ---------------------------------------------------------------------------
# Seed-aware: read expected.json if present (generated tasks)
# ---------------------------------------------------------------------------
EXPECTED_JSON="$REPORTS/expected.json"
if [ ! -f "$EXPECTED_JSON" ]; then
  EXPECTED_JSON="$(dirname "$0")/expected.json"
fi

# Determine expected run output and Result type name from expected.json or defaults
EXPECTED_RUN_MSG="All 10 jobs completed"
RESULT_TYPE="Result"
if [ -f "$EXPECTED_JSON" ]; then
  EXPECTED_RUN_MSG=$(python3 -c "
import json
d = json.load(open('$EXPECTED_JSON'))
print(d.get('print_msg', 'All 10 jobs completed'))
" 2>/dev/null || echo "All 10 jobs completed")
  RESULT_TYPE=$(python3 -c "
import json
d = json.load(open('$EXPECTED_JSON'))
print(d.get('Result', 'Result'))
" 2>/dev/null || echo "Result")
fi

# Check 1: go build compiles cleanly
CHECKS=$((CHECKS + 1))
if go build ./... > /tmp/go_build_out 2>&1; then
  PASSED=$((PASSED + 1))
else
  FAILURES="${FAILURES:+${FAILURES},}build_failed"
fi

# Check 2: go vet passes
CHECKS=$((CHECKS + 1))
if go vet ./... > /tmp/go_vet_out 2>&1; then
  PASSED=$((PASSED + 1))
else
  FAILURES="${FAILURES:+${FAILURES},}vet_failed"
fi

# Check 3: go test -race passes (no data races, no deadlocks, all tests pass)
CHECKS=$((CHECKS + 1))
if go test -race -count=1 -timeout 30s ./... > /tmp/go_test_out 2>&1; then
  PASSED=$((PASSED + 1))
else
  FAILURES="${FAILURES:+${FAILURES},}race_or_test_failed"
fi

# Check 4: go run completes within 10s and prints expected output
CHECKS=$((CHECKS + 1))
RUN_OUT=$(timeout 10s go run . 2>&1 || true)
if echo "$RUN_OUT" | grep -qF "$EXPECTED_RUN_MSG"; then
  PASSED=$((PASSED + 1))
else
  FAILURES="${FAILURES:+${FAILURES},}run_output_wrong"
fi

# Check 5a: stats map is protected — worker must use a mutex or sync.Map
CHECKS=$((CHECKS + 1))
if grep -qE 'sync\.Map|mu2\.Lock\(\)|mu\.Lock\(\)' main.go; then
  PASSED=$((PASSED + 1))
else
  FAILURES="${FAILURES:+${FAILURES},}stats_not_protected"
fi

# Check 5b: results channel is buffered (capacity argument present after the type)
CHECKS=$((CHECKS + 1))
# Match make(chan <ResultType>, <anything>) but not make(chan <ResultType>) with no second arg
if grep -E "make\\(chan ${RESULT_TYPE}," main.go | grep -qvE "make\\(chan ${RESULT_TYPE}\\)"; then
  PASSED=$((PASSED + 1))
else
  FAILURES="${FAILURES:+${FAILURES},}results_channel_unbuffered"
fi

# Check 5c: lock ordering is consistent — getStats must not do mu2.Lock before mu1.Lock
# (the classic deadlock pattern). If only one mutex appears in getStats, that's fine too.
CHECKS=$((CHECKS + 1))
GETSTATS_BODY=$(awk '/^func.*getStats/,/^}/' main.go 2>/dev/null || true)
HAS_MU1=$(echo "$GETSTATS_BODY" | grep -c 'mu1\.Lock' || true)
HAS_MU2=$(echo "$GETSTATS_BODY" | grep -c 'mu2\.Lock' || true)
if [ "$HAS_MU1" -gt 0 ] && [ "$HAS_MU2" -gt 0 ]; then
  # Both locks present — mu1 must appear before mu2
  MU1_LINE=$(echo "$GETSTATS_BODY" | grep -n 'mu1\.Lock' | head -1 | cut -d: -f1)
  MU2_LINE=$(echo "$GETSTATS_BODY" | grep -n 'mu2\.Lock' | head -1 | cut -d: -f1)
  if [ -n "$MU1_LINE" ] && [ -n "$MU2_LINE" ] && [ "$MU1_LINE" -lt "$MU2_LINE" ]; then
    PASSED=$((PASSED + 1))
  else
    FAILURES="${FAILURES:+${FAILURES},}lock_order_inconsistent"
  fi
else
  # Only one or zero locks in getStats — deadlock resolved by restructuring.
  PASSED=$((PASSED + 1))
fi

# Check 6: attestation.json verdict=pass
CHECKS=$((CHECKS + 1))
if python3 -c "
import json, sys
att = json.load(open(sys.argv[1]))
assert att.get('verdict') == 'pass'
" "$SUBMISSION/attestation.json" 2>/dev/null; then
  PASSED=$((PASSED + 1))
else
  FAILURES="${FAILURES:+${FAILURES},}bad_attestation"
fi

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
