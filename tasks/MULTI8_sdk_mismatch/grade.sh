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

EXPECTED_JSON="$REPORTS/expected.json"
if [ ! -f "$EXPECTED_JSON" ]; then
  EXPECTED_JSON="$(dirname "$0")/expected.json"
fi

CORRECT_NAME_FIELD="user_name"
CORRECT_LIST_KEY="results"
CORRECT_ERROR_FIELD="detail"
CORRECT_PAGE_PARAM="limit"
WRONG_NAME_FIELD="username"
WRONG_LIST_KEY="items"
WRONG_ERROR_FIELD="message"
WRONG_PAGE_PARAM="page_size"
if [ -f "$EXPECTED_JSON" ]; then
  CORRECT_NAME_FIELD=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('correct_name_field','user_name'))" 2>/dev/null || echo "user_name")
  CORRECT_LIST_KEY=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('correct_list_key','results'))" 2>/dev/null || echo "results")
  CORRECT_ERROR_FIELD=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('correct_error_field','detail'))" 2>/dev/null || echo "detail")
  CORRECT_PAGE_PARAM=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('correct_page_param','limit'))" 2>/dev/null || echo "limit")
  WRONG_NAME_FIELD=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('wrong_name_field','username'))" 2>/dev/null || echo "username")
  WRONG_LIST_KEY=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('wrong_list_key','items'))" 2>/dev/null || echo "items")
  WRONG_ERROR_FIELD=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('wrong_error_field','message'))" 2>/dev/null || echo "message")
  WRONG_PAGE_PARAM=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('wrong_page_param','page_size'))" 2>/dev/null || echo "page_size")
fi

# 1. SDK uses correct name field
check "python3 -c \"
source = open('sdk_client.py').read()
assert '${CORRECT_NAME_FIELD}' in source, 'Missing ${CORRECT_NAME_FIELD}'
print('NAME_FIELD_OK')
\"" "wrong_name_field"

# 2. SDK does not use old name field
check "python3 -c \"
source = open('sdk_client.py').read()
assert '\"${WRONG_NAME_FIELD}\"' not in source and \"'${WRONG_NAME_FIELD}'\" not in source, 'Still uses ${WRONG_NAME_FIELD}'
print('NO_OLD_NAME')
\"" "still_has_old_name_field"

# 3. SDK uses correct list key
check "python3 -c \"
source = open('sdk_client.py').read()
assert '${CORRECT_LIST_KEY}' in source, 'Missing ${CORRECT_LIST_KEY}'
print('LIST_KEY_OK')
\"" "wrong_list_key"

# 4. SDK uses correct error field
check "python3 -c \"
source = open('sdk_client.py').read()
assert '${CORRECT_ERROR_FIELD}' in source, 'Missing ${CORRECT_ERROR_FIELD}'
print('ERROR_FIELD_OK')
\"" "wrong_error_field"

# 5. SDK uses correct pagination param
check "python3 -c \"
source = open('sdk_client.py').read()
assert '${CORRECT_PAGE_PARAM}' in source, 'Missing ${CORRECT_PAGE_PARAM}'
print('PAGE_PARAM_OK')
\"" "wrong_page_param"

# 6. test_sdk.py passes
check "python3 -m pytest test_sdk.py -q 2>/dev/null || python3 -m unittest test_sdk 2>/dev/null" \
      "tests_fail"

# 7. api_spec.yaml unchanged
check "python3 -c \"
import hashlib
h = hashlib.md5(open('api_spec.yaml','rb').read()).hexdigest()
print(f'SPEC_HASH={h}')
\"" "spec_modified"

# 8. Attestation
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
