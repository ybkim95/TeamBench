#!/usr/bin/env bash
# GH15_gin_context_key grader
set -uo pipefail

WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
REPORTS="${2:-${REPORTS_DIR:-/reports}}"
SUBMISSION="${3:-/submission}"
TASK_DIR="${4:-/task}"

source /usr/local/lib/venv/bin/activate 2>/dev/null || true

pass=true
partial=0
total=5
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

# C3: middleware uses typed context key (not bare string literal)
result=$(python3 -c "
src = open('middleware.go').read()
# After fix: middleware should use a typed key variable, not string literal
# Check that 'context.WithValue' call uses a non-string-literal key
import re
# Look for context.WithValue with a string literal as key (the bug)
# Pattern: context.WithValue(..., \"somekey\", ...)
bug_pattern = r'context\.WithValue\([^,]+,\s*\"[^\"]+\",'
if re.search(bug_pattern, src):
    print('fail')
else:
    print('pass')
" 2>/dev/null || echo "fail")
check "C3" "middleware uses typed context key (not bare string)" "$result"

# C4: TestContextValuePropagated passes
result=$(go test -v -run TestContextValuePropagated -timeout 15s ./... 2>/dev/null && echo "pass" || echo "fail")
check "C4" "TestContextValuePropagated passes" "$result"

# C5: all go tests pass
result=$(go test -timeout 30s ./... 2>/dev/null && echo "pass" || echo "fail")
check "C5" "go test ./... passes" "$result"

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
