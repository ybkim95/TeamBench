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

# ── Helper: start a server on a given script, return PID ──────────────────
start_server() {
  local script="$1"
  python3 "$script" &
  local pid=$!
  # Wait up to 5s for it to be ready
  for i in $(seq 1 10); do
    sleep 0.5
    if python3 -c "import requests; requests.get('http://localhost:5000/health', timeout=1)" 2>/dev/null ||
       python3 -c "import requests; requests.get('http://localhost:5001/health', timeout=1)" 2>/dev/null ||
       python3 -c "import requests; requests.get('http://localhost:5002/health', timeout=1)" 2>/dev/null ||
       python3 -c "import requests; requests.get('http://localhost:5003/health', timeout=1)" 2>/dev/null; then
      break
    fi
  done
  echo "$pid"
}

kill_server() {
  local pid="$1"
  kill "$pid" 2>/dev/null || true
  wait "$pid" 2>/dev/null || true
}

# ── Check 1: test file exists ──────────────────────────────────────────────
check "test -f tests/test_integration.py" "test_file_missing"

# ── Check 2: test file is non-trivial (has actual test functions, not just TODOs) ──
check "python3 -c \"
import ast
with open('tests/test_integration.py') as f:
    src = f.read()
tree = ast.parse(src)
test_funcs = [
    n for n in ast.walk(tree)
    if isinstance(n, ast.FunctionDef) and n.name.startswith('test_')
    and any(
        not (isinstance(s, ast.Pass) or
             (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant)))
        for s in ast.walk(n)
        if isinstance(s, (ast.Assert, ast.Call, ast.Return))
    )
]
assert len(test_funcs) >= 3, f'Only {len(test_funcs)} implemented test functions (need >= 3 with actual assertions)'
print(f'IMPLEMENTED_TESTS: {len(test_funcs)}')
\"" "tests_not_implemented"

# ── Check 3: minimum test count ───────────────────────────────────────────
check "python3 -c \"
import ast, json, os
expected_path = None
for candidate in [
    os.path.join('$REPORTS', '../expected.json'),
    os.path.join('$REPORTS', 'expected.json'),
]:
    if os.path.exists(candidate):
        expected_path = candidate
        break
with open('tests/test_integration.py') as f:
    tree = ast.parse(f.read())
test_funcs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name.startswith('test_')]
min_tests = 8  # fallback
if expected_path:
    data = json.load(open(expected_path))
    min_tests = data.get('min_tests', 8)
assert len(test_funcs) >= min_tests, f'Only {len(test_funcs)} test functions (need >= {min_tests})'
print(f'TEST_COUNT: {len(test_funcs)} >= {min_tests}')
\"" "too_few_tests"

# ── Check 4: tests use assertions (not just pass/TODO) ────────────────────
check "python3 -c \"
import ast
with open('tests/test_integration.py') as f:
    tree = ast.parse(f.read())
assert_stmts = [n for n in ast.walk(tree) if isinstance(n, ast.Assert)]
raises_calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and
    hasattr(n.func, 'attr') and n.func.attr == 'raises']
# Also check for status_code comparisons via assert
eq_calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and
    hasattr(n.func, 'attr') and n.func.attr in ('assertEqual', 'assertEqual')]
total = len(assert_stmts) + len(raises_calls)
assert total >= 3, f'Only {total} assert statements/raises found (need >= 3)'
print(f'ASSERTIONS: {total}')
\"" "no_assertions"

# ── Check 5: health endpoint covered ─────────────────────────────────────
check "python3 -c \"
with open('tests/test_integration.py') as f:
    src = f.read()
assert '/health' in src or 'health' in src.lower(), 'No health endpoint test found'
print('HEALTH_ENDPOINT_COVERED')
\"" "health_not_tested"

# ── Check 6: auth enforcement tested (401) ───────────────────────────────
check "python3 -c \"
with open('tests/test_integration.py') as f:
    src = f.read()
assert '401' in src, 'No 401 status code check found — auth enforcement not tested'
print('AUTH_401_TESTED')
\"" "auth_not_tested"

# ── Check 7: 400 validation errors tested ────────────────────────────────
check "python3 -c \"
with open('tests/test_integration.py') as f:
    src = f.read()
assert '400' in src, 'No 400 status code check found — validation errors not tested'
print('VALIDATION_400_TESTED')
\"" "validation_not_tested"

# ── Check 8: 404 not-found cases tested ──────────────────────────────────
check "python3 -c \"
with open('tests/test_integration.py') as f:
    src = f.read()
assert '404' in src, 'No 404 status code check found — not-found cases not tested'
print('NOTFOUND_404_TESTED')
\"" "notfound_not_tested"

# ── Check 9: response schema fields verified ──────────────────────────────
check "python3 -c \"
with open('tests/test_integration.py') as f:
    src = f.read()
# Tests should check response JSON keys, not just status codes
import re
json_key_checks = re.findall(r'\[[\'\"][a-z_]+[\'\"]\]|\.get\([\'\"][a-z_]+[\'\"]\)|assert.*in.*json|json.*\[', src)
assert len(json_key_checks) >= 2, f'Tests appear to only check status codes — verify response body fields too'
print(f'SCHEMA_CHECKS: {len(json_key_checks)}')
\"" "schema_not_verified"

# ── Check 10: all tests pass against working server ───────────────────────
SERVER_PID=""
check "python3 -c \"
import subprocess, sys, time, os

# Start working server in background
srv = subprocess.Popen(
    [sys.executable, 'server.py'],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
)
time.sleep(2)

try:
    result = subprocess.run(
        [sys.executable, '-m', 'pytest', 'tests/test_integration.py', '-q', '--tb=short'],
        capture_output=True, text=True, timeout=120
    )
    print(result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)
    if result.stderr:
        print(result.stderr[-1000:], file=sys.stderr)
    assert result.returncode == 0, f'Tests failed on working server (exit {result.returncode})'
    print('ALL_TESTS_PASS_ON_WORKING_SERVER')
finally:
    srv.terminate()
    srv.wait(timeout=5)
\"" "tests_fail_on_working_server"

# ── Check 11: tests FAIL against broken server (mutation detection) ────────
check "python3 -c \"
import subprocess, sys, time

srv = subprocess.Popen(
    [sys.executable, 'broken_server.py'],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
)
time.sleep(2)

try:
    result = subprocess.run(
        [sys.executable, '-m', 'pytest', 'tests/test_integration.py', '-q', '--tb=no'],
        capture_output=True, text=True, timeout=120
    )
    print(result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)
    # Tests SHOULD fail (returncode != 0) against the broken server
    assert result.returncode != 0, 'Tests passed on broken server — mutation not detected'
    print('MUTATION_DETECTED: tests correctly fail on broken server')
finally:
    srv.terminate()
    srv.wait(timeout=5)
\"" "mutation_not_detected"

# ── Check 12: Content-Type header verified ────────────────────────────────
check "python3 -c \"
with open('tests/test_integration.py') as f:
    src = f.read()
has_content_type = (
    'content-type' in src.lower() or
    'Content-Type' in src or
    'application/json' in src or
    'headers' in src.lower()
)
assert has_content_type, 'No Content-Type or headers verification found'
print('CONTENT_TYPE_VERIFIED')
\"" "content_type_not_verified"

# ── Score output ──────────────────────────────────────────────────────────
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
