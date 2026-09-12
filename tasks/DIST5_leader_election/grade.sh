#!/usr/bin/env bash
# DIST5 grader: verify 3 bugs fixed + 2 partition edge cases handled
set -uo pipefail

WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
REPORTS="${2:-${REPORTS_DIR:-/reports}}"
SUBMISSION="${3:-/submission}"
TASK_DIR="${4:-/task}"

source /usr/local/lib/venv/bin/activate 2>/dev/null || true

pass=true
partial=0
total=10
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

# Install dependencies if needed
# was: pip install (grade-time network fetch), replaced scripts/make_graders_hermetic.py
tb_require pytest || true

# -------------------------------------------------------------------
# C1: All Python files parse without SyntaxError
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys, glob
for f in glob.glob('**/*.py', recursive=True):
    try:
        ast.parse(open(f).read())
    except SyntaxError as e:
        print(f'SyntaxError in {f}: {e}', file=sys.stderr)
        sys.exit(1)
sys.exit(0)
PYEOF
then
    check "C1" "All Python files have valid syntax" "pass"
else
    check "C1" "Syntax error in one or more Python files" "fail"
fi

# -------------------------------------------------------------------
# C2: Single-node / happy-path tests still pass (regression check)
# -------------------------------------------------------------------
if python3 -m pytest tests/test_basic.py -q --tb=short --timeout=30 2>/dev/null; then
    check "C2" "Basic leader election tests pass (no regression)" "pass"
else
    check "C2" "Basic leader election tests broken (regression)" "fail"
fi

# -------------------------------------------------------------------
# C3: Bug 1 — simultaneous election handling (static check)
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys

src = open('cluster/election.py').read()
# Must handle ELECTION message from lower-ID node during own election
# Look for handling of concurrent election / ALIVE response
has_alive_response = 'ALIVE' in src or 'alive' in src
has_election_handler = ('handle_election' in src or 'on_election' in src or
                        'receive_election' in src or 'ELECTION' in src)
has_concurrent_check = ('election_in_progress' in src or 'is_electing' in src or
                        '_electing' in src or 'election_active' in src or
                        'running_election' in src)
if has_alive_response and has_election_handler and has_concurrent_check:
    sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C3" "Bug 1 fixed: simultaneous election handling present" "pass"
else
    check "C3" "Bug 1 not fixed: no concurrent election handling" "fail"
fi

# -------------------------------------------------------------------
# C4: Bug 2 — timeout check uses (current_time - last_heartbeat)
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys, re

src = open('cluster/election.py').read()
# Must have correct timeout: current_time - last_heartbeat > timeout
# NOT the buggy: last_heartbeat > timeout
has_correct = bool(re.search(
    r'(time\.time\(\)|current_time|now|monotonic)\s*-\s*(last_heartbeat|_last_seen|heartbeat_time)',
    src
))
has_buggy = bool(re.search(
    r'(last_heartbeat|_last_seen|heartbeat_time)\s*>\s*(timeout|TIMEOUT|self\._timeout)',
    src
))
# Also check the opposite subtraction direction is not used incorrectly
if has_correct and not has_buggy:
    sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C4" "Bug 2 fixed: timeout check uses (current_time - last_heartbeat)" "pass"
else
    check "C4" "Bug 2 not fixed: heartbeat timeout check still inverted" "fail"
fi

# -------------------------------------------------------------------
# C5: Bug 3 — new node join triggers election
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys

src = open('cluster/election.py').read()
# Must have election trigger in join/add_node method
has_join = 'join' in src or 'add_node' in src or 'node_joined' in src
has_election_on_join = False

tree = ast.parse(src)
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and ('join' in node.name or 'add_node' in node.name):
        func_src = ast.unparse(node)
        if 'election' in func_src.lower() or 'start_election' in func_src:
            has_election_on_join = True
            break

if has_join and has_election_on_join:
    sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C5" "Bug 3 fixed: new node join triggers re-election" "pass"
else
    check "C5" "Bug 3 not fixed: new node join does not trigger election" "fail"
fi

# -------------------------------------------------------------------
# C6: test_simultaneous_election.py passes
# -------------------------------------------------------------------
if python3 -m pytest tests/test_simultaneous_election.py -q --tb=short --timeout=30 2>/dev/null; then
    check "C6" "Simultaneous election test passes" "pass"
else
    check "C6" "Simultaneous election test failed" "fail"
fi

# -------------------------------------------------------------------
# C7: test_heartbeat.py passes (timeout detection works)
# -------------------------------------------------------------------
if python3 -m pytest tests/test_heartbeat.py -q --tb=short --timeout=30 2>/dev/null; then
    check "C7" "Heartbeat timeout detection test passes" "pass"
else
    check "C7" "Heartbeat timeout detection test failed" "fail"
fi

# -------------------------------------------------------------------
# C8: test_node_join.py passes (new high-ID node triggers election)
# -------------------------------------------------------------------
if python3 -m pytest tests/test_node_join.py -q --tb=short --timeout=30 2>/dev/null; then
    check "C8" "Node join election test passes" "pass"
else
    check "C8" "Node join election test failed" "fail"
fi

# -------------------------------------------------------------------
# C9: test_partition.py passes (split brain + partition heal)
# -------------------------------------------------------------------
if python3 -m pytest tests/test_partition.py -q --tb=short --timeout=60 2>/dev/null; then
    check "C9" "Network partition tests pass" "pass"
else
    check "C9" "Network partition tests failed" "fail"
fi

# -------------------------------------------------------------------
# C10: All tests pass together
# -------------------------------------------------------------------
if python3 -m pytest tests/ -q --tb=short --timeout=120 2>&1 | tail -5 | grep -qE "passed|no tests"; then
    check "C10" "All tests pass together" "pass"
else
    check "C10" "Some tests fail when run together" "fail"
fi

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

# hermetic-by: scripts/make_graders_hermetic.py
