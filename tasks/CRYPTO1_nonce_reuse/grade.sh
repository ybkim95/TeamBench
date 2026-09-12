#!/usr/bin/env bash
# CRYPTO1 grader: verify 3 crypto bugs fixed + false positive preserved
set -uo pipefail

WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
REPORTS="${2:-${REPORTS_DIR:-/reports}}"
SUBMISSION="${3:-/submission}"
TASK_DIR="${4:-/task}"

cd "$WORKSPACE"

pass=true
partial=0
total=10
findings=""

check() {
    local id="$1"
    local desc="$2"
    local result="$3"
    if [ "$result" = "pass" ]; then
        partial=$((partial + 1))
        findings="${findings}{\"id\":\"${id}\",\"ok\":true,\"note\":\"${desc}\"},"
    else
        pass=false
        findings="${findings}{\"id\":\"${id}\",\"ok\":false,\"note\":\"${desc}\"},"
    fi
}

# Install dependencies if needed
# was: pip install (grade-time network fetch), replaced scripts/make_graders_hermetic.py
tb_require pytest cryptography || true

# -------------------------------------------------------------------
# C1: pytest tests/ passes overall
# -------------------------------------------------------------------
if python -m pytest tests/ -q --tb=no 2>/dev/null; then
    check "C1" "All pytest tests pass" "pass"
else
    check "C1" "pytest tests/ failed" "fail"
fi

# -------------------------------------------------------------------
# C2: nonce is 12 bytes (no struct.pack counter padding)
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys
src = open('crypto_service/nonce.py').read()
# Fail if struct.pack with a small format is used for nonce generation
if 'struct.pack' in src and ('>I' in src or '<I' in src or '>L' in src or '<L' in src):
    sys.exit(1)
