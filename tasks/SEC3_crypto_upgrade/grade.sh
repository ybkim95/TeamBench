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

# 2. No MD5 used in active code paths in crypto_utils.py
check "python3 -c \"
import ast, re
with open('crypto_utils.py') as f:
    source = f.read()
tree = ast.parse(source)

class DeprecatedMD5Visitor(ast.NodeVisitor):
    def __init__(self):
        self.bad_calls = []
    def visit_Call(self, node):
        # Detect hashlib.md5(...) calls
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == 'md5':
                self.bad_calls.append(node.lineno)
        # Detect md5(...) direct calls
        elif isinstance(node.func, ast.Name):
            if node.func.id == 'md5':
                self.bad_calls.append(node.lineno)
        self.generic_visit(node)

v = DeprecatedMD5Visitor()
v.visit(tree)
if v.bad_calls:
    # Allow if only in comments — check the actual source lines
    lines = source.splitlines()
    active_md5 = []
    for lineno in v.bad_calls:
        line = lines[lineno - 1].strip()
        if not line.startswith('#'):
            active_md5.append(lineno)
    assert not active_md5, f'hashlib.md5() still used in active code at lines: {active_md5}'
print('NO_MD5_IN_ACTIVE_CODE')
\"" "md5_still_used"

# 3. No SHA-1 used as primary primitive in crypto_utils.py
check "python3 -c \"
import ast
with open('crypto_utils.py') as f:
    source = f.read()
tree = ast.parse(source)

class SHA1Visitor(ast.NodeVisitor):
    def __init__(self):
        self.bad_calls = []
    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute) and node.func.attr == 'sha1':
            self.bad_calls.append(node.lineno)
        elif isinstance(node.func, ast.Name) and node.func.id == 'sha1':
            self.bad_calls.append(node.lineno)
        self.generic_visit(node)

v = SHA1Visitor()
v.visit(tree)
lines = source.splitlines()
active_sha1 = [
    ln for ln in v.bad_calls
    if not lines[ln - 1].strip().startswith('#')
]
assert not active_sha1, f'hashlib.sha1() still used in active code at lines: {active_sha1}'
print('NO_SHA1_IN_ACTIVE_CODE')
\"" "sha1_still_used"

# 4. No DES or RC4 (ARC4) usage in crypto_utils.py
check "python3 -c \"
import re
with open('crypto_utils.py') as f:
    source = f.read()
lines = source.splitlines()
bad_lines = []
for i, line in enumerate(lines, 1):
    stripped = line.strip()
    if stripped.startswith('#'):
        continue
    # Detect DES.new, ARC4.new, MODE_ECB in active code
    if re.search(r'DES\.new|ARC4\.new|MODE_ECB|from Crypto\.Cipher import DES|from Crypto\.Cipher import ARC4', stripped):
        bad_lines.append((i, stripped))
assert not bad_lines, f'Deprecated cipher (DES/RC4/ECB) still in active code: {bad_lines}'
print('NO_DES_RC4_ECB')
\"" "des_rc4_ecb_still_used"

# 5. Modern algorithm present — must use SHA-256, AES-GCM, PBKDF2, HMAC, or scrypt
check "python3 -c \"
import re
with open('crypto_utils.py') as f:
    source = f.read()
# Must contain at least one of these modern primitives
modern_patterns = [
    r'pbkdf2_hmac',
    r'scrypt',
    r'argon2',
    r'MODE_GCM',
    r'MODE_CCM',
    r'hmac\.new',
    r'sha256',
    r'SHA256',
    r'Scrypt',
    r'PBKDF2',
]
found = [p for p in modern_patterns if re.search(p, source)]
assert found, f'No modern crypto primitive found in crypto_utils.py. Expected one of: {modern_patterns}'
print(f'MODERN_ALGO_PRESENT: {found}')
\"" "no_modern_algo"

