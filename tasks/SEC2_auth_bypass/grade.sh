#!/usr/bin/env bash
set -o pipefail
WORKSPACE="$1"; REPORTS="$2"; SUBMISSION="$3"; TASK_DIR="$4"

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

# 1. All Python files are syntactically valid
check "python3 -c \"
import py_compile, os
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d != '__pycache__']
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            py_compile.compile(path, doraise=True)
print('SYNTAX_OK')
\"" "syntax_error"

# 2. JWT decode now validates expiry (verify_exp must not be False)
check "python3 -c \"
with open('auth.py') as f:
    code = f.read()
import ast
tree = ast.parse(code)
# Walk all keyword arguments to jwt.decode calls
class JwtDecodeVisitor(ast.NodeVisitor):
    def __init__(self):
        self.bad = False
    def visit_Call(self, node):
        # Detect jwt.decode(...)
        is_jwt_decode = False
        if isinstance(node.func, ast.Attribute) and node.func.attr == 'decode':
            is_jwt_decode = True
        elif isinstance(node.func, ast.Name) and node.func.id == 'decode':
            is_jwt_decode = True
        if is_jwt_decode:
            for kw in node.keywords:
                if kw.arg == 'options' and isinstance(kw.value, ast.Dict):
                    for k, v in zip(kw.value.keys, kw.value.values):
                        key = k.s if isinstance(k, ast.Constant) else (k.value if hasattr(k, 'value') else '')
                        if key == 'verify_exp':
                            val = v.value if isinstance(v, ast.Constant) else None
                            if val is False:
                                self.bad = True
        self.generic_visit(node)

v = JwtDecodeVisitor()
v.visit(tree)
assert not v.bad, 'jwt.decode still passes verify_exp=False'
# Belt-and-suspenders: grep source for the pattern without quoting issues
import re
assert not re.search(r'verify_exp[^:]*:[^F]*False', code), 'verify_exp False still in source'
print('JWT_EXPIRY_FIXED')
\"" "jwt_expiry_not_validated"

# 3. Admin endpoint checks user role before allowing access
check "python3 -c \"
with open('routes.py') as f:
    code = f.read()
import ast, re
tree = ast.parse(code)
# Find function containing 'admin' in its name
admin_funcs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and 'admin' in n.name]
assert len(admin_funcs) >= 1, 'No admin function found'
admin_src = ast.get_source_segment(code, admin_funcs[0])
# Must reference a role/access_level/tier field from user_data
has_role_check = bool(re.search(r'user_data\[.*(role|access_level|tier).*\]', admin_src or ''))
# Also accept: user_data.get('role') style
has_role_get  = bool(re.search(r'user_data\.get\(.*(role|access_level|tier)', admin_src or ''))
assert has_role_check or has_role_get, 'Admin function does not check role in user_data'
# Must return 403 on failure
assert '403' in (admin_src or ''), 'Admin function does not return 403 for unauthorized access'
print('ADMIN_ROLE_CHECK_PRESENT')
\"" "admin_missing_role_check"

# 4. Password reset token is invalidated after use
check "python3 -c \"
with open('routes.py') as f:
    code = f.read()
import ast, re
tree = ast.parse(code)
# Find confirm_password_reset function
reset_funcs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and 'confirm' in n.name and 'reset' in n.name]
assert len(reset_funcs) >= 1, 'No confirm_password_reset function found'
fn_src = ast.get_source_segment(code, reset_funcs[0]) or ''
# Must have a deletion: del store[token], store.pop(token), invalidate_reset_token(token)
has_del       = bool(re.search(r'del\s+\w+\[token\]', fn_src))
has_pop       = bool(re.search(r'\w+\.pop\(token', fn_src))
has_invalidate = 'invalidate_reset_token' in fn_src and 'TODO' not in fn_src.split('invalidate_reset_token')[0].rsplit('\n', 1)[-1]
assert has_del or has_pop or has_invalidate, 'Reset token not invalidated after use'
# The TODO comment must be gone or replaced with actual code
assert '# TODO: clean up used tokens' not in fn_src, 'TODO placeholder still present instead of real invalidation'
print('RESET_TOKEN_INVALIDATED')
\"" "reset_token_not_invalidated"

# 5. JWT secret loaded from environment (not hardcoded)
check "python3 -c \"
with open('auth.py') as f:
    code = f.read()
import ast, re
# Must use os.environ or os.getenv
assert 'os.environ' in code or 'os.getenv' in code, 'JWT secret not loaded from environment'
# Must NOT contain a naked string assignment like SECRET = 'changeme-dev-secret' as the sole value
# (having it as a fallback default is fine)
# Key check: the actual variable holding the secret must reference os.environ/os.getenv
has_env_load = bool(re.search(r'=\s*os\.environ(?:\.get)?\s*\(', code))
has_getenv   = bool(re.search(r'=\s*os\.getenv\s*\(', code))
assert has_env_load or has_getenv, 'JWT secret not dynamically loaded from env'
print('JWT_SECRET_ENV_OK')
\"" "jwt_secret_hardcoded"

# 6. No new dangerous calls introduced
check "python3 -c \"
import os
for fname in ('auth.py', 'routes.py', 'models.py'):
    with open(fname) as f:
        code = f.read()
    assert 'eval(' not in code, f'eval() found in {fname}'
    assert 'exec(' not in code, f'exec() found in {fname}'
    assert '__import__' not in code, f'__import__ found in {fname}'
print('NO_NEW_VULNS')
\"" "new_vulnerability_introduced"

# 7. Original non-auth routes still present
check "python3 -c \"
import ast
with open('routes.py') as f:
    code = f.read()
tree = ast.parse(code)
func_names = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
# Must have at least one list route, one detail route, one admin route, two reset routes
list_funcs   = [n for n in func_names if n.startswith('list_') or n.startswith('get_')]
admin_funcs  = [n for n in func_names if 'admin' in n]
reset_funcs  = [n for n in func_names if 'reset' in n]
assert len(list_funcs) >= 2,  f'Expected list+detail routes, got: {list_funcs}'
assert len(admin_funcs) >= 1, f'Expected admin route, got: {admin_funcs}'
assert len(reset_funcs) >= 2, f'Expected 2 reset routes, got: {reset_funcs}'
print('ROUTES_PRESENT')
\"" "routes_missing"

# 8. requirements.txt includes PyJWT
check "python3 -c \"
with open('requirements.txt') as f:
    reqs = f.read().lower()
assert 'pyjwt' in reqs, 'PyJWT not in requirements.txt'
print('REQUIREMENTS_OK')
\"" "requirements_missing_pyjwt"

# 9. @require_auth decorator still applied to protected endpoints
check "python3 -c \"
with open('routes.py') as f:
    code = f.read()
import re
# Count @require_auth decorators
decorators = re.findall(r'@require_auth', code)
assert len(decorators) >= 3, f'Expected at least 3 @require_auth decorators, found {len(decorators)}'
print('AUTH_DECORATORS_OK')
\"" "auth_decorator_missing"

# 10. Attestation check
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
