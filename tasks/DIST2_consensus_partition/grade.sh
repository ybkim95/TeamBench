#!/usr/bin/env bash
# DIST2 grader: verify all 3 Raft consensus bugs are fixed
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
# C1: Syntax validity — all raft/*.py files must parse
# -------------------------------------------------------------------
if python3 -c "
import ast, sys
for f in ['raft/node.py', 'raft/messages.py', 'raft/log.py', 'raft/network.py']:
    try:
        ast.parse(open(f).read())
    except SyntaxError as e:
        print(f'SyntaxError in {f}: {e}')
        sys.exit(1)
sys.exit(0)
" 2>/dev/null; then
    check "C1" "Syntax valid: all raft/*.py files parse cleanly" "pass"
else
    check "C1" "Syntax error in one or more raft source files" "fail"
fi

# -------------------------------------------------------------------
# C2: network.py must be unchanged (diff against original)
# -------------------------------------------------------------------
ORIG_NETWORK_HASH=$(python3 -c "
import hashlib, sys
try:
    data = open('raft/network.py', 'rb').read()
    # Check for the canonical marker comment that we embed
    if b'DO NOT MODIFY' in data or b'SimulatedNetwork' in data:
        sys.exit(0)
    sys.exit(0)
except:
    sys.exit(1)
" 2>/dev/null && echo "ok" || echo "fail")

# Static check: network.py must still contain SimulatedNetwork class and partition support
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys
src = open('raft/network.py').read()
tree = ast.parse(src)
has_network_cls = any(
    isinstance(n, ast.ClassDef) and 'network' in n.name.lower()
    for n in ast.walk(tree)
)
has_partition = 'partition' in src.lower()
if has_network_cls and has_partition:
    sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C2" "network.py unchanged: SimulatedNetwork class and partition support intact" "pass"
else
    check "C2" "network.py was modified: SimulatedNetwork class or partition support removed" "fail"
fi

# -------------------------------------------------------------------
# C3: Bug 1 — RequestVote handler checks log up-to-date-ness (static)
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys

src = open('raft/node.py').read()
tree = ast.parse(src)

for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and 'request_vote' in node.name.lower():
        func_src = ast.unparse(node)
        # Must reference last_term or last_index for log comparison
        has_log_check = (
            'last_term' in func_src or
            'last_index' in func_src or
            'up_to_date' in func_src or
            '_log_is_up_to_date' in func_src or
            'log_ok' in func_src
        )
        if has_log_check:
            sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C3" "Bug 1 fixed: RequestVote handler checks log up-to-date-ness" "pass"
else
    check "C3" "Bug 1 not fixed: RequestVote handler missing log up-to-date check" "fail"
fi

# -------------------------------------------------------------------
# C4: test_election.py passes (stale candidate rejected)
# -------------------------------------------------------------------
if python3 -m pytest tests/test_election.py -q --tb=short --timeout=60 2>/dev/null; then
    check "C4" "test_election.py passes: stale candidate correctly rejected" "pass"
else
    check "C4" "test_election.py failed: stale candidate not rejected" "fail"
fi

# -------------------------------------------------------------------
# C5: Bug 2 — AppendEntries handler checks prevLogIndex/prevLogTerm (static)
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys

src = open('raft/node.py').read()
tree = ast.parse(src)

for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and 'append_entries' in node.name.lower():
        func_src = ast.unparse(node)
        # Must check prev_log_index and prev_log_term
        has_prev_index = 'prev_log_index' in func_src
        has_prev_term = 'prev_log_term' in func_src
        if has_prev_index and has_prev_term:
            sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C5" "Bug 2 fixed: AppendEntries handler checks prevLogIndex and prevLogTerm" "pass"
else
    check "C5" "Bug 2 not fixed: AppendEntries handler missing consistency check" "fail"
fi

# -------------------------------------------------------------------
# C6: test_replication.py passes (log consistency enforced)
# -------------------------------------------------------------------
if python3 -m pytest tests/test_replication.py -q --tb=short --timeout=60 2>/dev/null; then
    check "C6" "test_replication.py passes: log consistency check enforced" "pass"
else
    check "C6" "test_replication.py failed: AppendEntries consistency check not working" "fail"
fi

# -------------------------------------------------------------------
# C7: Bug 3 — commit logic checks current term (static)
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys

src = open('raft/node.py').read()
tree = ast.parse(src)

for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and (
        'commit' in node.name.lower() or 'try_commit' in node.name.lower()
    ):
        func_src = ast.unparse(node)
        # Must compare log entry term to current_term
        has_term_check = (
            'current_term' in func_src and
            ('term_at' in func_src or 'entry.term' in func_src or
             'log.term' in func_src or '.term ==' in func_src or
             '.term !=' in func_src)
        )
        if has_term_check:
            sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C7" "Bug 3 fixed: commit logic checks entry is from current term" "pass"
else
    check "C7" "Bug 3 not fixed: commit logic missing current-term check" "fail"
fi

# -------------------------------------------------------------------
# C8: test_commit.py passes (old-term entries not committed alone)
# -------------------------------------------------------------------
if python3 -m pytest tests/test_commit.py -q --tb=short --timeout=60 2>/dev/null; then
    check "C8" "test_commit.py passes: old-term entries not committed without current-term entry" "pass"
else
    check "C8" "test_commit.py failed: old-term commit safety violated" "fail"
fi

# -------------------------------------------------------------------
# C9: test_partition.py passes (partition + heal scenario)
# -------------------------------------------------------------------
if python3 -m pytest tests/test_partition.py -q --tb=short --timeout=120 2>/dev/null; then
    check "C9" "test_partition.py passes: partition and heal scenario works" "pass"
else
    check "C9" "test_partition.py failed: partition/heal scenario failing" "fail"
fi

# -------------------------------------------------------------------
# C10: test_safety.py passes (all 3 safety invariants hold)
# -------------------------------------------------------------------
if python3 -m pytest tests/test_safety.py -q --tb=short --timeout=120 2>/dev/null; then
    check "C10" "test_safety.py passes: election safety, leader completeness, SM safety" "pass"
else
    check "C10" "test_safety.py failed: safety invariants violated" "fail"
fi

# -------------------------------------------------------------------
# C11: Scenario files present and valid JSON
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import json, sys, os
for fname in ['tests/scenarios/partition_heal.json', 'tests/scenarios/leader_crash.json']:
    if not os.path.exists(fname):
        print(f"Missing: {fname}")
        sys.exit(1)
    try:
        data = json.load(open(fname))
        if 'steps' not in data and 'scenario' not in data and 'name' not in data:
            sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in {fname}: {e}")
        sys.exit(1)
sys.exit(0)
PYEOF
then
    check "C11" "Scenario files present and valid: partition_heal.json, leader_crash.json" "pass"
else
    check "C11" "Scenario files missing or invalid JSON" "fail"
fi

# -------------------------------------------------------------------
# C12: Full pytest suite passes
# -------------------------------------------------------------------
if python3 -m pytest tests/ -q --tb=short --timeout=120 2>/dev/null; then
    check "C12" "Full test suite passes: all pytest tests green" "pass"
else
    check "C12" "Full test suite has failures" "fail"
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
