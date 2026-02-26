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

EXPECTED="$REPORTS/expected.json"

# Determine the module file from expected.json
MODULE_FILE=$(python3 -c "import json; print(json.load(open('$EXPECTED'))['module_file'])" 2>/dev/null)
if [ -z "$MODULE_FILE" ]; then
  MODULE_FILE="data_utils.py"
fi

# ── Check 1: Class names are PascalCase ──────────────────────────────────────
check "python3 -c \"
import json, re
with open('$EXPECTED') as f:
    exp = json.load(f)
cls_good  = exp['class_good']
cls2_good = exp['class2_good']
cls_bad   = exp['class_bad']
cls2_bad  = exp['class2_bad']
with open('$MODULE_FILE') as f:
    code = f.read()
# Good names must be defined as classes
assert re.search(r'^class ' + re.escape(cls_good) + r'[\s:(]', code, re.MULTILINE), \
    f'PascalCase class {cls_good!r} not found'
assert re.search(r'^class ' + re.escape(cls2_good) + r'[\s:(]', code, re.MULTILINE), \
    f'PascalCase class {cls2_good!r} not found'
# Bad names must NOT appear as class definitions
assert not re.search(r'^class ' + re.escape(cls_bad) + r'[\s:(]', code, re.MULTILINE), \
    f'Bad class name {cls_bad!r} still defined'
assert not re.search(r'^class ' + re.escape(cls2_bad) + r'[\s:(]', code, re.MULTILINE), \
    f'Bad class name {cls2_bad!r} still defined'
print('CLASS_NAMES_OK')
\"" "class_names_not_pascal_case"

# ── Check 2: Function names are snake_case ───────────────────────────────────
check "python3 -c \"
import json, re
with open('$EXPECTED') as f:
    exp = json.load(f)
fn1_good = exp['fn1_good']
fn2_good = exp['fn2_good']
fn1_bad  = exp['fn1_bad']
fn2_bad  = exp['fn2_bad']
with open('$MODULE_FILE') as f:
    code = f.read()
# Good names must exist as function/method definitions
assert re.search(r'def ' + re.escape(fn1_good) + r'\s*\(', code), \
    f'snake_case function {fn1_good!r} not found'
assert re.search(r'def ' + re.escape(fn2_good) + r'\s*\(', code), \
    f'snake_case function {fn2_good!r} not found'
# Bad names must NOT appear as definitions
assert not re.search(r'def ' + re.escape(fn1_bad) + r'\s*\(', code), \
    f'camelCase function {fn1_bad!r} still defined'
assert not re.search(r'def ' + re.escape(fn2_bad) + r'\s*\(', code), \
    f'camelCase function {fn2_bad!r} still defined'
print('FUNCTION_NAMES_OK')
\"" "function_names_not_snake_case"

# ── Check 3: Local variable names are snake_case ─────────────────────────────
check "python3 -c \"
import json, re
with open('$EXPECTED') as f:
    exp = json.load(f)
var1_bad = exp['var1_bad']
var2_bad = exp['var2_bad']
with open('$MODULE_FILE') as f:
    code = f.read()
# camelCase variable names must not appear as assignments
assert not re.search(r'\b' + re.escape(var1_bad) + r'\s*=', code), \
    f'camelCase variable {var1_bad!r} still present'
assert not re.search(r'\b' + re.escape(var2_bad) + r'\s*=', code), \
    f'camelCase variable {var2_bad!r} still present'
print('VARIABLE_NAMES_OK')
\"" "variable_names_not_snake_case"

# ── Check 4: No wildcard imports ─────────────────────────────────────────────
check "python3 -c \"
import re
with open('$MODULE_FILE') as f:
    code = f.read()
wildcards = re.findall(r'^from\s+\S+\s+import\s+\*', code, re.MULTILINE)
assert len(wildcards) == 0, f'Wildcard imports still present: {wildcards}'
print('NO_WILDCARD_IMPORTS')
\"" "wildcard_imports_present"

# ── Check 5: Import order correct (stdlib before third-party) ─────────────────
check "python3 -c \"
import re
with open('$MODULE_FILE') as f:
    code = f.read()
# Third-party packages that should NOT appear before any stdlib import
third_party = ['requests', 'numpy', 'yaml', 'boto3', 'np']
lines = code.split('\n')
import_lines = [(i, l.strip()) for i, l in enumerate(lines) if re.match(r'^import |^from \S+ import', l.strip())]
# Find the first third-party import line index
first_tp = None
for idx, (lineno, imp) in enumerate(import_lines):
    for pkg in third_party:
        if re.match(r'^import ' + re.escape(pkg) + r'(\s|$)', imp) or \
           re.match(r'^from ' + re.escape(pkg) + r'(\s|\.|$)', imp):
            if first_tp is None:
                first_tp = (idx, lineno, imp)
