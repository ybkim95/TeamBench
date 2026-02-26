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

# Load seed-specific expected values
EXPECTED_JSON="$REPORTS/expected.json"
if [ -f "$EXPECTED_JSON" ]; then
  MODULE_NAME=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('module_name','textparser'))")
  CLASS_NAME=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('class_name','TextParser'))")
  FEAT_FUNC=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('feat_func','enable_strict_mode'))")
  DEPRECATED_ALIAS=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('deprecated_alias','run'))")
  EXTRA_KEY=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('extra_key','version'))")
  VERSION_STR=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('version_str','1.2.0'))")
else
  MODULE_NAME="textparser"
  CLASS_NAME="TextParser"
  FEAT_FUNC="enable_strict_mode"
  DEPRECATED_ALIAS="run"
  EXTRA_KEY="version"
  VERSION_STR="1.2.0"
fi

cd "$WORKSPACE"

# ── Check 1: new_feature.py exists and has no NotImplementedError active ──────
check "python3 -c \"
import ast, sys
with open('new_feature.py') as f:
    src = f.read()
assert 'NotImplementedError' not in src or 'raise NotImplementedError' not in src, \
    'new_feature.py still raises NotImplementedError'
print('NEW_FEATURE_IMPLEMENTED')
\"" "new_feature_not_implemented"

# ── Check 2: feat_func is importable and callable ─────────────────────────────
check "python3 -c \"
import sys
sys.path.insert(0, '.')
from new_feature import ${FEAT_FUNC}
assert callable(${FEAT_FUNC}), '${FEAT_FUNC} must be callable'
print('FEAT_FUNC_IMPORTABLE')
\"" "feat_func_not_importable"

# ── Check 3: feat_func returns the same instance (in-place) ──────────────────
check "python3 -c \"
import sys
sys.path.insert(0, '.')
from ${MODULE_NAME} import ${CLASS_NAME}
from new_feature import ${FEAT_FUNC}
obj = ${CLASS_NAME}()
result = ${FEAT_FUNC}(obj)
assert result is obj, '${FEAT_FUNC} must return the same instance'
print('RETURNS_SAME_INSTANCE')
\"" "feat_func_returns_wrong_object"

# ── Check 4: process() still returns dict with required keys after enhancement ─
check "python3 -c \"
import sys
sys.path.insert(0, '.')
from ${MODULE_NAME} import ${CLASS_NAME}
from new_feature import ${FEAT_FUNC}
obj = ${CLASS_NAME}()
${FEAT_FUNC}(obj)
result = obj.process('hello')
assert isinstance(result, dict), 'process() must return dict'
assert 'result' in result, 'missing result key'
assert 'status' in result, 'missing status key'
assert '${EXTRA_KEY}' in result, 'missing ${EXTRA_KEY} key'
assert result['status'] == 'ok', 'status must be ok'
print('PROCESS_SHAPE_PRESERVED')
\"" "process_shape_broken"

# ── Check 5: Constructor still accepts None, str, dict (all legacy formats) ───
check "python3 -c \"
import sys
sys.path.insert(0, '.')
from ${MODULE_NAME} import ${CLASS_NAME}
from new_feature import ${FEAT_FUNC}
obj1 = ${CLASS_NAME}()
obj2 = ${CLASS_NAME}(config=None)
obj3 = ${CLASS_NAME}(config='key=val,mode=fast')
obj4 = ${CLASS_NAME}(config={'a': '1'})
for o in [obj1, obj2, obj3, obj4]:
    ${FEAT_FUNC}(o)
    r = o.process('test')
    assert r['status'] == 'ok'
print('CONSTRUCTOR_COMPAT_OK')
\"" "constructor_compat_broken"

# ── Check 6: Deprecated alias still callable and returns same shape ────────────
check "python3 -c \"
import sys, warnings
sys.path.insert(0, '.')
from ${MODULE_NAME} import ${CLASS_NAME}
from new_feature import ${FEAT_FUNC}
obj = ${CLASS_NAME}()
${FEAT_FUNC}(obj)
with warnings.catch_warnings():
    warnings.simplefilter('ignore', DeprecationWarning)
    r = obj.${DEPRECATED_ALIAS}('test')