# 6. Key derivation uses proper KDF — not raw hash output as key material
check "python3 -c \"
import ast, re
with open('crypto_utils.py') as f:
    source = f.read()
tree = ast.parse(source)

# Find derive_key function
derive_funcs = [
    n for n in ast.walk(tree)
    if isinstance(n, ast.FunctionDef) and 'derive' in n.name.lower() and 'key' in n.name.lower()
]
if not derive_funcs:
    # No derive_key — check that no raw hash is used as key anywhere
    raw_key_pattern = re.search(r'hashlib\.(md5|sha1)\([^)]*\)\.digest\(\)', source)
    assert not raw_key_pattern, 'Raw md5/sha1 digest used as key material'
    print('KEY_DERIVATION_OK: no derive_key but no raw hash keys either')
else:
    fn_src = ast.get_source_segment(source, derive_funcs[0]) or ''
    # Must NOT use raw md5/sha1 digest as the returned key
    has_raw_md5_key = bool(re.search(r'hashlib\.md5\([^)]*\)\.digest\(\)', fn_src))
    has_raw_sha1_key = bool(re.search(r'hashlib\.sha1\([^)]*\)\.digest\(\)', fn_src))
    assert not has_raw_md5_key, 'derive_key() uses raw md5 hash as key (must use PBKDF2/scrypt/argon2)'
    assert not has_raw_sha1_key, 'derive_key() uses raw sha1 hash as key (must use PBKDF2/scrypt/argon2)'
    # Must use a proper KDF
    has_pbkdf2 = 'pbkdf2_hmac' in fn_src
    has_scrypt  = 'scrypt' in fn_src
    has_argon2  = 'argon2' in fn_src.lower()
    assert has_pbkdf2 or has_scrypt or has_argon2, \
        'derive_key() must use pbkdf2_hmac, scrypt, or argon2 — not raw hash'
    print('KEY_DERIVATION_OK: proper KDF in derive_key()')
\"" "key_derivation_raw_hash"

# 7. AES mode must NOT be ECB (if AES is present, it must use GCM or CCM)
check "python3 -c \"
import re
with open('crypto_utils.py') as f:
    source = f.read()
lines = source.splitlines()
ecb_lines = []
for i, line in enumerate(lines, 1):
    stripped = line.strip()
    if stripped.startswith('#'):
        continue
    if 'MODE_ECB' in stripped:
        ecb_lines.append((i, stripped))
assert not ecb_lines, f'AES ECB mode still in active code: {ecb_lines}'
print('NO_ECB_MODE')
\"" "aes_ecb_mode_present"

# 8. Backward compatibility bridge present (old-format data can still be read)
check "python3 -c \"
import re
# Check for backward compat markers in storage.py, crypto_utils.py, or migrate.py
compat_patterns = [
    r'_legacy',
    r'_v1',
    r'_v2',
    r'_crypto_version',
    r'old.format',
    r'legacy.format',
    r'backward.compat',
    r'migrate',
    r'fallback',
]
found_compat = False
for fname in ('storage.py', 'crypto_utils.py', 'migrate.py'):
    try:
        with open(fname) as f:
            source = f.read()
        if any(re.search(p, source, re.IGNORECASE) for p in compat_patterns):
            found_compat = True
            break
    except FileNotFoundError:
        pass
assert found_compat, 'No backward compatibility bridge found (look for migration/version/legacy markers)'
print('BACKWARD_COMPAT_BRIDGE_PRESENT')
\"" "no_backward_compat"

# 9. Migration order correct in migrate.py (key_derivation before storage before api)
check "python3 -c \"
with open('migrate.py') as f:
    source = f.read()
import re

# Find positions of the three migration phases in run_migration or the file overall
# Accept various naming conventions
kd_pos = -1; st_pos = -1; ap_pos = -1

patterns_kd = [r'key.deriv', r'kdf', r'Step 1', r'\[1/']
patterns_st = [r'storage', r'store', r'Step 2', r'\[2/']
patterns_ap = [r'api', r'API', r'Step 3', r'\[3/']