# Must produce 12-byte nonces — check by instantiation
import importlib.util
spec = importlib.util.spec_from_file_location("nonce_mod", "crypto_service/nonce.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
# Find the NonceGenerator class
gen_cls = None
for name in dir(mod):
    obj = getattr(mod, name)
    if isinstance(obj, type) and 'nonce' in name.lower():
        gen_cls = obj
        break
if gen_cls is None:
    sys.exit(1)
g = gen_cls()
n = g.generate()
assert len(n) == 12, f"Expected 12 bytes, got {len(n)}"
sys.exit(0)
PYEOF
then
    check "C2" "Nonce is 12 bytes (no struct.pack counter)" "pass"
else
    check "C2" "Nonce is not 12 bytes or still uses struct.pack counter" "fail"
fi

# -------------------------------------------------------------------
# C3: nonce generation uses os.urandom (not counter-based)
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys
src = open('crypto_service/nonce.py').read()
tree = ast.parse(src)
# Check that os.urandom is called
has_urandom = 'os.urandom' in src or 'urandom' in src
# Check that counter-based pattern is gone
has_counter_pack = ('struct.pack' in src and
                    any(fmt in src for fmt in ['>I', '<I', '>L', '<L', '>Q', '<Q']))
if has_urandom and not has_counter_pack:
    sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C3" "Nonce generation uses os.urandom (not counter-based)" "pass"
else
    check "C3" "Nonce generation still counter-based or missing os.urandom" "fail"
fi

# -------------------------------------------------------------------
# C4: test_nonce_collision.py passes (100K nonces are unique)
# -------------------------------------------------------------------
if python -m pytest tests/test_nonce_collision.py -q --tb=no 2>/dev/null; then
    check "C4" "Nonce collision test passes (100K nonces unique)" "pass"
else
    check "C4" "Nonce collision test failed (nonces not unique)" "fail"
fi

# -------------------------------------------------------------------
# C5: PBKDF2 iterations >= 100000 (source check)
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import re, sys
src = open('crypto_service/key_derivation.py').read()
iters = [int(x) for x in re.findall(r'iterations\s*=\s*(\d+)', src)]
if not iters:
    # Also check positional argument style: pbkdf2_hmac('sha256', ..., salt, 100000)
    # Match 5th or 6th numeric arg to pbkdf2_hmac
    iters = [int(x) for x in re.findall(r'pbkdf2_hmac\s*\([^)]*?(\d{6,})', src)]
if any(i >= 100000 for i in iters):
    sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C5" "PBKDF2 uses >= 100000 iterations" "pass"
else
    check "C5" "PBKDF2 iterations still too low (< 100000)" "fail"
fi

# -------------------------------------------------------------------
# C6: test_key_strength.py passes
# -------------------------------------------------------------------
if python -m pytest tests/test_key_strength.py -q --tb=no 2>/dev/null; then
    check "C6" "Key strength test passes (>= 100000 iterations verified)" "pass"
else
    check "C6" "Key strength test failed" "fail"
fi

# -------------------------------------------------------------------
# C7: GCM tag length is 16 bytes (no 8-byte truncation)
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys
src = open('crypto_service/encryption.py').read()
# Fail if tag is sliced to 8 bytes
if '[-8:]' in src or '[-16:-8]' in src or 'tag_length=8' in src or 'tag_len=8' in src:
    sys.exit(1)
# Verify by instantiation: encrypt and check tag size
import importlib.util, sys as _sys
spec = importlib.util.spec_from_file_location("enc_mod", "crypto_service/encryption.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
svc_cls = None
for name in dir(mod):
    obj = getattr(mod, name)
    if isinstance(obj, type) and 'encrypt' in name.lower():
        svc_cls = obj
        break
if svc_cls is None:
    _sys.exit(1)
import os
key = os.urandom(32)
nonce = os.urandom(12)
svc = svc_cls()
ciphertext, tag = svc.encrypt(key, b"test plaintext data", nonce)
assert len(tag) == 16, f"Tag must be 16 bytes, got {len(tag)}"
_sys.exit(0)
PYEOF
then
    check "C7" "GCM auth tag is full 16 bytes (no truncation)" "pass"
else
    check "C7" "GCM auth tag is still truncated (not 16 bytes)" "fail"
fi

# -------------------------------------------------------------------
# C8: test_tag_integrity.py passes
# -------------------------------------------------------------------
if python -m pytest tests/test_tag_integrity.py -q --tb=no 2>/dev/null; then
    check "C8" "Tag integrity test passes (16-byte tag verified)" "pass"
else
    check "C8" "Tag integrity test failed" "fail"
fi

# -------------------------------------------------------------------
# C9: utils.py unchanged — salt still uses os.urandom (false positive preserved)
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys
src = open('crypto_service/utils.py').read()
tree = ast.parse(src)
# Must still contain os.urandom call in generate_salt
has_urandom = 'os.urandom' in src
# Must not have been replaced with secrets.token_bytes or similar that changes semantics
# (os.urandom is correct — we just verify it was not removed)
if has_urandom:
    sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C9" "utils.py preserved: salt still uses os.urandom (correct)" "pass"
else
    check "C9" "utils.py incorrectly modified: os.urandom removed from salt generation" "fail"
fi

# -------------------------------------------------------------------
# C10: Syntax validity — all crypto_service modules parse cleanly
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys, os
modules = [
    'crypto_service/nonce.py',
    'crypto_service/key_derivation.py',
    'crypto_service/encryption.py',
    'crypto_service/utils.py',
]
for path in modules:
    if not os.path.exists(path):
        print(f"Missing: {path}", file=sys.stderr)
        sys.exit(1)
    try:
        ast.parse(open(path).read())
    except SyntaxError as e:
        print(f"SyntaxError in {path}: {e}", file=sys.stderr)
        sys.exit(1)
sys.exit(0)
PYEOF
then
    check "C10" "All crypto_service modules have valid syntax" "pass"
else
    check "C10" "Syntax error in one or more crypto_service modules" "fail"
fi

# -------------------------------------------------------------------
# Collect pytest summary
# -------------------------------------------------------------------
pytest_out=$(python -m pytest tests/ -q --tb=no 2>&1 || true)
pytest_pass=$(echo "$pytest_out" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' || echo "0")
pytest_fail=$(echo "$pytest_out" | grep -oE '[0-9]+ failed' | grep -oE '[0-9]+' || echo "0")

partial_score=$(awk "BEGIN {printf \"%.4f\", $partial / $total}")
findings="${findings%,}"  # Remove trailing comma

cat > "${REPORTS}/score.json" <<EOF
{
  "pass": $( [ "$pass" = "true" ] && echo "true" || echo "false" ),
  "secondary": {
    "partial_score": $partial_score,
    "checks_passed": $partial,
    "total_checks": $total,
    "pytest_passed": ${pytest_pass:-0},
    "pytest_failed": ${pytest_fail:-0}
  },
  "failure_modes": [],
  "checklist": [$findings]
}
EOF

# hermetic-by: scripts/make_graders_hermetic.py
