#!/usr/bin/env bash
# DIST1 grader: verify all 3 race conditions are fixed
set -uo pipefail

WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
REPORTS="${2:-${REPORTS_DIR:-/reports}}"

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
# C1: Syntax validity — queue.py and priority.py must parse
# -------------------------------------------------------------------
if python3 -c "
import ast, sys
for f in ['mqueue/queue.py', 'mqueue/priority.py', 'mqueue/consumer.py']:
    try:
        ast.parse(open(f).read())
    except SyntaxError as e:
        print(f'SyntaxError in {f}: {e}')
        sys.exit(1)
sys.exit(0)
" 2>/dev/null; then
    check "C1" "Syntax valid: queue.py, priority.py, consumer.py parse cleanly" "pass"
else
    check "C1" "Syntax error in one or more mqueue source files" "fail"
fi

# -------------------------------------------------------------------
# C2: Single-thread tests still pass (regression check)
# -------------------------------------------------------------------
if python3 -m pytest tests/test_single_thread.py -q --tb=short --timeout=30 2>/dev/null; then
    check "C2" "Single-thread tests still pass (no regression)" "pass"
else
    check "C2" "Single-thread tests broken (regression introduced)" "fail"
fi

# -------------------------------------------------------------------
# C3: Bug 1 — put() uses lock covering BOTH check AND append (static check)
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys

src = open('mqueue/queue.py').read()
tree = ast.parse(src)

for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == 'put':
        func_src = ast.unparse(node)
        # Must have a with-lock statement that covers both the capacity check
        # and the append/add operation
        has_with_lock = False
        for child in ast.walk(node):
            if isinstance(child, ast.With):
                with_src = ast.unparse(child)
                # The with block must contain both a comparison (capacity check)
                # and an append/add/put call
                has_check = ('>=' in with_src or 'len(' in with_src or
                             'size' in with_src or 'full' in with_src.lower())
                has_append = ('append' in with_src or 'put' in with_src or
                              'add' in with_src or 'push' in with_src)
                if has_check and has_append:
                    has_with_lock = True
                    break
        if has_with_lock:
            sys.exit(0)
        else:
            sys.exit(1)
sys.exit(1)
PYEOF
then
    check "C3" "Bug 1 fixed: put() lock covers both capacity check and append" "pass"
else
    check "C3" "Bug 1 not fixed: put() capacity check and append not atomic" "fail"
fi

# -------------------------------------------------------------------
# C4: test_capacity.py passes (capacity never exceeded under concurrent puts)
# -------------------------------------------------------------------
if python3 -m pytest tests/test_capacity.py -q --tb=short --timeout=60 2>/dev/null; then
    check "C4" "test_capacity.py passes: capacity never exceeded under concurrent puts" "pass"
else
    check "C4" "test_capacity.py failed: capacity exceeded under concurrent load" "fail"
fi

# -------------------------------------------------------------------
# C5: Bug 2 — acknowledgment pattern present (static check)
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys

src = open('mqueue/queue.py').read()
# Must have in_flight dict or similar staging area, AND ack method
has_inflight = ('in_flight' in src or 'in_transit' in src or
                'pending_ack' in src or 'unacked' in src or
                'staging' in src)
has_ack = 'def ack' in src
has_nack = 'def nack' in src or 'def requeue' in src or 'def reject' in src

if has_inflight and has_ack:
    sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C5" "Bug 2 fixed: acknowledgment pattern (in_flight + ack method) present" "pass"
else
    check "C5" "Bug 2 not fixed: no acknowledgment pattern found in queue.py" "fail"
fi

# -------------------------------------------------------------------
# C6: get() returns a receipt/token alongside the message
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys

src = open('mqueue/queue.py').read()
tree = ast.parse(src)

for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == 'get':
        for child in ast.walk(node):
            # Look for a return with a tuple (msg, receipt)
            if isinstance(child, ast.Return) and child.value is not None:
                if isinstance(child.value, ast.Tuple) and len(child.value.elts) >= 2:
                    sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C6" "get() returns (message, receipt) tuple" "pass"
else
    check "C6" "get() does not return a receipt — ack pattern incomplete" "fail"
fi