if first_tp is not None:
    tp_idx, tp_lineno, tp_imp = first_tp
    # All imports before first_tp must also be third-party, OR there must be
    # a blank line between the last stdlib and first third-party
    # Check: no stdlib import appears AFTER first third-party without a blank line separator
    import sys
    stdlib_after = []
    for idx2, (lineno2, imp2) in enumerate(import_lines[tp_idx+1:], tp_idx+1):
        pkg_name = re.match(r'^import (\S+)', imp2)
        if pkg_name:
            name = pkg_name.group(1).split('.')[0]
            if name in sys.stdlib_module_names if hasattr(sys, 'stdlib_module_names') else name not in third_party:
                # Check if there is a blank line between tp and this import
                between_lines = lines[tp_lineno+1:lineno2]
                if not any(l.strip() == '' for l in between_lines):
                    stdlib_after.append(imp2)
    assert len(stdlib_after) == 0, f'stdlib imports after third-party without blank separator: {stdlib_after}'
print('IMPORT_ORDER_OK')
\"" "import_order_incorrect"

# ── Check 6: All public functions/methods have type hints ─────────────────────
check "python3 -c \"
import ast, sys
with open('$MODULE_FILE') as f:
    src = f.read()
tree = ast.parse(src)

missing = []
for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        # Skip private (leading underscore)
        if node.name.startswith('_'):
            continue
        # Check return annotation
        if node.returns is None:
            missing.append(f'{node.name}: missing return type annotation')
        # Check parameter annotations (skip self/cls)
        for arg in node.args.args:
            if arg.arg in ('self', 'cls'):
                continue
            if arg.annotation is None:
                missing.append(f'{node.name}: param {arg.arg!r} missing type annotation')

assert len(missing) == 0, 'Missing type hints:\\n' + '\\n'.join(missing)
print('TYPE_HINTS_OK')
\"" "type_hints_missing"

# ── Check 7: Line length <= 88 characters ────────────────────────────────────
check "python3 -c \"
with open('$MODULE_FILE') as f:
    lines = f.readlines()
long_lines = [(i+1, len(l.rstrip()), l.rstrip()) for i, l in enumerate(lines) if len(l.rstrip()) > 88]
assert len(long_lines) == 0, \
    'Lines exceeding 88 chars:\\n' + '\\n'.join(f'  line {n}: {length} chars' for n, length, _ in long_lines)
print('LINE_LENGTH_OK')
\"" "line_length_exceeded"

# ── Check 8: Public functions/methods have Google-style docstrings ────────────
check "python3 -c \"
import ast
with open('$MODULE_FILE') as f:
    src = f.read()
tree = ast.parse(src)

missing_doc = []
bad_doc = []
for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if node.name.startswith('_'):
            continue
        docstring = ast.get_docstring(node)
        if docstring is None:
            missing_doc.append(node.name)
            continue
        # Google style: first line ends with period, and if multi-param,
        # should have Args: section. At minimum docstring must be non-trivial.
        if len(docstring.strip()) < 10:
            bad_doc.append(f'{node.name}: docstring too short')
        # Must end first line with a period (sentence)
        first_line = docstring.strip().split('\n')[0]
        if not first_line.endswith('.'):
            bad_doc.append(f'{node.name}: first docstring line does not end with a period')

assert len(missing_doc) == 0, f'Public functions missing docstrings: {missing_doc}'
assert len(bad_doc) == 0, f'Bad docstrings: {bad_doc}'
print('DOCSTRINGS_OK')
\"" "docstrings_missing_or_bad"

# ── Check 9: Trailing commas in multi-line collections ───────────────────────
check "python3 -c \"
import ast, tokenize, io
with open('$MODULE_FILE') as f:
    src = f.read()
# Parse and check: no SyntaxError means trailing commas don't break anything.
# We look for multi-line list/dict literals where the last element lacks a comma.
# Simple heuristic: find patterns like:
#   'value'\n    ] or 'value'\n    }  without a trailing comma
import re
# Match: a string or identifier at end of line, then optional whitespace, then ] or }
# that is NOT preceded by a comma
bad = re.findall(
    r'([^,\n])\s*\n\s*[}\]]',
    src
)
# Filter out comments and blank lines
filtered = [b for b in bad if b.strip() not in ('', '#')]
assert len(filtered) == 0, f'Missing trailing commas in multi-line collections ({len(filtered)} found)'
print('TRAILING_COMMAS_OK')
\"" "trailing_commas_missing"

# ── Check 10: File is syntactically valid Python ──────────────────────────────
check "python3 -c \"
import py_compile
py_compile.compile('$MODULE_FILE', doraise=True)
print('SYNTAX_OK')
\"" "syntax_error"

# ── Check 11: Tests still pass ───────────────────────────────────────────────
check "python3 -m pytest tests/test_module.py -q --tb=short 2>&1 | tail -5 | grep -E '^[0-9]+ passed'" "tests_failing"

# ── Check 12: No functional logic changed (function count preserved) ───────────
check "python3 -c \"
import ast
with open('$MODULE_FILE') as f:
    src = f.read()
tree = ast.parse(src)
funcs = [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
# Must have at least 5 functions (process, validate, fn1, fn2, _internal_helper, __init__)
assert len(funcs) >= 5, f'Too few functions — logic may have been removed: {funcs}'
print('FUNCTION_COUNT_OK')
\"" "functions_removed"

# ── Check 13: Attestation ─────────────────────────────────────────────────────
check "python3 -c \"
import json, sys
att = json.load(open(sys.argv[1]))
assert att.get('verdict') == 'pass', f'verdict={att.get(\\\"verdict\\\")}'
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
