#!/usr/bin/env bash
# DIST4 grader: verify Lamport clock bugs fixed and vector clock unchanged
set -uo pipefail

WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
REPORTS="${2:-${REPORTS_DIR:-/reports}}"
SUBMISSION="${3:-/submission}"
TASK_DIR="${4:-/task}"

cd "$WORKSPACE"

pass=true
partial=0
total=12
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

# Install pytest if needed
# was: pip install (grade-time network fetch), replaced scripts/make_graders_hermetic.py
tb_require pytest || true

# -------------------------------------------------------------------
# C1: All pytest tests pass
# -------------------------------------------------------------------
if python -m pytest tests/ -q --tb=no 2>/dev/null; then
    check "C1" "All pytest tests pass" "pass"
else
    check "C1" "Some pytest tests failed" "fail"
fi

# -------------------------------------------------------------------
# C2: test_lamport.py passes (send before increment)
# -------------------------------------------------------------------
if python -m pytest tests/test_lamport.py -q --tb=no 2>/dev/null; then
    check "C2" "test_lamport.py passes (send rule verified)" "pass"
else
    check "C2" "test_lamport.py failed (send before increment not fixed)" "fail"
fi

# -------------------------------------------------------------------
# C3: test_ordering.py passes (consistent ordering across replicas)
# -------------------------------------------------------------------
if python -m pytest tests/test_ordering.py -q --tb=no 2>/dev/null; then
    check "C3" "test_ordering.py passes (tie-breaking verified)" "pass"
else
    check "C3" "test_ordering.py failed (tie-breaking not fixed)" "fail"
fi

# -------------------------------------------------------------------
# C4: test_causal.py passes (causal events ordered correctly)
# -------------------------------------------------------------------
if python -m pytest tests/test_causal.py -q --tb=no 2>/dev/null; then
    check "C4" "test_causal.py passes (causal ordering correct)" "pass"
else
    check "C4" "test_causal.py failed (causal ordering broken)" "fail"
fi

# -------------------------------------------------------------------
# C5: test_consistency.py passes (all replicas see same final order)
# -------------------------------------------------------------------
if python -m pytest tests/test_consistency.py -q --tb=no 2>/dev/null; then
    check "C5" "test_consistency.py passes (replica consistency verified)" "pass"
else
    check "C5" "test_consistency.py failed (replicas disagree on order)" "fail"
fi

# -------------------------------------------------------------------
# C6: test_vector.py passes (vector clock unchanged and correct)
# -------------------------------------------------------------------
if python -m pytest tests/test_vector.py -q --tb=no 2>/dev/null; then
    check "C6" "test_vector.py passes (vector clock untouched and correct)" "pass"
else
    check "C6" "test_vector.py failed (vector clock was incorrectly modified)" "fail"
fi

# -------------------------------------------------------------------
# C7: Static: send_event uses self.clock as timestamp (not a saved pre-increment variable)
# The correct fix: self.clock += 1 then Event(timestamp=self.clock, ...)
# The bug: timestamp = self.clock; self.clock += 1; Event(timestamp=timestamp, ...)
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys

src = open('eventlog/lamport.py').read()
tree = ast.parse(src)

