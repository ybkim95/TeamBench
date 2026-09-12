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

# Load expected.json for seed-specific params
MAX_KEY_LEN=$(python3 -c "import json; print(json.load(open('$REPORTS/expected.json')).get('max_key_length', 64))" 2>/dev/null || echo 64)
MAX_VAL_SIZE=$(python3 -c "import json; print(json.load(open('$REPORTS/expected.json')).get('max_value_size', 1024))" 2>/dev/null || echo 1024)
MAX_KEYS=$(python3 -c "import json; print(json.load(open('$REPORTS/expected.json')).get('max_keys', 100))" 2>/dev/null || echo 100)

# ── MUST requirements (M1-M12) ──────────────────────────────────────────────

# M1: SET stores value
check "python3 -c \"
from protocol import KVStore
s = KVStore()
r = s.execute('SET foo bar')
assert 'OK' in r, f'SET should return OK, got {r}'
print('M1_PASS')
\"" "M1_set_fails"

# M2: GET returns value or ERR key_not_found
check "python3 -c \"
from protocol import KVStore
s = KVStore()
s.execute('SET mykey myval')
r = s.execute('GET mykey')
assert 'myval' in r, f'GET should return value, got {r}'
r2 = s.execute('GET missing')
assert 'ERR' in r2 and 'key_not_found' in r2, f'GET missing should return ERR key_not_found, got {r2}'
print('M2_PASS')
\"" "M2_get_fails"

# M3: DEL removes key or ERR key_not_found
check "python3 -c \"
from protocol import KVStore
s = KVStore()
s.execute('SET delme val')
r = s.execute('DEL delme')
assert 'OK' in r, f'DEL should return OK, got {r}'
r2 = s.execute('DEL delme')
assert 'ERR' in r2 and 'key_not_found' in r2, f'DEL missing should return ERR key_not_found, got {r2}'
print('M3_PASS')
\"" "M3_del_fails"

# M4: KEYS lists all keys with END
check "python3 -c \"
from protocol import KVStore
s = KVStore()
s.execute('SET alpha 1')
s.execute('SET beta 2')
r = s.execute('KEYS')
assert 'alpha' in r and 'beta' in r and 'END' in r, f'KEYS should list keys and END, got {r}'
print('M4_PASS')
\"" "M4_keys_fails"

# M5: COUNT returns number of keys
check "python3 -c \"
from protocol import KVStore
s = KVStore()
s.execute('SET a 1')
s.execute('SET b 2')
r = s.execute('COUNT')
assert 'COUNT 2' in r or 'COUNT  2' in r or r.strip() == '2', f'COUNT should return COUNT 2, got {r}'
print('M5_PASS')
\"" "M5_count_fails"

# M6: EXISTS returns TRUE/FALSE
check "python3 -c \"
from protocol import KVStore
s = KVStore()
s.execute('SET x 1')
r1 = s.execute('EXISTS x')
r2 = s.execute('EXISTS y')
assert 'TRUE' in r1, f'EXISTS x should return TRUE, got {r1}'
assert 'FALSE' in r2, f'EXISTS y should return FALSE, got {r2}'
print('M6_PASS')
\"" "M6_exists_fails"

# M7: FLUSH removes all keys
check "python3 -c \"
from protocol import KVStore
s = KVStore()
s.execute('SET a 1')
s.execute('SET b 2')
r = s.execute('FLUSH')
assert 'OK' in r, f'FLUSH should return OK, got {r}'
r2 = s.execute('COUNT')
assert '0' in r2, f'After FLUSH, COUNT should be 0, got {r2}'
print('M7_PASS')
\"" "M7_flush_fails"

# M8: OK for successful SET and DEL
check "python3 -c \"
from protocol import KVStore
s = KVStore()
r1 = s.execute('SET k v')
assert r1.strip() == 'OK' or r1.strip().startswith('OK'), f'SET should return OK, got {r1}'
r2 = s.execute('DEL k')
assert r2.strip() == 'OK' or r2.strip().startswith('OK'), f'DEL should return OK, got {r2}'
print('M8_PASS')
\"" "M8_ok_response_fails"

# M9: ERR unknown_command
check "python3 -c \"
from protocol import KVStore
s = KVStore()
r = s.execute('BOGUS xyz')
assert 'ERR' in r and 'unknown_command' in r, f'Unknown cmd should return ERR unknown_command, got {r}'
print('M9_PASS')
\"" "M9_unknown_cmd_fails"

# M10: ERR key_too_long
check "python3 -c \"
from protocol import KVStore
s = KVStore()
long_key = 'x' * ($MAX_KEY_LEN + 10)
r = s.execute(f'SET {long_key} val')
assert 'ERR' in r and 'key_too_long' in r, f'Long key should return ERR key_too_long, got {r}'
print('M10_PASS')
\"" "M10_key_too_long_fails"

