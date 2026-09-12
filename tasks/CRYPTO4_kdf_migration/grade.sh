#!/usr/bin/env bash
# CRYPTO4 grader: verify Argon2id migration with backward compatibility
set -uo pipefail

WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
REPORTS="${2:-${REPORTS_DIR:-/reports}}"
SUBMISSION="${3:-/submission}"
TASK_DIR="${4:-/task}"

cd "$WORKSPACE"

pass=true
partial=0
total=12
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

# Install dependencies
# was: pip install (grade-time network fetch), replaced scripts/make_graders_hermetic.py
tb_require pytest argon2-cffi || true

# -------------------------------------------------------------------
# C1: pytest tests/ passes overall
# -------------------------------------------------------------------
if python -m pytest tests/ -q --tb=no 2>/dev/null; then
    check "C1" "pytest tests/ passes" "pass"
else
    check "C1" "pytest tests/ failed" "fail"
fi

# -------------------------------------------------------------------
# C2: New users get Argon2id hashes
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import sys, sqlite3
sys.path.insert(0, '.')
from auth_system.hasher import hash_password
h, fmt = hash_password("newpassword123")
assert h.startswith("argon2:"), f"New hash must be argon2: prefix, got {h[:30]}"
assert fmt == 3, f"New hash format must be 3 (Argon2id), got {fmt}"
sys.exit(0)
PYEOF
then
    check "C2" "New users receive Argon2id hashes" "pass"
else
    check "C2" "New users still receive MD5 hashes (hasher.py not updated)" "fail"
fi

# -------------------------------------------------------------------
# C3: Format 0 (plain MD5) users can log in
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import sys, hashlib
sys.path.insert(0, '.')
from auth_system.verifier import verify_password
from auth_system.formats import PLAIN_MD5
password = "legacypassword"
stored = "md5:" + hashlib.md5(password.encode()).hexdigest()
assert verify_password(password, stored, PLAIN_MD5), "Format 0 verification failed"
sys.exit(0)
PYEOF
then
    check "C3" "Format 0 (plain MD5) users can authenticate" "pass"
else
    check "C3" "Format 0 (plain MD5) authentication broken" "fail"
fi

# -------------------------------------------------------------------
# C4: Format 1 (salted MD5, HEX salt) users can log in
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import sys, hashlib
sys.path.insert(0, '.')
from auth_system.verifier import verify_password
from auth_system.formats import SALTED_MD5
password = "legacypassword"
salt_hex = "deadbeefcafe0123"
salt_bytes = bytes.fromhex(salt_hex)
h = hashlib.md5(salt_bytes + password.encode()).hexdigest()
stored = f"md5s:{salt_hex}:{h}"
assert verify_password(password, stored, SALTED_MD5), "Format 1 (hex-salt) verification failed"
sys.exit(0)
PYEOF
then
    check "C4" "Format 1 (salted MD5, hex salt) users can authenticate" "pass"
else
    check "C4" "Format 1 hex-salt bug not fixed (base64 decode instead of hex)" "fail"
fi

# -------------------------------------------------------------------
# C5: Format 2 (SHA256-HMAC, base64 salt) users can log in
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import sys, hashlib, hmac, base64
sys.path.insert(0, '.')
from auth_system.verifier import verify_password
from auth_system.formats import SHA256_HMAC
password = "legacypassword"
salt_bytes = b"testingsalt"
mac = hmac.new(salt_bytes, password.encode(), hashlib.sha256).digest()
stored = f"sha256h:{base64.b64encode(salt_bytes).decode()}:{base64.b64encode(mac).decode()}"
assert verify_password(password, stored, SHA256_HMAC), "Format 2 (SHA256-HMAC) verification failed"
sys.exit(0)
PYEOF
then
    check "C5" "Format 2 (SHA256-HMAC, base64 salt) users can authenticate" "pass"
else
    check "C5" "Format 2 SHA256-HMAC authentication broken" "fail"
fi

# -------------------------------------------------------------------
# C6: Hash upgrade happens on login (legacy -> Argon2id)
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import sys, sqlite3, hashlib
sys.path.insert(0, '.')
from auth_system.migrator import upgrade_hash
from auth_system.verifier import verify_password
from auth_system.formats import PLAIN_MD5, ARGON2ID

conn = sqlite3.connect(":memory:")
conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, hash_value TEXT, hash_format INTEGER)")
password = "upgradetest"
stored = "md5:" + hashlib.md5(password.encode()).hexdigest()
conn.execute("INSERT INTO users VALUES (1, 'u', ?, 0)", (stored,))
conn.commit()

upgrade_hash(1, password, conn)

row = conn.execute("SELECT hash_value, hash_format FROM users WHERE id=1").fetchone()
new_hash, new_fmt = row
assert new_hash.startswith("argon2:"), f"Upgraded hash must be argon2: prefix, got {new_hash[:30]}"
sys.exit(0)
PYEOF
then
    check "C6" "Hash upgraded to Argon2id after successful login" "pass"
else
    check "C6" "Hash upgrade to Argon2id not working" "fail"
fi

# -------------------------------------------------------------------
# C7: Format detection works for all 4 formats
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import sys
sys.path.insert(0, '.')
from auth_system.formats import detect_format, PLAIN_MD5, SALTED_MD5, SHA256_HMAC, ARGON2ID
assert detect_format("md5:abc123") == PLAIN_MD5
assert detect_format("md5s:deadbeef:abc123") == SALTED_MD5
assert detect_format("sha256h:dGVzdA==:abc123==") == SHA256_HMAC
assert detect_format("argon2:$argon2id$v=19$m=65536,t=2,p=1$abc$def") == ARGON2ID
sys.exit(0)
PYEOF
then
    check "C7" "Format detector identifies all 4 formats correctly" "pass"
