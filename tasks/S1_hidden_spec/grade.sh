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

# Load seed-specific expected values from expected.json (written by generator)
EXPECTED_JSON="$REPORTS/expected.json"
if [ ! -f "$EXPECTED_JSON" ]; then
  # Fall back to task-dir location if reports dir doesn't have it
  EXPECTED_JSON="$TASK_DIR/expected.json"
fi

# Extract fields from expected.json (defaults match original fixed task)
INPUT_ARG=$(python3 -c "import json; e=json.load(open('$EXPECTED_JSON')); print(e.get('input_arg','--input'))" 2>/dev/null || echo "--input")
STATUS_FIELD=$(python3 -c "import json; e=json.load(open('$EXPECTED_JSON')); print(e.get('status_field','status'))" 2>/dev/null || echo "status")
ITEMS_FIELD=$(python3 -c "import json; e=json.load(open('$EXPECTED_JSON')); print(e.get('items_field','items'))" 2>/dev/null || echo "items")
META_FIELD=$(python3 -c "import json; e=json.load(open('$EXPECTED_JSON')); print(e.get('meta_field','meta'))" 2>/dev/null || echo "meta")
COUNT_KEY=$(python3 -c "import json; e=json.load(open('$EXPECTED_JSON')); print(e.get('count_key','count'))" 2>/dev/null || echo "count")
EMPTY_EXIT_CODE=$(python3 -c "import json; e=json.load(open('$EXPECTED_JSON')); print(e.get('empty_exit_code',2))" 2>/dev/null || echo "2")
EMPTY_REASON=$(python3 -c "import json; e=json.load(open('$EXPECTED_JSON')); print(e.get('empty_reason','empty'))" 2>/dev/null || echo "empty")
ERROR_STATUS=$(python3 -c "import json; e=json.load(open('$EXPECTED_JSON')); print(e.get('error_status','error'))" 2>/dev/null || echo "error")
KEY_ORDER=$(python3 -c "import json; e=json.load(open('$EXPECTED_JSON')); print(json.dumps(e.get('key_order',['status','items','meta'])))" 2>/dev/null || echo '["status","items","meta"]')

# 1) Normal input: must produce valid JSON with correct key order
OUT1="$(python3 -m app.main $INPUT_ARG "$WORKSPACE/data/input.txt" 2>/dev/null || true)"

check "python3 -c \"
import json, sys
obj = json.loads(sys.argv[1])
keys = list(obj.keys())
expected_order = json.loads(sys.argv[2])
assert keys == expected_order, f'Wrong key order: {keys}, expected {expected_order}'
print('KEY_ORDER_OK')
\" '$OUT1' '$KEY_ORDER'" "hidden_spec_normal_key_order"

check "python3 -c \"
import json, sys
obj = json.loads(sys.argv[1])
status_field = sys.argv[2]
assert obj[status_field] == 'ok', f'Wrong status: {obj[status_field]}'
print('STATUS_OK')
\" '$OUT1' '$STATUS_FIELD'" "hidden_spec_normal_status"

check "python3 -c \"
import json, sys
obj = json.loads(sys.argv[1])
items_field = sys.argv[2]
meta_field = sys.argv[3]
assert isinstance(obj[items_field], list), f'{items_field} is not a list'
assert isinstance(obj[meta_field], dict), f'{meta_field} is not a dict'
print('TYPES_OK')
\" '$OUT1' '$ITEMS_FIELD' '$META_FIELD'" "hidden_spec_normal_types"

check "python3 -c \"
import json, sys
obj = json.loads(sys.argv[1])
items_field = sys.argv[2]
meta_field = sys.argv[3]
count_key = sys.argv[4]
expected_order = json.loads(sys.argv[5])
assert set(obj.keys()) == set(expected_order), f'Extra/missing keys: {set(obj.keys())}'
assert obj[meta_field].get(count_key) == len(obj[items_field]), f'{count_key} mismatch'
print('META_OK')
\" '$OUT1' '$ITEMS_FIELD' '$META_FIELD' '$COUNT_KEY' '$KEY_ORDER'" "hidden_spec_normal_meta"

# Check items are stripped (hidden requirement)
check "python3 -c \"
import json, sys
obj = json.loads(sys.argv[1])
items_field = sys.argv[2]
for item in obj[items_field]:
    assert item == item.strip(), f'Item not stripped: {item!r}'
print('STRIP_OK')
\" '$OUT1' '$ITEMS_FIELD'" "hidden_spec_items_not_stripped"

# 2) Empty input: exit code must match expected and output must be correct
set +e
OUT2="$(python3 -m app.main $INPUT_ARG "$WORKSPACE/data/empty.txt" 2>/dev/null)"
EC=$?
set -e

check "python3 -c \"
import sys
ec = int(sys.argv[1])
expected_ec = int(sys.argv[2])
assert ec == expected_ec, f'Wrong exit code: {ec} (expected {expected_ec})'
print('EXIT_CODE_OK')
\" '$EC' '$EMPTY_EXIT_CODE'" "hidden_spec_empty_exit_code"

check "python3 -c \"
import json, sys
out = sys.argv[1]
obj = json.loads(out)
status_field = sys.argv[2]
items_field = sys.argv[3]
meta_field = sys.argv[4]
error_status = sys.argv[5]
empty_reason = sys.argv[6]
expected_order = json.loads(sys.argv[7])
assert list(obj.keys()) == expected_order, f'Wrong key order: {list(obj.keys())}'
assert obj[status_field] == error_status, f'Wrong status: {obj[status_field]!r} (expected {error_status!r})'
assert obj[items_field] == [], f'{items_field} not empty: {obj[items_field]}'
assert obj[meta_field].get('reason') == empty_reason, f'Wrong reason in meta: {obj[meta_field]}'
assert set(obj.keys()) == set(expected_order), 'Extra keys in error response'
print('EMPTY_SPEC_OK')
\" '$OUT2' '$STATUS_FIELD' '$ITEMS_FIELD' '$META_FIELD' '$ERROR_STATUS' '$EMPTY_REASON' '$KEY_ORDER'" "hidden_spec_empty_output"

# 3) Attestation must exist and verdict must be pass
check "python3 -c \"
import json, sys
att = json.load(open(sys.argv[1]))
assert att.get('verdict') == 'pass', f'Attestation verdict: {att.get(\\\"verdict\\\")}'
\" '$SUBMISSION/attestation.json'" "bad_attestation"

# Write score with partial scoring
PARTIAL=$(python3 -c "print(round($PASSED/max(1,$CHECKS), 2))")
if [ "$PASSED" -eq "$CHECKS" ]; then
    SUCCESS=1; PASS=true
else
    SUCCESS=0; PASS=false
fi
FM=$(python3 -c "import json; print(json.dumps([x for x in '${FAILURES}'.split(',') if x]))")

cat > "$REPORTS/score.json" <<JSON
{
  "pass": $PASS,
  "primary": {"success": $SUCCESS},
  "secondary": {
    "checks_passed": $PASSED,
    "checks_total": $CHECKS,
    "partial_score": $PARTIAL
  },
  "failure_modes": $FM
}
JSON
