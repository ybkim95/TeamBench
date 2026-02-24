#!/usr/bin/env bash
set -euo pipefail
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

check "python3 -c \"
with open('requirements.txt') as f:
    content = f.read()
lines = [l.strip() for l in content.splitlines() if l.strip() and not l.startswith('#')]
utils_found = False
for l in lines:
    if l.startswith('utils'):
        utils_found = True
        ver = l.split('==')[1] if '==' in l else ''
        major = int(ver.split('.')[0]) if ver else 0
        assert major >= 2, f'utils must be >=2.0, got {l}'
assert utils_found, 'requirements.txt must pin utils'
print('REQUIREMENTS_OK')
\"" "bad_requirements"

check "python3 -c \"
with open('vendor/libbar/libbar_core.py') as f:
    code = f.read()
assert 'utils.legacy' not in code and 'utils.compat' not in code, 'libbar still uses legacy/compat path'
assert 'utils.v2' in code, 'libbar must use utils.v2'
print('LIBBAR_FIX_OK')
\"" "libbar_not_fixed"

check "python3 -c \"
import sys, os
sys.path.insert(0, 'vendor/utils_pkg')
sys.path.insert(0, 'vendor/libfoo')
sys.path.insert(0, 'vendor/libbar')
from libfoo_core import foo_process
from libbar_core import bar_process
r1 = foo_process('x')
r2 = bar_process('y')
assert r1['mode'] == 'foo'
assert r2['mode'] == 'bar'
assert r1['version'] == '2.0'
assert r2['version'] == '2.0'
print('INTEGRATION_OK')
\"" "integration_test_fail"

check "python3 -c \"
import json, sys
att = json.load(open(sys.argv[1]))
assert att.get('verdict') == 'pass'
\" '$SUBMISSION/attestation.json'" "bad_attestation"

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