# -------------------------------------------------------------------
# C7: test_crash_recovery.py passes (unacked message re-queued)
# -------------------------------------------------------------------
if python3 -m pytest tests/test_crash_recovery.py -q --tb=short --timeout=60 2>/dev/null; then
    check "C7" "test_crash_recovery.py passes: unacked message re-queued on nack" "pass"
else
    check "C7" "test_crash_recovery.py failed: crash recovery not working" "fail"
fi

# -------------------------------------------------------------------
# C8: Bug 3 — priority comparator uses seq or compare=False (static check)
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys

src = open('mqueue/priority.py').read()
# Must use compare=False on message field OR have a seq/counter tie-breaker
has_compare_false = 'compare=False' in src
has_seq = ('seq' in src or 'counter' in src or 'sequence' in src or
           'tiebreak' in src or 'order' in src)
# The message field must not be the second field used in ordering
# i.e., it must either be excluded or come after a seq field
if has_compare_false or (has_seq and 'seq' in src):
    sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C8" "Bug 3 fixed: priority comparator uses type-safe tie-breaker" "pass"
else
    check "C8" "Bug 3 not fixed: priority comparator still type-unsafe" "fail"
fi

# -------------------------------------------------------------------
# C9: No TypeError from equal-priority messages with dict/list payloads
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import sys, importlib.util

spec = importlib.util.spec_from_file_location("priority", "mqueue/priority.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Find the PriorityMessage class (may have seed-variant name)
pm_cls = None
for name in dir(mod):
    obj = getattr(mod, name)
    if isinstance(obj, type) and 'priority' in name.lower() or 'message' in name.lower():
        pm_cls = obj
        break
if pm_cls is None:
    # fallback: try common names
    for name in ['PriorityMessage', 'PriorityItem', 'PriorityEvent', 'PriorityJob']:
        if hasattr(mod, name):
            pm_cls = getattr(mod, name)
            break

if pm_cls is None:
    sys.exit(1)

try:
    # Construct two equal-priority messages with dict payloads (would crash buggy version)
    # Try different constructor signatures
    try:
        a = pm_cls(priority=1, seq=0, message={"key": "val1"})
        b = pm_cls(priority=1, seq=1, message={"key": "val2"})
    except TypeError:
        try:
            a = pm_cls(1, 0, {"key": "val1"})
            b = pm_cls(1, 1, {"key": "val2"})
        except TypeError:
            a = pm_cls(priority=1, message={"key": "val1"})
            b = pm_cls(priority=1, message={"key": "val2"})
    result = a < b  # This crashes buggy code with TypeError
    sys.exit(0)
except TypeError:
    sys.exit(1)
PYEOF
then
    check "C9" "No TypeError from equal-priority messages with dict payloads" "pass"
else
    check "C9" "TypeError still raised when comparing equal-priority dict messages" "fail"
fi

# -------------------------------------------------------------------
# C10: test_ordering.py passes (priority ordering maintained)
# -------------------------------------------------------------------
if python3 -m pytest tests/test_ordering.py -q --tb=short --timeout=30 2>/dev/null; then
    check "C10" "test_ordering.py passes: priority ordering maintained" "pass"
else
    check "C10" "test_ordering.py failed: priority ordering broken" "fail"
fi

# -------------------------------------------------------------------
# C11: test_message_loss.py passes (zero-loss guarantee)
# -------------------------------------------------------------------
if python3 -m pytest tests/test_message_loss.py -q --tb=short --timeout=120 2>/dev/null; then
    check "C11" "test_message_loss.py passes: zero message loss confirmed" "pass"
else
    check "C11" "test_message_loss.py failed: messages being lost" "fail"
fi

# -------------------------------------------------------------------
# C12: test_concurrent.py passes (10K messages, 20 threads)
# -------------------------------------------------------------------
if python3 -m pytest tests/test_concurrent.py -q --tb=short --timeout=120 2>/dev/null; then
    check "C12" "test_concurrent.py passes: 10K messages across 20 threads" "pass"
else
    check "C12" "test_concurrent.py failed: concurrent correctness issues remain" "fail"
fi

# -------------------------------------------------------------------
# Scoring
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
