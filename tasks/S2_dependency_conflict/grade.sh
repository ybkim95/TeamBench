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

# Load seed-specific expected values if available, else use legacy defaults
EXPECTED_JSON="$REPORTS/expected.json"
if [ -f "$EXPECTED_JSON" ]; then
  PKG2_BUGGY_IMPORT=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('pkg2_buggy_import','utils.compat'))")
  PKG2_CORRECT_IMPORT=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('pkg2_correct_import','utils.v2'))")
  PKG1_NAME=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('pkg1_name','libfoo'))")
  PKG2_NAME=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('pkg2_name','libbar'))")
  UTIL_PKG=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('util_pkg_name','utils_pkg'))")
  UTIL_MODULE=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('util_module','utils'))")
  REQUIRED_UTILS_VER=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('required_utils_version','2.0.0'))")
else
  # Legacy defaults (original task seed)
  PKG2_BUGGY_IMPORT="utils.compat"
  PKG2_CORRECT_IMPORT="utils.v2"
  PKG1_NAME="libfoo"
  PKG2_NAME="libbar"
  UTIL_PKG="utils_pkg"
  UTIL_MODULE="utils"
  REQUIRED_UTILS_VER="2.0.0"
fi

cd "$WORKSPACE"

check "python3 -c \"
with open('requirements.txt') as f:
    content = f.read()
lines = [l.strip() for l in content.splitlines() if l.strip() and not l.startswith('#')]
utils_found = False
for l in lines:
    if l.startswith('${UTIL_MODULE}'):
        utils_found = True
        ver = l.split('==')[1] if '==' in l else ''
        major = int(ver.split('.')[0]) if ver else 0
        assert major >= 2, f'${UTIL_MODULE} must be >=2.0, got {l}'
assert utils_found, 'requirements.txt must pin ${UTIL_MODULE}'
print('REQUIREMENTS_OK')
\"" "bad_requirements"

check "python3 -c \"
with open('vendor/${PKG2_NAME}/${PKG2_NAME}_core.py') as f:
    code = f.read()
assert '${PKG2_BUGGY_IMPORT}' not in code, '${PKG2_NAME} still uses buggy import path'
assert '${PKG2_CORRECT_IMPORT}' in code, '${PKG2_NAME} must use ${PKG2_CORRECT_IMPORT}'
print('PKG2_FIX_OK')
\"" "pkg2_not_fixed"

check "python3 -c \"
import sys, os
sys.path.insert(0, 'vendor/${UTIL_PKG}')
sys.path.insert(0, 'vendor/${PKG1_NAME}')
sys.path.insert(0, 'vendor/${PKG2_NAME}')
from ${PKG1_NAME}_core import *
from ${PKG2_NAME}_core import *
import inspect
pkg1_funcs = [n for n,f in inspect.getmembers(__import__('${PKG1_NAME}_core'), inspect.isfunction)]
pkg2_funcs = [n for n,f in inspect.getmembers(__import__('${PKG2_NAME}_core'), inspect.isfunction)]
assert len(pkg1_funcs) > 0, 'no functions in ${PKG1_NAME}_core'
assert len(pkg2_funcs) > 0, 'no functions in ${PKG2_NAME}_core'
pkg1_mod = __import__('${PKG1_NAME}_core')
pkg2_mod = __import__('${PKG2_NAME}_core')
r1 = getattr(pkg1_mod, pkg1_funcs[0])('x')
r2 = getattr(pkg2_mod, pkg2_funcs[0])('y')
assert r1['version'] == '2.0', f'${PKG1_NAME} version wrong: {r1}'
assert r2['version'] == '2.0', f'${PKG2_NAME} version wrong: {r2}'
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
