#!/usr/bin/env bash
set -euo pipefail
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

# 1) Normal input: must produce valid JSON with correct key order
OUT1="$(python -m app.main --input "$WORKSPACE/data/input.txt" 2>/dev/null || true)"

check "python3 -c \"
import json, sys
obj = json.loads(sys.argv[1])
keys = list(obj.keys())
assert keys == ['status', 'items', 'meta'], f'Wrong key order: {keys}'
print('KEY_ORDER_OK')
\" '$OUT1'" "hidden_spec_normal_key_order"

check "python3 -c \"
import json, sys
obj = json.loads(sys.argv[1])
assert obj['status'] == 'ok', f'Wrong status: {obj[\"status\"]}'
print('STATUS_OK')
\" '$OUT1'" "hidden_spec_normal_status"

check "python3 -c \"
import json, sys
obj = json.loads(sys.argv[1])
assert isinstance(obj['items'], list), 'items is not a list'
assert isinstance(obj['meta'], dict), 'meta is not a dict'
print('TYPES_OK')
\" '$OUT1'" "hidden_spec_normal_types"

check "python3 -c \"
import json, sys
obj = json.loads(sys.argv[1])
assert set(obj.keys()) == {'status', 'items', 'meta'}, f'Extra keys: {set(obj.keys())}'
assert obj['meta'].get('count') == len(obj['items']), 'count mismatch'
print('META_OK')
\" '$OUT1'" "hidden_spec_normal_meta"

# 2) Empty input: exit code must be 2 and exact json
set +e
OUT2="$(python -m app.main --input "$WORKSPACE/data/empty.txt" 2>/dev/null)"
EC=$?
set -e

check "python3 -c \"
import sys
ec = int(sys.argv[1])
assert ec == 2, f'Wrong exit code: {ec} (expected 2)'
print('EXIT_CODE_OK')
\" '$EC'" "hidden_spec_empty_exit_code"

check "python3 -c \"
import json, sys
out = sys.argv[1]
obj = json.loads(out)
assert list(obj.keys()) == ['status', 'items', 'meta'], f'Wrong key order: {list(obj.keys())}'
assert obj['status'] == 'error', f'Wrong status: {obj[\"status\"]}'
assert obj['items'] == [], f'items not empty: {obj[\"items\"]}'
assert obj['meta'].get('reason') == 'empty', f'Wrong meta: {obj[\"meta\"]}'
assert set(obj.keys()) == {'status', 'items', 'meta'}, f'Extra keys'
print('EMPTY_SPEC_OK')
\" '$OUT2'" "hidden_spec_empty_output"

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