for node in ast.walk(tree):
    if not (isinstance(node, ast.FunctionDef) and node.name == 'send_event'):
        continue

    # Find all local variable assignments in send_event
    # If a variable is assigned `self.clock` BEFORE increment, and that variable
    # is used as the timestamp argument to Event(), it's the bug.
    pre_increment_vars = set()  # vars assigned self.clock value before +1
    saw_increment = False

    for stmt in ast.walk(ast.Module(body=node.body, type_ignores=[])):
        if not isinstance(stmt, ast.Assign):
            continue
        val_src = ast.unparse(stmt.value)
        tgt_src = ast.unparse(stmt.targets[0]) if stmt.targets else ''
        if 'self.clock' in val_src and not saw_increment:
            # e.g.  timestamp = self.clock  (pre-increment capture)
            pre_increment_vars.add(tgt_src)
        if 'self.clock' in tgt_src and ('+= 1' in ast.unparse(stmt) or
                                          (isinstance(stmt.value, ast.BinOp) and
                                           ast.unparse(stmt.value).endswith('+ 1'))):
            saw_increment = True

    # Check if Event() is called with timestamp= one of the pre-increment vars
    for call_node in ast.walk(ast.Module(body=node.body, type_ignores=[])):
        if not isinstance(call_node, ast.Call):
            continue
        func_name = ast.unparse(call_node.func)
        if 'Event' not in func_name:
            continue
        for kw in call_node.keywords:
            if kw.arg == 'timestamp':
                ts_val = ast.unparse(kw.value)
                if ts_val in pre_increment_vars:
                    # Bug present: timestamp is a pre-increment saved variable
                    sys.exit(1)
                if 'self.clock' in ts_val:
                    # Correct: uses self.clock directly (after increment)
                    sys.exit(0)
        # Also check positional args: Event(timestamp, node_id, ...)
        if call_node.args:
            ts_val = ast.unparse(call_node.args[0])
            if ts_val in pre_increment_vars:
                sys.exit(1)
            if 'self.clock' in ts_val:
                sys.exit(0)

    sys.exit(1)

sys.exit(1)
PYEOF
then
    check "C7" "Static: send_event increments clock before attaching timestamp" "pass"
else
    check "C7" "Static: send_event still uses pre-increment value for timestamp" "fail"
fi

# -------------------------------------------------------------------
# C8: Static: receive_event has max(...) + 1 (AST check — immune to comments)
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys
src = open('eventlog/lamport.py').read()
tree = ast.parse(src)
for node in ast.walk(tree):
    if not (isinstance(node, ast.FunctionDef) and node.name == 'receive_event'):
        continue
    # Look for AST pattern: BinOp(left=Call(func=max,...), op=Add, right=Constant(1))
    # i.e. max(...) + 1
    for child in ast.walk(node):
        if not isinstance(child, ast.BinOp):
            continue
        if not isinstance(child.op, ast.Add):
            continue
        if not isinstance(child.right, ast.Constant):
            continue
        if child.right.value != 1:
            continue
        # left must be a call to max()
        left = child.left
        if isinstance(left, ast.Call) and ast.unparse(left.func) == 'max':
            sys.exit(0)
    sys.exit(1)
sys.exit(1)
PYEOF
then
    check "C8" "Static: receive_event uses max(local, received) + 1" "pass"
else
    check "C8" "Static: receive_event missing +1 after max (Lamport rule violated)" "fail"
fi

# -------------------------------------------------------------------
# C9: Static: ordering comparator has node_id tie-breaking
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys
src = open('eventlog/ordering.py').read()
tree = ast.parse(src)
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == 'compare':
        func_src = ast.unparse(node)
        has_node_id = 'node_id' in func_src
        # Must reference node_id in comparison context
        if has_node_id:
            sys.exit(0)
        sys.exit(1)
sys.exit(1)
PYEOF
then
    check "C9" "Static: ordering comparator has node_id tie-breaking logic" "pass"
else
    check "C9" "Static: ordering comparator missing node_id tie-breaking" "fail"
fi

# -------------------------------------------------------------------
# C10: vector_clock.py unchanged (content must match original hash)
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import hashlib, sys
src = open('eventlog/vector_clock.py').read()
# Check that key structural elements are present and unmodified
checks = [
    'class VectorClock',
    'def increment',
    'def update',
    'def happens_before',
    'def concurrent',
    'defaultdict',
    'self.clock[self.node_id] += 1',
]
for c in checks:
    if c not in src:
        sys.exit(1)
# Verify the happens_before logic uses all() and any() (correct impl)
if 'all(' in src and 'any(' in src:
    sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C10" "vector_clock.py content intact (VectorClock not modified)" "pass"