else
    check "C7" "Format detection broken for one or more formats" "fail"
fi

# -------------------------------------------------------------------
# C8: After upgrade, hash_format updated to 3 (format marker bug)
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import sys, sqlite3, hashlib
sys.path.insert(0, '.')
from auth_system.migrator import upgrade_hash

conn = sqlite3.connect(":memory:")
conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, hash_value TEXT, hash_format INTEGER)")
password = "markertest"
stored = "md5:" + hashlib.md5(password.encode()).hexdigest()
conn.execute("INSERT INTO users VALUES (1, 'u', ?, 0)", (stored,))
conn.commit()

upgrade_hash(1, password, conn)

row = conn.execute("SELECT hash_format FROM users WHERE id=1").fetchone()
new_fmt = row[0]
assert new_fmt == 3, f"hash_format must be updated to 3 after upgrade, got {new_fmt}"
sys.exit(0)
PYEOF
then
    check "C8" "hash_format column updated to 3 (Argon2id) after upgrade" "pass"
else
    check "C8" "Format marker bug not fixed: hash_format not updated to 3 after upgrade" "fail"
fi

# -------------------------------------------------------------------
# C9: Second login after upgrade succeeds (format marker correct)
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import sys, sqlite3, hashlib
sys.path.insert(0, '.')
from auth_system.migrator import upgrade_hash
from auth_system.verifier import verify_password

conn = sqlite3.connect(":memory:")
conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, hash_value TEXT, hash_format INTEGER)")
password = "secondlogintest"
stored = "md5:" + hashlib.md5(password.encode()).hexdigest()
conn.execute("INSERT INTO users VALUES (1, 'u', ?, 0)", (stored,))
conn.commit()

# First login: upgrade
upgrade_hash(1, password, conn)

# Second login: read updated values and verify
row = conn.execute("SELECT hash_value, hash_format FROM users WHERE id=1").fetchone()
new_hash, new_fmt = row
assert verify_password(password, new_hash, new_fmt), \
    f"Second login failed after upgrade: fmt={new_fmt} hash={new_hash[:30]}"
sys.exit(0)
PYEOF
then
    check "C9" "Second login after upgrade succeeds (format marker correct)" "pass"
else
    check "C9" "Second login fails after upgrade (format marker bug still present)" "fail"
fi

# -------------------------------------------------------------------
# C10: New hashes do not use MD5
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import sys
sys.path.insert(0, '.')
from auth_system.hasher import hash_password
for pw in ["test1", "password123", "hunter2"]:
    h, fmt = hash_password(pw)
    assert not h.startswith("md5:"), f"New hash must not use MD5, got {h[:30]}"
    assert not h.startswith("md5s:"), f"New hash must not use salted MD5, got {h[:30]}"
sys.exit(0)
PYEOF
then
    check "C10" "New hashes do not use MD5 prefix" "pass"
else
    check "C10" "New hashes still use MD5 (hasher.py not fully migrated)" "fail"
fi

# -------------------------------------------------------------------
# C11: Syntax validity (all auth_system modules importable)
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import sys
sys.path.insert(0, '.')
import auth_system.formats
import auth_system.verifier
import auth_system.migrator
import auth_system.hasher
import auth_system.user_store
sys.exit(0)
PYEOF
then
    check "C11" "All auth_system modules import without syntax errors" "pass"
else
    check "C11" "Syntax error in one or more auth_system modules" "fail"
fi

# -------------------------------------------------------------------
# C12: Argon2id parameters are reasonable (time_cost >= 1, memory_cost >= 65536)
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import sys, ast
sys.path.insert(0, '.')

# Check migrator.py for PasswordHasher instantiation parameters
src = open('auth_system/migrator.py').read()
tree = ast.parse(src)

time_cost_ok = True
memory_cost_ok = True

for node in ast.walk(tree):
    if isinstance(node, ast.Call):
        func_name = ""
        if isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
        elif isinstance(node.func, ast.Name):
            func_name = node.func.id
        if "PasswordHasher" in func_name or (
            isinstance(node.func, ast.Attribute) and node.func.attr == "PasswordHasher"
        ):
            for kw in node.keywords:
                if kw.arg == "time_cost" and isinstance(kw.value, ast.Constant):
                    if kw.value.value < 1:
                        time_cost_ok = False
                if kw.arg == "memory_cost" and isinstance(kw.value, ast.Constant):
                    if kw.value.value < 65536:
                        memory_cost_ok = False

assert time_cost_ok, "time_cost must be >= 1"
assert memory_cost_ok, "memory_cost must be >= 65536 (64 MB)"
sys.exit(0)
PYEOF
then
    check "C12" "Argon2id parameters reasonable (time_cost>=1, memory_cost>=65536)" "pass"
else
    check "C12" "Argon2id parameters too weak or not set" "fail"
fi

# -------------------------------------------------------------------
# Run pytest (informational counts)
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
    "checks_correct": $partial,
    "total_checks": $total,
    "pytest_passed": ${pytest_pass:-0},
    "pytest_failed": ${pytest_fail:-0}
  },
  "failure_modes": [],
  "checklist": [$findings]
}
EOF

# hermetic-by: scripts/make_graders_hermetic.py
