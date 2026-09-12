#!/usr/bin/env bash
# DIST3 grader: verify idempotency implemented for 4 operations, balance untouched
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
# C1: Full pytest suite passes
# -------------------------------------------------------------------
if python -m pytest tests/ -q --tb=no 2>/dev/null; then
    check "C1" "All tests pass: pytest tests/" "pass"
else
    check "C1" "pytest tests/ failed" "fail"
fi

# -------------------------------------------------------------------
# C2: test_charges.py passes (double-charge retry test)
# -------------------------------------------------------------------
if python -m pytest tests/test_charges.py -q --tb=no 2>/dev/null; then
    check "C2" "test_charges.py passed (charge idempotency correct)" "pass"
else
    check "C2" "test_charges.py failed (double-charge on retry)" "fail"
fi

# -------------------------------------------------------------------
# C3: test_refunds.py passes (double-refund retry test)
# -------------------------------------------------------------------
if python -m pytest tests/test_refunds.py -q --tb=no 2>/dev/null; then
    check "C3" "test_refunds.py passed (refund idempotency correct)" "pass"
else
    check "C3" "test_refunds.py failed (double-refund on retry)" "fail"
fi

# -------------------------------------------------------------------
# C4: test_webhooks.py passes (webhook sent exactly once)
# -------------------------------------------------------------------
if python -m pytest tests/test_webhooks.py -q --tb=no 2>/dev/null; then
    check "C4" "test_webhooks.py passed (webhook delivered exactly once)" "pass"
else
    check "C4" "test_webhooks.py failed (webhook sent multiple times)" "fail"
fi

# -------------------------------------------------------------------
# C5: test_ledger.py passes (ledger entry created once)
# -------------------------------------------------------------------
if python -m pytest tests/test_ledger.py -q --tb=no 2>/dev/null; then
    check "C5" "test_ledger.py passed (ledger entry deduplicated)" "pass"
else
    check "C5" "test_ledger.py failed (duplicate ledger entries)" "fail"
fi

# -------------------------------------------------------------------
# C6: test_balance.py passes (balance endpoint unchanged)
# -------------------------------------------------------------------
if python -m pytest tests/test_balance.py -q --tb=no 2>/dev/null; then
    check "C6" "test_balance.py passed (balance endpoint still works)" "pass"
else
    check "C6" "test_balance.py failed (balance endpoint broken)" "fail"
fi

# -------------------------------------------------------------------
# C7: payments/balance.py has NO idempotency_key parameter (no overfix)
# Trap check: the balance endpoint must NOT be modified
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys
src = open('payments/balance.py').read()
tree = ast.parse(src)
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == 'get_balance':
        param_names = [a.arg for a in node.args.args]
        if 'idempotency_key' in param_names:
            sys.exit(1)  # overfix: added idempotency_key to balance
        sys.exit(0)
sys.exit(1)  # function not found
PYEOF
then
    check "C7" "payments/balance.py not modified (no idempotency_key added to get_balance)" "pass"
else
    check "C7" "payments/balance.py incorrectly modified (idempotency_key added to get_balance)" "fail"
fi

# -------------------------------------------------------------------
# C8: payments/idempotency.py is implemented (not just a stub)
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys
src = open('payments/idempotency.py').read()
tree = ast.parse(src)
# Must have at least one class or function definition
has_def = any(isinstance(n, (ast.ClassDef, ast.FunctionDef)) for n in ast.walk(tree))
if not has_def:
    sys.exit(1)
# Must have actual logic (more than just a comment/docstring)
# Count non-trivial statements (assignments, function bodies with >1 stmt)
non_trivial = [n for n in ast.walk(tree) if isinstance(n, (ast.Assign, ast.Return, ast.If, ast.With))]
if len(non_trivial) < 2:
    sys.exit(1)
sys.exit(0)
PYEOF
then
    check "C8" "payments/idempotency.py is implemented (not empty stub)" "pass"
else
    check "C8" "payments/idempotency.py is still an empty stub" "fail"
fi

# -------------------------------------------------------------------
# C9: test_concurrent.py passes (concurrent retries handled safely)
# -------------------------------------------------------------------
if python -m pytest tests/test_concurrent.py -q --tb=no 2>/dev/null; then
    check "C9" "test_concurrent.py passed (concurrent retries handled)" "pass"
else
    check "C9" "test_concurrent.py failed (race condition in concurrent retries)" "fail"
fi

# -------------------------------------------------------------------
# C10: test_idempotency.py passes (store isolation tests)
# -------------------------------------------------------------------
if python -m pytest tests/test_idempotency.py -q --tb=no 2>/dev/null; then
    check "C10" "test_idempotency.py passed (idempotency store unit tests)" "pass"
else
    check "C10" "test_idempotency.py failed (store isolation broken)" "fail"
fi

# -------------------------------------------------------------------
# C11: Syntax validity — all payment modules parse cleanly
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys
modules = [
    'payments/charges.py',
    'payments/refunds.py',
    'payments/webhooks.py',
    'payments/ledger.py',
    'payments/balance.py',
    'payments/idempotency.py',
]
for path in modules:
    try:
        ast.parse(open(path).read())
    except SyntaxError as e:
        print(f"SyntaxError in {path}: {e}", file=sys.stderr)
        sys.exit(1)
sys.exit(0)
PYEOF
then
    check "C11" "All payment modules have valid syntax" "pass"
else
    check "C11" "Syntax error in one or more payment modules" "fail"
fi

# -------------------------------------------------------------------
# C12: Static check — idempotency imported in all 4 non-idempotent modules
# (checks that idempotency.py is actually wired in, not just implemented)
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys

def imports_idempotency(path):
    src = open(path).read()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if 'idempotency' in alias.name:
                    return True
        if isinstance(node, ast.ImportFrom):
            if node.module and 'idempotency' in node.module:
                return True
    return False

modules = [
    'payments/charges.py',
    'payments/refunds.py',
    'payments/webhooks.py',
    'payments/ledger.py',
]
missing = [m for m in modules if not imports_idempotency(m)]
if missing:
    print(f"Missing idempotency import in: {missing}", file=sys.stderr)
    sys.exit(1)
sys.exit(0)
PYEOF
then
    check "C12" "idempotency.py imported in all 4 non-idempotent modules" "pass"
else
    check "C12" "idempotency.py not imported in one or more modules (not wired in)" "fail"
fi

# -------------------------------------------------------------------
# Final score
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