# M11: ERR value_too_large
check "python3 -c \"
from protocol import KVStore
s = KVStore()
big_val = 'x' * ($MAX_VAL_SIZE + 10)
r = s.execute(f'SET k {big_val}')
assert 'ERR' in r and 'value_too_large' in r, f'Big value should return ERR value_too_large, got {r}'
print('M11_PASS')
\"" "M11_value_too_large_fails"

# M12: ERR store_full (but update existing key allowed)
check "python3 -c \"
from protocol import KVStore
s = KVStore()
# Fill to capacity
for i in range($MAX_KEYS):
    s.execute(f'SET key{i} val{i}')
# One more should fail
r = s.execute('SET overflow_key overflow_val')
assert 'ERR' in r and 'store_full' in r, f'Over capacity should return ERR store_full, got {r}'
# Updating existing should succeed
r2 = s.execute('SET key0 updated')
assert 'OK' in r2, f'Update existing at capacity should return OK, got {r2}'
print('M12_PASS')
\"" "M12_store_full_fails"

# ── SHOULD requirements (S1-S5) ─────────────────────────────────────────────

SHOULD_PASSED=0

# S1: MSET
S1_RESULT=$(python3 -c "
from protocol import KVStore
s = KVStore()
r = s.execute('MSET a 1 b 2 c 3')
ok = 'OK' in r and '3' in r
r2 = s.execute('GET a')
ok = ok and '1' in r2
print('PASS' if ok else 'FAIL')
" 2>/dev/null || echo "FAIL")
check "[ '$S1_RESULT' = 'PASS' ]" "S1_mset_fails"
[ "$S1_RESULT" = "PASS" ] && SHOULD_PASSED=$((SHOULD_PASSED + 1))

# S2: MGET
S2_RESULT=$(python3 -c "
from protocol import KVStore
s = KVStore()
s.execute('SET x 10')
s.execute('SET y 20')
r = s.execute('MGET x y z')
ok = '10' in r and '20' in r and 'NIL' in r and 'END' in r
print('PASS' if ok else 'FAIL')
" 2>/dev/null || echo "FAIL")
check "[ '$S2_RESULT' = 'PASS' ]" "S2_mget_fails"
[ "$S2_RESULT" = "PASS" ] && SHOULD_PASSED=$((SHOULD_PASSED + 1))

# S3+S4: TTL and SETEX
S3_RESULT=$(python3 -c "
from protocol import KVStore
import time
s = KVStore()
s.execute('SET perm val')
r = s.execute('TTL perm')
ok = '-1' in r
s.execute('SETEX temp 2 val2')
r2 = s.execute('TTL temp')
# TTL should be > 0
ok = ok and ('1' in r2 or '2' in r2)
print('PASS' if ok else 'FAIL')
" 2>/dev/null || echo "FAIL")
check "[ '$S3_RESULT' = 'PASS' ]" "S3_ttl_fails"
[ "$S3_RESULT" = "PASS" ] && SHOULD_PASSED=$((SHOULD_PASSED + 1))

S4_RESULT=$(python3 -c "
from protocol import KVStore
import time
s = KVStore()
s.execute('SETEX expkey 1 expval')
r = s.execute('GET expkey')
ok = 'expval' in r
time.sleep(1.5)
r2 = s.execute('GET expkey')
ok = ok and ('ERR' in r2 or 'key_not_found' in r2)
print('PASS' if ok else 'FAIL')
" 2>/dev/null || echo "FAIL")
check "[ '$S4_RESULT' = 'PASS' ]" "S4_setex_fails"
[ "$S4_RESULT" = "PASS" ] && SHOULD_PASSED=$((SHOULD_PASSED + 1))

# S5: APPEND
S5_RESULT=$(python3 -c "
from protocol import KVStore
s = KVStore()
s.execute('SET msg hello')
r = s.execute('APPEND msg _world')
ok = 'OK' in r and '11' in r
r2 = s.execute('GET msg')
ok = ok and 'hello_world' in r2
# APPEND on new key
r3 = s.execute('APPEND newkey fresh')
ok = ok and 'OK' in r3
r4 = s.execute('GET newkey')
ok = ok and 'fresh' in r4
print('PASS' if ok else 'FAIL')
" 2>/dev/null || echo "FAIL")
check "[ '$S5_RESULT' = 'PASS' ]" "S5_append_fails"
[ "$S5_RESULT" = "PASS" ] && SHOULD_PASSED=$((SHOULD_PASSED + 1))

# ── Check SHOULD threshold ──────────────────────────────────────────────────
check "[ $SHOULD_PASSED -ge 3 ]" "insufficient_should_requirements"

# ── Existing tests pass ─────────────────────────────────────────────────────
check "python3 -m pytest tests/test_protocol.py -q --tb=short 2>&1 | tail -1 | grep -qE 'passed|no tests ran'" "existing_tests_fail"

# ── Attestation ─────────────────────────────────────────────────────────────
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
  "secondary": {"checks_passed": $PASSED, "checks_total": $CHECKS, "partial_score": $PARTIAL, "should_passed": $SHOULD_PASSED},
  "failure_modes": $FM
}
JSON