else
    check "C10" "vector_clock.py was modified (must not change correct VectorClock)" "fail"
fi

# -------------------------------------------------------------------
# C11: Syntax validity of all eventlog modules
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys, os
modules = [
    'eventlog/lamport.py',
    'eventlog/ordering.py',
    'eventlog/vector_clock.py',
    'eventlog/event.py',
    'eventlog/node.py',
    'eventlog/network.py',
]
for m in modules:
    if os.path.exists(m):
        try:
            ast.parse(open(m).read())
        except SyntaxError as e:
            print(f"Syntax error in {m}: {e}", file=sys.stderr)
            sys.exit(1)
sys.exit(0)
PYEOF
then
    check "C11" "All eventlog modules have valid Python syntax" "pass"
else
    check "C11" "Syntax error in one or more eventlog modules" "fail"
fi

# -------------------------------------------------------------------
# C12: Concurrent events from 3 nodes produce identical ordering on all nodes
# (functional simulation — send+receive through simulated network)
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import sys, os
sys.path.insert(0, '.')
from functools import cmp_to_key

try:
    from eventlog.lamport import LamportClock
    from eventlog.event import Event
    from eventlog.ordering import EventOrderer

    # Simulate 3 nodes independently sending events, then all replicas sort
    nodes = ["alpha", "beta", "gamma"]
    clocks = {n: LamportClock(n) for n in nodes}
    all_events = []

    # alpha sends 2 events
    e1 = clocks["alpha"].send_event("write", {"k": "x"})
    all_events.append(e1)
    # gamma sends event
    e2 = clocks["gamma"].send_event("write", {"k": "z"})
    all_events.append(e2)
    # beta receives e1 from alpha and sends its own
    clocks["beta"].receive_event(e1)
    e3 = clocks["beta"].send_event("write", {"k": "y"})
    all_events.append(e3)
    # alpha sends another event
    e4 = clocks["alpha"].send_event("read", {"k": "x"})
    all_events.append(e4)
    # gamma receives e3
    clocks["gamma"].receive_event(e3)
    e5 = clocks["gamma"].send_event("read", {"k": "z"})
    all_events.append(e5)

    orderer = EventOrderer()

    # Replica 1: sort in original order
    replica1 = sorted(all_events, key=cmp_to_key(orderer.compare))
    # Replica 2: sort in reversed order (simulates different arrival)
    replica2 = sorted(reversed(all_events), key=cmp_to_key(orderer.compare))
    # Replica 3: sort in shuffled order
    shuffled = all_events[2:] + all_events[:2]
    replica3 = sorted(shuffled, key=cmp_to_key(orderer.compare))

    ids1 = [(e.timestamp, e.node_id) for e in replica1]
    ids2 = [(e.timestamp, e.node_id) for e in replica2]
    ids3 = [(e.timestamp, e.node_id) for e in replica3]

    if ids1 == ids2 == ids3:
        sys.exit(0)
    else:
        print(f"Replicas disagree: {ids1} vs {ids2} vs {ids3}", file=sys.stderr)
        sys.exit(1)
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
PYEOF
then
    check "C12" "Concurrent events from 3 nodes produce identical ordering on all replicas" "pass"
else
    check "C12" "Replicas produce inconsistent ordering for concurrent events" "fail"
fi

# -------------------------------------------------------------------
# Compute final score
# -------------------------------------------------------------------
partial_score=$(awk "BEGIN {printf \"%.4f\", $partial / $total}")
findings="${findings%,}"  # Remove trailing comma

cat > "${REPORTS}/score.json" <<EOF
{
  "pass": $( [ "$pass" = "true" ] && echo "true" || echo "false" ),
  "secondary": {
    "partial_score": $partial_score,
    "checks_passed": $partial,
    "total_checks": $total
  },
  "failure_modes": [],
  "checklist": [$findings]
}
EOF

# hermetic-by: scripts/make_graders_hermetic.py
