#!/usr/bin/env bash
# Grade script for CR4: API Design Review Fix
# Arguments:
#   $1 = WORKSPACE  (directory containing app.py and tests/)
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

# Read expected values
RESOURCE=$(python3 -c "import json; print(json.load(open('$EXPECTED'))['resource'])" 2>/dev/null)
RESOURCES=$(python3 -c "import json; print(json.load(open('$EXPECTED'))['resources'])" 2>/dev/null)
V1_BAD=$(python3 -c "import json; print(json.load(open('$EXPECTED'))['v1_bad_method'])" 2>/dev/null)
V2_BAD=$(python3 -c "import json; print(json.load(open('$EXPECTED'))['v2_bad_name'])" 2>/dev/null)
V2_GOOD=$(python3 -c "import json; print(json.load(open('$EXPECTED'))['v2_good_name'])" 2>/dev/null)
V3P1=$(python3 -c "import json; print(json.load(open('$EXPECTED'))['v3_param1'])" 2>/dev/null)
V3P2=$(python3 -c "import json; print(json.load(open('$EXPECTED'))['v3_param2'])" 2>/dev/null)
V4_BAD=$(python3 -c "import json; print(json.load(open('$EXPECTED'))['v4_bad_code'])" 2>/dev/null)
V4_GOOD=$(python3 -c "import json; print(json.load(open('$EXPECTED'))['v4_good_code'])" 2>/dev/null)

# ── Check 1: app.py is syntactically valid Python ────────────────────────────
check "python3 -c \"
import py_compile
py_compile.compile('app.py', doraise=True)
print('SYNTAX_OK')
\"" "syntax_error"

# ── Check 2: app.py imports without errors ───────────────────────────────────
check "python3 -c \"
import importlib.util, sys
spec = importlib.util.spec_from_file_location('app', 'app.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print('IMPORT_OK')
\"" "import_error"

# ── Check 3: All tests pass ───────────────────────────────────────────────────
check "python3 -m pytest tests/test_api.py -q --tb=short 2>&1 | tail -5 | grep -E '^[0-9]+ passed'" "tests_failing"

# ── Check 4: V5 — All routes use /api/v1/ prefix ─────────────────────────────
check "python3 -c \"
import ast, re

with open('app.py') as f:
    src = f.read()

tree = ast.parse(src)

# Collect all route strings from @app.route(...) decorators
routes = []
for node in ast.walk(tree):
    if isinstance(node, ast.Call):
        fn = node.func
        is_route = (
            (isinstance(fn, ast.Attribute) and fn.attr == 'route') or
            (isinstance(fn, ast.Name) and fn.id == 'route')
        )
        if is_route and node.args:
            route_val = node.args[0]
            if isinstance(route_val, ast.Constant):
                routes.append(route_val.value)

assert routes, 'No @app.route decorators found in app.py'

# Every route must start with /api/v1/ (health and stats too)
bad_routes = [r for r in routes if not r.startswith('/api/v1/')]
assert not bad_routes, f'Routes missing /api/v1/ prefix: {bad_routes}'
print('VERSIONING_OK')
\"" "missing_api_v1_prefix"

# ── Check 5: V1 — Create endpoint uses POST, not the bad method ──────────────
check "python3 -c \"
import ast

with open('app.py') as f:
    src = f.read()
tree = ast.parse(src)

bad_method = '$V1_BAD'
resource = '$RESOURCE'

# Look for the create function's decorator
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == f'create_{resource}':
        for dec in node.decorator_list:
            if isinstance(dec, ast.Call) and dec.keywords:
                for kw in dec.keywords:
                    if kw.arg == 'methods' and isinstance(kw.value, ast.List):
                        methods = [
                            elt.value for elt in kw.value.elts
                            if isinstance(elt, ast.Constant)
                        ]
                        assert bad_method not in methods, \
                            f'create_{resource} still uses {bad_method} — V1 not fixed'
                        assert 'POST' in methods, \
                            f'create_{resource} must use POST, got {methods}'
print('HTTP_METHOD_OK')
\"" "wrong_http_method_not_fixed"

# ── Check 6: V1 — No GET-based create routes anywhere ────────────────────────
check "python3 -c \"
import ast

with open('app.py') as f:
    src = f.read()
tree = ast.parse(src)

# Scan all route decorators: no POST-equivalent path should allow GET
# Specifically: routes ending in just /<resources> (collection) must not allow GET for creation
# We simply check that 'create_' functions don't have GET in their methods
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name.startswith('create_'):
        for dec in node.decorator_list:
            if isinstance(dec, ast.Call):
                for kw in dec.keywords:
                    if kw.arg == 'methods' and isinstance(kw.value, ast.List):
                        methods = [
                            elt.value for elt in kw.value.elts
                            if isinstance(elt, ast.Constant)
                        ]
                        assert 'GET' not in methods, \
                            f'{node.name} must not use GET for creation'
print('NO_GET_CREATE')
\"" "get_used_for_create"

# ── Check 7: V2 — camelCase route name is gone; snake_case present ────────────
check "python3 -c \"
import ast, re

with open('app.py') as f:
    src = f.read()
tree = ast.parse(src)

bad_name = '$V2_BAD'

# The old camelCase route string must not appear in any route decorator
routes = []
for node in ast.walk(tree):
    if isinstance(node, ast.Call):
        fn = node.func
        is_route = (
            (isinstance(fn, ast.Attribute) and fn.attr == 'route') or
            (isinstance(fn, ast.Name) and fn.id == 'route')
        )
        if is_route and node.args and isinstance(node.args[0], ast.Constant):
            routes.append(node.args[0].value)

bad_routes = [r for r in routes if bad_name in r]
assert not bad_routes, f'camelCase route segment {bad_name!r} still present: {bad_routes}'

# A snake_case search/filter route must exist
has_search = any('search' in r or 'filter' in r for r in routes)
assert has_search, f'No snake_case search route found. Routes: {routes}'
print('NAMING_OK')
\"" "camelcase_route_not_fixed"

# ── Check 8: V2 — Function name is snake_case (camelCase function gone) ───────
check "python3 -c \"
import ast

with open('app.py') as f:
    src = f.read()
tree = ast.parse(src)

bad_fn = '$V2_BAD'

for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef):
        assert node.name != bad_fn, \
            f'camelCase function {bad_fn!r} still defined — V2 not fixed'
