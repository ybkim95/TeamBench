#!/usr/bin/env bash
# GO3_channel_deadlock grader
set -o pipefail

WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
REPORTS="${2:-${REPORTS_DIR:-/reports}}"
SUBMISSION="${3:-/submission}"
TASK_DIR="${4:-/task}"

mkdir -p "${REPORTS}"

CHECKS=0; PASSED=0; FAILURES=""

cd "${WORKSPACE}"

# ---------------------------------------------------------------------------
# Read seed-specific expected values from expected.json
# ---------------------------------------------------------------------------
EXPECTED_JSON="${REPORTS}/expected.json"
if [ ! -f "${EXPECTED_JSON}" ]; then
  EXPECTED_JSON="$(dirname "$0")/expected.json"
fi

BUF_SIZE=4
if [ -f "${EXPECTED_JSON}" ]; then
  BUF_SIZE=$(python3 -c "
import json
d = json.load(open('${EXPECTED_JSON}'))
print(d.get('buf_size', 4))
" 2>/dev/null || echo 4)
fi

# ---------------------------------------------------------------------------
# C1: go build compiles cleanly
# ---------------------------------------------------------------------------
CHECKS=$((CHECKS + 1))
if go build ./... > /tmp/go3_build.out 2>&1; then
  PASSED=$((PASSED + 1))
else
  FAILURES="${FAILURES:+${FAILURES},}build_failed"
fi

# ---------------------------------------------------------------------------
# C2: go vet passes
# ---------------------------------------------------------------------------
CHECKS=$((CHECKS + 1))
if go vet ./... > /tmp/go3_vet.out 2>&1; then
  PASSED=$((PASSED + 1))
else
  FAILURES="${FAILURES:+${FAILURES},}vet_failed"
fi

# ---------------------------------------------------------------------------
# C3: all tests pass within timeout (primary correctness check)
# ---------------------------------------------------------------------------
CHECKS=$((CHECKS + 1))
if go test -timeout 30s -v ./... > /tmp/go3_test.out 2>&1; then
  PASSED=$((PASSED + 1))
else
  FAILURES="${FAILURES:+${FAILURES},}tests_failed_or_timed_out"
fi

# ---------------------------------------------------------------------------
# C4: Bug 1 fixed — source channel is buffered
# Detect make(chan <Type>) with no capacity argument in the source function.
# We look for make(chan <ident>) without a trailing comma+size inside the
# source function body. If the line has make(chan <Type>, ...) it is buffered.
# ---------------------------------------------------------------------------
CHECKS=$((CHECKS + 1))
# Extract source function body (up to next top-level func) and check all
# make(chan ...) calls have a second argument.
UNBUFFERED_CHAN=$(python3 -c "
import re, sys
try:
    src = open('pipeline.go').read()
    # Find source function body — between first func ... { and matching }
    # Simple heuristic: look for 'make(chan ' patterns without a comma
    makes = re.findall(r'make\(chan\s+\w+\)', src)
    # Any make(chan T) with no size arg is unbuffered
    print('fail' if makes else 'pass')
except Exception as e:
    print('fail')
" 2>/dev/null || echo "fail")
if [ "${UNBUFFERED_CHAN}" = "pass" ]; then
  PASSED=$((PASSED + 1))
else
  FAILURES="${FAILURES:+${FAILURES},}source_channel_unbuffered"
fi

# ---------------------------------------------------------------------------
# C5: Bug 2 fixed — filter output channel is closed
# The closing goroutine inside the filter function must call close(filterCh)
# or close() on whatever the filter output channel variable is named.
# We count close( calls in pipeline.go; after fix there should be >= 3
# (source closes its ch, transform closes out, filter closes its ch).
# ---------------------------------------------------------------------------
CHECKS=$((CHECKS + 1))
CLOSE_COUNT=$(grep -c 'close(' pipeline.go 2>/dev/null || echo 0)
if [ "${CLOSE_COUNT}" -ge 3 ]; then
  PASSED=$((PASSED + 1))
else
  FAILURES="${FAILURES:+${FAILURES},}filter_channel_not_closed"
fi

# ---------------------------------------------------------------------------
# C6: Bug 4 fixed — every wg.Add(1) has a corresponding wg.Done()
# After fix the conditional guard `if workerID < workers-1` should be gone.
# We detect the bug pattern: wg.Done() inside an if/guard block.
# ---------------------------------------------------------------------------
CHECKS=$((CHECKS + 1))
WG_MISMATCH=$(python3 -c "
try:
    src = open('pipeline.go').read()
    # Bug pattern: wg.Done() only called conditionally (inside 'if workerID')
    import re
    # Look for the guard pattern: if <var> < workers
    has_guard = bool(re.search(r'if\s+\w+\s*<\s*workers\s*-\s*1', src))
    print('fail' if has_guard else 'pass')
except Exception:
    print('fail')
" 2>/dev/null || echo "fail")
if [ "${WG_MISMATCH}" = "pass" ]; then
  PASSED=$((PASSED + 1))
else
  FAILURES="${FAILURES:+${FAILURES},}waitgroup_counter_mismatch"
fi

# ---------------------------------------------------------------------------
# C7: attestation.json verdict=pass
# ---------------------------------------------------------------------------
CHECKS=$((CHECKS + 1))
if python3 -c "
import json, sys
att = json.load(open(sys.argv[1]))
assert att.get('verdict') == 'pass'
" "${SUBMISSION}/attestation.json" 2>/dev/null; then
  PASSED=$((PASSED + 1))
else
  FAILURES="${FAILURES:+${FAILURES},}bad_attestation"
fi

# ---------------------------------------------------------------------------
# Write score.json
# ---------------------------------------------------------------------------
PARTIAL=$(python3 -c "print(round($PASSED/max(1,$CHECKS), 2))")
if [ "$PASSED" -eq "$CHECKS" ]; then
  PASS=true
else
  PASS=false
fi
FM=$(python3 -c "import json; print(json.dumps([x for x in '${FAILURES}'.split(',') if x]))")

cat > "${REPORTS}/score.json" <<JSON
{
  "pass": ${PASS},
  "primary": {"success": $([ "${PASS}" = "true" ] && echo 1 || echo 0)},
  "secondary": {
    "checks_passed": ${PASSED},
    "checks_total": ${CHECKS},
    "partial_score": ${PARTIAL}
  },
  "failure_modes": ${FM}
}
JSON