assert isinstance(r, dict), 'deprecated alias must return dict'
assert 'result' in r
assert 'status' in r
assert r['status'] == 'ok'
print('DEPRECATED_ALIAS_STILL_WORKS')
\"" "deprecated_alias_broken"

# ── Check 7: Deprecated alias still emits DeprecationWarning ──────────────────
check "python3 -c \"
import sys, warnings
sys.path.insert(0, '.')
from ${MODULE_NAME} import ${CLASS_NAME}
from new_feature import ${FEAT_FUNC}
obj = ${CLASS_NAME}()
${FEAT_FUNC}(obj)
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter('always')
    obj.${DEPRECATED_ALIAS}('x')
assert any(issubclass(warning.category, DeprecationWarning) for warning in w), \
    'deprecated alias must still emit DeprecationWarning'
print('DEPRECATION_WARNING_EMITTED')
\"" "deprecation_warning_suppressed"

# ── Check 8: ValueError for None data still starts with 'Invalid input:' ──────
check "python3 -c \"
import sys
sys.path.insert(0, '.')
from ${MODULE_NAME} import ${CLASS_NAME}
from new_feature import ${FEAT_FUNC}
obj = ${CLASS_NAME}()
${FEAT_FUNC}(obj)
try:
    obj.process(None)
    assert False, 'Should have raised ValueError'
except ValueError as e:
    assert str(e).startswith('Invalid input:'), f'Wrong error message: {str(e)}'
print('ERROR_MESSAGE_STABLE')
\"" "error_message_changed"

# ── Check 9: __version__ remains in 1.x series ────────────────────────────────
check "python3 -c \"
import sys
sys.path.insert(0, '.')
from ${MODULE_NAME} import ${CLASS_NAME}
ver = ${CLASS_NAME}.__version__
assert isinstance(ver, str), '__version__ must be a string'
assert ver.startswith('1.'), f'__version__ must stay 1.x, got {ver}'
print('VERSION_STABLE')
\"" "version_bumped"

# ── Check 10: core.py was not modified (sig check) ────────────────────────────
check "python3 -c \"
import sys, inspect
sys.path.insert(0, '.')
from ${MODULE_NAME} import ${CLASS_NAME}
# Verify __init__ signature has exactly (self, config=None)
sig = inspect.signature(${CLASS_NAME}.__init__)
params = list(sig.parameters.keys())
assert params == ['self', 'config'], f'Constructor signature changed: {params}'
# Verify config default is None
p = sig.parameters['config']
assert p.default is None, f'config default changed to {p.default}'
print('CONSTRUCTOR_SIG_UNCHANGED')
\"" "constructor_signature_changed"

# ── Check 11: Enhancement is instance-scoped (doesn't pollute other instances) ─
check "python3 -c \"
import sys
sys.path.insert(0, '.')
from ${MODULE_NAME} import ${CLASS_NAME}
from new_feature import ${FEAT_FUNC}
obj1 = ${CLASS_NAME}()
obj2 = ${CLASS_NAME}()
${FEAT_FUNC}(obj1)
# obj2 must still work cleanly
r = obj2.process('hello')
assert r['status'] == 'ok', 'Enhancement polluted other instances'
# obj1 must work too
r2 = obj1.process('world')
assert r2['status'] == 'ok'
print('INSTANCE_SCOPED')
\"" "enhancement_not_instance_scoped"

# ── Check 12: Double-enhancement is idempotent ────────────────────────────────
check "python3 -c \"
import sys
sys.path.insert(0, '.')
from ${MODULE_NAME} import ${CLASS_NAME}
from new_feature import ${FEAT_FUNC}
obj = ${CLASS_NAME}()
r1 = ${FEAT_FUNC}(obj)
r2 = ${FEAT_FUNC}(obj)
assert r1 is obj and r2 is obj
result = obj.process('idempotent')
assert result['status'] == 'ok'
print('IDEMPOTENT')
\"" "enhancement_not_idempotent"

# ── Check 13: Full pytest suite passes ────────────────────────────────────────
check "python3 -m pytest tests/ -q --tb=no 2>&1 | tail -1 | grep -E '^[0-9]+ passed'" "pytest_suite_failed"

# ── Check 14: Attestation ─────────────────────────────────────────────────────
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