print('FUNCTION_NAMES_SNAKE_CASE')
\"" "camelcase_function_not_fixed"

# ── Check 9: V3 — List endpoint accepts pagination query params ───────────────
check "python3 -c \"
import ast

with open('app.py') as f:
    src = f.read()
tree = ast.parse(src)

resources = '$RESOURCES'
p1 = '$V3P1'
p2 = '$V3P2'

# Find list function
list_fn = None
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == f'list_{resources}':
        list_fn = node
        break

assert list_fn is not None, f'list_{resources} function not found'

fn_src = ast.unparse(list_fn) if hasattr(ast, 'unparse') else ''

# Must reference both pagination param names via request.args.get(...)
import re
# Check for request.args.get calls with our param names
calls_p1 = re.search(rf\"request\\.args\\.get\\(['\\\"]{{re.escape(p1)}}['\\\"]\\)\", fn_src)
calls_p2 = re.search(rf\"request\\.args\\.get\\(['\\\"]{{re.escape(p2)}}['\\\"]\\)\", fn_src)
assert calls_p1, f'list_{resources} does not use request.args.get(\"{p1}\")'
assert calls_p2, f'list_{resources} does not use request.args.get(\"{p2}\")'
print('PAGINATION_OK')
\"" "pagination_not_implemented"

# ── Check 10: V3 — List response has pagination envelope fields ───────────────
check "python3 -c \"
import ast

with open('app.py') as f:
    src = f.read()
tree = ast.parse(src)

resources = '$RESOURCES'
p1 = '$V3P1'
p2 = '$V3P2'

list_fn = None
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == f'list_{resources}':
        list_fn = node
        break

assert list_fn is not None

fn_src = ast.unparse(list_fn) if hasattr(ast, 'unparse') else ''

# The response dict/jsonify call should reference pagination fields
assert p1 in fn_src, f'list_{resources} response does not include \"{p1}\" key'
assert p2 in fn_src, f'list_{resources} response does not include \"{p2}\" key'
assert 'total' in fn_src, f'list_{resources} response does not include \"total\" key'
print('PAGINATION_ENVELOPE_OK')
\"" "pagination_envelope_missing"

# ── Check 11: V4 — Create returns 201, not the bad code ──────────────────────
check "python3 -c \"
import ast

with open('app.py') as f:
    src = f.read()
tree = ast.parse(src)

resource = '$RESOURCE'
v4_bad = int('$V4_BAD')

# Find create function and check its return statements
create_fn = None
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == f'create_{resource}':
        create_fn = node
        break

assert create_fn is not None, f'create_{resource} not found'

# Collect all integer constants in return statements
for node in ast.walk(create_fn):
    if isinstance(node, ast.Return) and node.value:
        # Check for tuple returns like (jsonify(...), 200) — the second element
        if isinstance(node.value, ast.Tuple) and len(node.value.elts) >= 2:
            status_node = node.value.elts[-1]
            if isinstance(status_node, ast.Constant) and isinstance(status_node.value, int):
                code = status_node.value
                if code == v4_bad and v4_bad != 201:
                    assert False, f'create_{resource} still returns {v4_bad} — V4 not fixed'
                # Success path should return 201
                if code not in (400, 422):
                    assert code == 201, f'create_{resource} success path returns {code}, expected 201'
print('CREATE_STATUS_201')
\"" "create_not_returning_201"

# ── Check 12: V4 — Delete returns 204, no body ───────────────────────────────
check "python3 -c \"
import ast

with open('app.py') as f:
    src = f.read()
tree = ast.parse(src)

resource = '$RESOURCE'

delete_fn = None
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == f'delete_{resource}':
        delete_fn = node
        break

assert delete_fn is not None, f'delete_{resource} not found'

fn_src = ast.unparse(delete_fn) if hasattr(ast, 'unparse') else ''

# Must contain 204 status code on success path
assert '204' in fn_src, f'delete_{resource} does not return 204 — V4 not fixed'
print('DELETE_STATUS_204')
\"" "delete_not_returning_204"

# ── Check 13: V4 — 404 for not-found (not 200 or 500) ────────────────────────
check "python3 -c \"
import ast

with open('app.py') as f:
    src = f.read()
tree = ast.parse(src)

resource = '$RESOURCE'
v4_bad = int('$V4_BAD')

get_fn = None
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == f'get_{resource}':
        get_fn = node
        break

assert get_fn is not None, f'get_{resource} not found'

fn_src = ast.unparse(get_fn) if hasattr(ast, 'unparse') else ''

# Must have 404 in function
assert '404' in fn_src, f'get_{resource} does not return 404 for missing resource — V4 not fixed'
print('NOTFOUND_STATUS_404')
\"" "notfound_not_returning_404"

# ── Check 14: V6 — All error returns are JSON (no bare string errors) ─────────
check "python3 -c \"
import ast, re

with open('app.py') as f:
    src = f.read()
tree = ast.parse(src)

# Find all return statements with non-2xx status codes
# Each must call jsonify() — bare string constants are not allowed
issues = []
for node in ast.walk(tree):
    if isinstance(node, ast.Return) and node.value:
        val = node.value
        # Pattern: return 'some string', STATUS_CODE
        if isinstance(val, ast.Tuple) and len(val.elts) >= 2:
            body = val.elts[0]
            status = val.elts[-1]
            if isinstance(status, ast.Constant) and isinstance(status.value, int):
                code = status.value
                if code >= 400:
                    # Body must be a jsonify() call, not a bare string
                    if isinstance(body, ast.Constant) and isinstance(body.value, str):
                        issues.append(f'bare string error at status {code}: {body.value!r}')

assert not issues, f'Bare string error responses found (V6 not fixed): {issues}'
print('JSON_ERROR_SCHEMA_OK')
\"" "bare_string_errors_remain"

# ── Check 15: V6 — Error JSON has both 'error' and 'code' keys ────────────────
check "python3 -c \"
import re

with open('app.py') as f:
    src = f.read()

# All jsonify calls that appear in non-2xx return context should have both keys
# We search for jsonify({...}) patterns near error status codes
# Strategy: find all return jsonify({...}), STATUS patterns
import ast

tree = ast.parse(src)

error_returns = []
for node in ast.walk(tree):
    if isinstance(node, ast.Return) and node.value:
        val = node.value
        if isinstance(val, ast.Tuple) and len(val.elts) >= 2:
            body = val.elts[0]
            status = val.elts[-1]
            if isinstance(status, ast.Constant) and isinstance(status.value, int):
                if status.value >= 400:
                    body_src = ast.unparse(body) if hasattr(ast, 'unparse') else ''
                    error_returns.append((status.value, body_src))

for code, body_src in error_returns:
    # body_src should be a jsonify({...}) call containing 'error' and 'code' keys
    assert 'jsonify' in body_src, \
        f'Error return for {code} is not wrapped in jsonify(): {body_src}'
    assert \"'error'\" in body_src or '\"error\"' in body_src, \
        f'Error JSON for {code} missing \"error\" key: {body_src}'
    assert \"'code'\" in body_src or '\"code\"' in body_src, \
        f'Error JSON for {code} missing \"code\" key: {body_src}'

print(f'ERROR_SCHEMA_FIELDS_OK (checked {len(error_returns)} error returns)')
\"" "error_schema_missing_fields"

# ── Check 16: Attestation ──────────────────────────────────────────────────────
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
