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

cd "$WORKSPACE"

# Load expected values from grader-only expected.json
EXPECTED="$REPORTS/expected.json"

# ── Check 1: SQL injection fixed (parameterized query) ──────────────────────
check "python3 -c \"
import json, re
with open('app.py') as f:
    code = f.read()
# Must NOT have an f-string building the SELECT query with user input
bad_patterns = re.findall(r'f[\\\"\\']SELECT.*WHERE.*=.*{', code)
assert len(bad_patterns) == 0, f'SQL f-string injection still present: {bad_patterns}'
# Must have a parameterized placeholder
assert '?' in code, 'No ? placeholder found — parameterized query missing'
# Must pass the parameter separately (tuple or list after query string)
assert re.search(r'conn\.execute\s*\(\s*[\\\"\\']SELECT', code) or \
       re.search(r'execute\s*\(\s*query\s*,', code), \
       'No evidence of parameterized execute call'
print('SQL_INJECTION_FIXED')
\"" "sql_injection_not_fixed"

# ── Check 2: N+1 query eliminated (batch SELECT with IN clause) ─────────────
check "python3 -c \"
import re
with open('app.py') as f:
    code = f.read()
# Must NOT have a for-loop that executes one SELECT per iteration
loop_queries = re.findall(r'for\s+\w+\s+in\s+ids.*?\.execute\s*\(', code, re.DOTALL)
assert len(loop_queries) == 0, 'N+1 loop-per-query pattern still present'
# Must use IN clause
assert ' IN ' in code.upper() or 'IN (' in code.upper(), 'No IN clause found for batch query'
print('N_PLUS_ONE_FIXED')
\"" "n_plus_one_not_fixed"

# ── Check 3: Function renamed correctly ─────────────────────────────────────
check "python3 -c \"
import json
with open('$EXPECTED') as f:
    exp = json.load(f)
good = exp['good_func_name']
bad  = exp['bad_func_name']
with open('app.py') as f:
    code = f.read()
import re
# Good name must be defined as a top-level function
assert re.search(r'^def ' + re.escape(good) + r'\s*\(', code, re.MULTILINE), \
    f'Renamed function {good!r} not found in app.py'
# Bad name must NOT appear as a function definition any more
assert not re.search(r'^def ' + re.escape(bad) + r'\s*\(', code, re.MULTILINE), \
    f'Old function name {bad!r} still defined in app.py'
print('FUNCTION_RENAMED')
\"" "function_not_renamed"

# ── Check 4: Bare except replaced with specific exceptions ──────────────────
check "python3 -c \"
import re
with open('app.py') as f:
    code = f.read()
# No bare 'except:' allowed
bare = re.findall(r'^\s*except\s*:', code, re.MULTILINE)
assert len(bare) == 0, f'Bare except still present ({len(bare)} occurrence(s))'
# Must have a specific exception clause in the validate function
# (the except in the bad-func body uses 'Exception as e' which is acceptable)
# Just verify no bare except remains anywhere
print('BARE_EXCEPT_FIXED')
\"" "bare_except_not_fixed"

# ── Check 5: Existing tests still pass ──────────────────────────────────────
check "python3 -m pytest tests/test_app.py -q --tb=short 2>&1 | tail -5 | grep -E '^[0-9]+ passed'" "tests_failing"

# ── Check 6: No excessive changes (only the 4 review items addressed) ────────
check "python3 -c \"
import ast, os
# app.py must still be syntactically valid Python
with open('app.py') as f:
    src = f.read()
tree = ast.parse(src)
# Count top-level function definitions — should still have the same 6 (renamed, not added)
funcs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and
         isinstance(getattr(n, 'col_offset', 1), int) and n.col_offset == 0]
assert len(funcs) == 6, f'Expected 6 top-level functions, got {len(funcs)}: {funcs}'
print('SCOPE_OK')
\"" "excessive_changes"

# ── Check 7: app.py is syntactically valid ───────────────────────────────────
check "python3 -c \"
import py_compile
py_compile.compile('app.py', doraise=True)
print('SYNTAX_OK')
\"" "syntax_error"

# ── Check 8: Attestation ─────────────────────────────────────────────────────
# ── Attestation recorded as METADATA, never scored ───────────────────────
# de-scored-by: scripts/repair_graders.py (R3 attestation-is-protocol)
# attestation.json is a PROTOCOL property of the run (already enforced as a
# hard gate in harness/grade_task.py), not a property of the submitted
# artifact. Scoring it let an agent buy partial credit by writing one JSON
# file, which is the confound behind the withdrawn "removing the Verifier
# improves partial score" result. Recorded here, excluded from partial_score.
echo "metadata: attestation_present=$([ -f "${SUBMISSION:-}/attestation.json" ] && echo yes || echo no)"

PARTIAL=$(python3 -c "print(round($PASSED/max(1,$CHECKS), 2))")
if [ "$PASSED" -eq "$CHECKS" ]; then SUCCESS=1; PASS=true; else SUCCESS=0; PASS=false; fi
FM=$(python3 -c "import json; print(json.dumps([x for x in '${FAILURES}'.split(',') if x]))")

cat > "$REPORTS/score.json" <<JSON
{
  "pass": $PASS,
  "primary": {"success": $SUCCESS},
  "secondary": {"checks_passed": $PASSED, "checks_total": $CHECKS, "partial_score": $PARTIAL},
  "failure_modes": $FM
}
JSON