for p in patterns_kd:
    m = re.search(p, source, re.IGNORECASE)
    if m and kd_pos == -1:
        kd_pos = m.start()

for p in patterns_st:
    m = re.search(p, source, re.IGNORECASE)
    if m and st_pos == -1:
        st_pos = m.start()

for p in patterns_ap:
    m = re.search(p, source, re.IGNORECASE)
    if m and ap_pos == -1:
        ap_pos = m.start()

assert kd_pos != -1, 'migrate.py does not reference key derivation step'
assert st_pos != -1, 'migrate.py does not reference storage step'
assert ap_pos != -1, 'migrate.py does not reference API step'
assert kd_pos < st_pos, f'Key derivation step ({kd_pos}) must come before storage step ({st_pos})'
assert st_pos < ap_pos, f'Storage step ({st_pos}) must come before API step ({ap_pos})'
print('MIGRATION_ORDER_CORRECT')
\"" "migration_order_wrong"

# 10. No new dangerous primitives introduced (no eval, exec, hardcoded keys)
check "python3 -c \"
import re
for fname in ('crypto_utils.py', 'storage.py', 'api.py', 'migrate.py'):
    try:
        with open(fname) as f:
            code = f.read()
    except FileNotFoundError:
        continue
    assert 'eval(' not in code, f'eval() found in {fname}'
    assert 'exec(' not in code, f'exec() found in {fname}'
    # Must not introduce new hardcoded keys (anything that looks like a raw secret)
    # Allow the env fallback pattern 'default-dev-key' but not new naked hex strings
    naked_key = re.search(r'key\s*=\s*[\"\\']([0-9a-f]{32,64})[\"\\']', code)
    assert not naked_key, f'Hardcoded key material found in {fname}: {naked_key.group(0) if naked_key else \"\"}'
print('NO_NEW_VULNS')
\"" "new_vulnerability_introduced"

# 11. migrate.py actually implements migration (not just stubs)
check "python3 -c \"
with open('migrate.py') as f:
    source = f.read()
import re

# Count TODO markers — too many means implementation was not done
todo_count = len(re.findall(r'#\s*TODO', source))
# Count lines with actual logic (non-comment, non-blank, not just 'pass')
logic_lines = [
    l for l in source.splitlines()
    if l.strip() and not l.strip().startswith('#') and l.strip() != 'pass'
]
assert len(logic_lines) >= 15, f'migrate.py appears mostly stubbed ({len(logic_lines)} logic lines)'
assert todo_count <= 2, f'migrate.py still has {todo_count} TODO stubs (expected ≤2 after implementation)'
print(f'MIGRATE_IMPLEMENTED: {len(logic_lines)} logic lines, {todo_count} TODOs')
\"" "migrate_still_stubbed"

# 12. API endpoints still present after migration (no regression)
check "python3 -c \"
import ast
with open('api.py') as f:
    source = f.read()
tree = ast.parse(source)
func_names = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
# Must have at least create, get, and list endpoints
has_create = any('create' in n or 'post' in n.lower() for n in func_names)
has_get    = any('get' in n for n in func_names)
has_list   = any('list' in n for n in func_names)
assert has_create or len(func_names) >= 2, f'API endpoints missing after migration. Found: {func_names}'
print(f'API_ENDPOINTS_OK: {func_names}')
\"" "api_regression"

# 13. requirements.txt includes cryptography or pycryptodome for modern primitives
check "python3 -c \"
with open('requirements.txt') as f:
    reqs = f.read().lower()
has_cryptography = 'cryptography' in reqs
has_pycryptodome = 'pycryptodome' in reqs or 'pycryptodomex' in reqs
assert has_cryptography or has_pycryptodome, \
    'requirements.txt missing cryptography or pycryptodome for modern crypto primitives'
print('REQUIREMENTS_OK')
\"" "requirements_missing_crypto"

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
