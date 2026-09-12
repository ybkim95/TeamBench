#!/usr/bin/env bash
# GH16_fiber_cors_logic grader
set -uo pipefail

WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
REPORTS="${2:-${REPORTS_DIR:-/reports}}"
SUBMISSION="${3:-/submission}"
TASK_DIR="${4:-/task}"

source /usr/local/lib/venv/bin/activate 2>/dev/null || true

pass=true
partial=0
total=6
findings=""

check() {
    local id="$1"
    local desc="$2"
    local result="$3"
    if [ "$result" = "pass" ]; then
        partial=$((partial + 1))
        findings="${findings}{\"id\":\"${id}\",\"ok\":true,\"note\":\"${desc}\"},"
    else
        pass=false
        findings="${findings}{\"id\":\"${id}\",\"ok\":false,\"note\":\"${desc}\"},"
    fi
}

cd "${WORKSPACE}"

# C1: Go files compile
result=$(go build ./... 2>/dev/null && echo "pass" || echo "fail")
check "C1" "go build ./... succeeds" "$result"

# C2: go vet passes
result=$(go vet ./... 2>/dev/null && echo "pass" || echo "fail")
check "C2" "go vet ./... passes" "$result"

# C3: cors.go uses && not || in the guard (core fix)
result=$(python3 -c "
import re
src = open('cors.go').read()
# The fixed guard must use && — origin == \"\" && requestMethod == \"\"
# The buggy guard used ||
# Look for the skip pattern
if re.search(r'origin\s*==\s*\"\"\s*&&\s*requestMethod\s*==\s*\"\"', src):
    print('pass')
elif re.search(r'origin\s*==\s*\"\"\s*\|\|\s*requestMethod\s*==\s*\"\"', src):
    print('fail')
else:
    # Different variable names but same logic — check for || in guard
    if '||' in src and 'origin' in src:
        print('fail')
    else:
        print('pass')
" 2>/dev/null || echo "fail")
check "C3" "cors.go guard uses && (not ||)" "$result"

# C4: TestRealCORSRequestGetsHeaders passes
result=$(go test -v -run TestRealCORSRequestGetsHeaders -timeout 15s ./... 2>/dev/null && echo "pass" || echo "fail")
check "C4" "TestRealCORSRequestGetsHeaders passes" "$result"

# C5: TestNonCORSRequestNoHeaders passes
result=$(go test -v -run TestNonCORSRequestNoHeaders -timeout 15s ./... 2>/dev/null && echo "pass" || echo "fail")
check "C5" "TestNonCORSRequestNoHeaders passes" "$result"

# C6: all go tests pass
result=$(go test -timeout 30s ./... 2>/dev/null && echo "pass" || echo "fail")
check "C6" "go test ./... passes" "$result"

partial_score=$(python3 -c "print(round($partial / $total, 2))")
findings="${findings%,}"

mkdir -p "${REPORTS}"
cat > "${REPORTS}/score.json" <<EOF
{
  "pass": $( [ "$pass" = "true" ] && echo "true" || echo "false" ),
  "secondary": {
    "partial_score": $partial_score,
    "checks_passed": $partial,
    "checks_total": $total
  },
  "failure_modes": [],
  "checklist": [$findings]
}
EOF
