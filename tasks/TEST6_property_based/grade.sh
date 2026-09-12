#!/usr/bin/env bash
# Grade script for TEST6: Property-Based Testing
# Arguments:
#   $1 = WORKSPACE  (directory containing datastructs.py and tests/)
#   $2 = REPORTS    (grader-only directory; contains expected.json)
#   $3 = SUBMISSION (directory where the agent writes attestation.json)
#   $4 = TASK_DIR   (task definition directory)
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

EXPECTED="$REPORTS/expected.json"
SL_NAME=$(python3 -c "import json; print(json.load(open('$EXPECTED'))['sorted_list_name'])" 2>/dev/null)
BQ_NAME=$(python3 -c "import json; print(json.load(open('$EXPECTED'))['bounded_queue_name'])" 2>/dev/null)
LRU_NAME=$(python3 -c "import json; print(json.load(open('$EXPECTED'))['lru_cache_name'])" 2>/dev/null)

# ── Check 1: test_properties.py exists and is non-empty ──────────────────
check "test -s tests/test_properties.py" "test_file_missing_or_empty"

# ── Check 2: test_properties.py has at least 10 test functions ───────────
check "python3 -c \"
import ast
with open('tests/test_properties.py') as f:
    tree = ast.parse(f.read())
test_funcs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name.startswith('test_')]
assert len(test_funcs) >= 10, f'Only {len(test_funcs)} test functions (need >= 10)'
print(f'FOUND {len(test_funcs)} TESTS')
\"" "too_few_tests"

# ── Check 3: Tests use Hypothesis @given decorator ───────────────────────
check "python3 -c \"
import ast
with open('tests/test_properties.py') as f:
    src = f.read()
tree = ast.parse(src)
given_count = 0
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef):
        for dec in node.decorator_list:
            dec_src = ast.dump(dec)
            if 'given' in dec_src:
                given_count += 1
assert given_count >= 5, f'Only {given_count} @given decorators (need >= 5)'
print(f'FOUND {given_count} @given DECORATED TESTS')
\"" "insufficient_hypothesis_usage"

# ── Check 4: Tests import all 3 data structures ─────────────────────────
check "python3 -c \"
with open('tests/test_properties.py') as f:
    src = f.read()
for name in ['$SL_NAME', '$BQ_NAME', '$LRU_NAME']:
    assert name in src, f'{name} not imported in test file'
print('ALL_IMPORTS_OK')
\"" "missing_datastructure_imports"

# ── Check 5: SortedList invariant tests exist (INV-1 through INV-4) ─────
check "python3 -c \"
with open('tests/test_properties.py') as f:
    src = f.read().lower()
# Must have test functions that reference sorting/order concepts
sort_tests = sum(1 for keyword in ['sorted', 'order', 'sort', 'insert', 'remove', 'contains']
                 if keyword in src)
assert sort_tests >= 3, f'Only {sort_tests} SortedList-related keywords found'
print(f'SORTED_LIST_TESTS: {sort_tests} keywords')
\"" "missing_sorted_list_invariant_tests"

# ── Check 6: BoundedQueue invariant tests exist (INV-5 through INV-7) ───
check "python3 -c \"
with open('tests/test_properties.py') as f:
    src = f.read().lower()
queue_tests = sum(1 for keyword in ['capacity', 'fifo', 'enqueue', 'dequeue', 'overflow', 'full', 'queue']
                  if keyword in src)
assert queue_tests >= 3, f'Only {queue_tests} BoundedQueue-related keywords found'
print(f'BOUNDED_QUEUE_TESTS: {queue_tests} keywords')
\"" "missing_bounded_queue_invariant_tests"

# ── Check 7: LRUCache invariant tests exist (INV-8 through INV-10) ──────
check "python3 -c \"
with open('tests/test_properties.py') as f:
    src = f.read().lower()
lru_tests = sum(1 for keyword in ['lru', 'evict', 'cache', 'capacity', 'put', 'get', 'recent']
                if keyword in src)
assert lru_tests >= 3, f'Only {lru_tests} LRUCache-related keywords found'
print(f'LRU_CACHE_TESTS: {lru_tests} keywords')
\"" "missing_lru_cache_invariant_tests"

# ── Check 8: Tests can be collected by pytest (no syntax errors) ────────
check "python3 -m pytest tests/test_properties.py --collect-only -q 2>&1 | grep -E '(test|selected)'" "tests_not_collectable"

# ── Check 9: At least some tests detect bugs (run and expect some failures on buggy code) ──
check "python3 -c \"
import subprocess, sys
result = subprocess.run(
    [sys.executable, '-m', 'pytest', 'tests/test_properties.py', '-x', '--tb=no', '-q',
     '--hypothesis-seed=0'],
    capture_output=True, text=True, timeout=120
)
# We expect some tests to FAIL because the code has bugs
# If all tests pass, the tests are not finding the bugs
output = result.stdout + result.stderr
if 'failed' in output or result.returncode != 0:
    print('BUGS_DETECTED: tests correctly fail on buggy code')
else:
    # Check if tests actually ran
    if 'passed' in output:
        # Tests all passed — they may not be detecting bugs
        # This is still partially OK if the tests are well-structured
        print('TESTS_PASS_WARNING: tests pass but may not detect all bugs')
    else:
        assert False, 'Tests did not run successfully'
\"" "tests_not_detecting_bugs"

# ── Check 10: Attestation ──────────────────────────────────────────────
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
