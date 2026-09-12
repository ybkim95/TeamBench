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

DETAIL_FIELD="body"
TIME_FIELD="created_at"
if [ -f "$EXPECTED_JSON" ]; then
  DETAIL_FIELD=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('detail_field','body'))" 2>/dev/null || echo "body")
  TIME_FIELD=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('time_field','created_at'))" 2>/dev/null || echo "created_at")
fi

# 1. app.py imports without error
check "python3 -c 'from app import app'" "import_error"

# 2. GET endpoint returns a plain JSON array (not envelope)
check "python3 -c \"
from app import app
client = app.test_client()
import json
res = client.get('/api/items')
data = json.loads(res.data)
assert isinstance(data, list), f'Expected list, got {type(data).__name__}'
print('LIST_OK')
\"" "get_returns_envelope"

# 3. POST creates item with correct fields
check "python3 -c \"
from app import app
client = app.test_client()
import json
res = client.post('/api/items', data=json.dumps({'title': 'T', '${DETAIL_FIELD}': 'D'}), content_type='application/json')
assert res.status_code == 201, f'Expected 201, got {res.status_code}'
item = json.loads(res.data)
assert 'title' in item, 'Missing title'
assert '${DETAIL_FIELD}' in item, 'Missing ${DETAIL_FIELD}'
print('POST_OK')
\"" "post_create_fail"

# 4. Items have correct detail field name
check "python3 -c \"
from app import app
client = app.test_client()
import json
client.post('/api/items', data=json.dumps({'title': 'X', '${DETAIL_FIELD}': 'Y'}), content_type='application/json')
res = client.get('/api/items')
items = json.loads(res.data)
assert len(items) > 0, 'No items'
assert '${DETAIL_FIELD}' in items[0], f'Missing field ${DETAIL_FIELD} in {list(items[0].keys())}'
print('FIELD_OK')
\"" "wrong_detail_field"

# 5. Items have created_at (not timestamp)
check "python3 -c \"
from app import app
client = app.test_client()
import json
client.post('/api/items', data=json.dumps({'title': 'X', '${DETAIL_FIELD}': 'Y'}), content_type='application/json')
res = client.get('/api/items')
items = json.loads(res.data)
assert '${TIME_FIELD}' in items[0], f'Missing ${TIME_FIELD}'
assert 'timestamp' not in items[0], 'Still has stale timestamp field'
print('TIME_FIELD_OK')
\"" "wrong_time_field"

# 6. types.json references created_at not timestamp
check "python3 -c \"
import json
with open('types.json') as f:
    t = json.load(f)
fields = [x.get('name', x) if isinstance(x, dict) else x for x in t.get('item', {}).get('fields', t.get('fields', []))]
field_names = [f if isinstance(f, str) else str(f) for f in fields]
text = json.dumps(t)
assert '${TIME_FIELD}' in text, 'types.json missing ${TIME_FIELD}'
assert 'timestamp' not in text, 'types.json still has stale timestamp'
print('TYPES_OK')
\"" "types_json_stale"

# 7. static/app.js uses correct detail field
check "grep -q '${DETAIL_FIELD}' static/app.js && ! grep -q 'description' static/app.js" \
      "frontend_wrong_field"

# 8. test_app.py passes all tests
check "python3 -m pytest test_app.py -q 2>/dev/null || python3 -m unittest test_app 2>/dev/null" \
      "tests_fail"

# 9. No envelope wrapper in GET response
check "python3 -c \"
import ast
source = open('app.py').read()
assert '\\\"data\\\"' not in source or 'jsonify(items)' in source or 'jsonify(result)' in source, 'Still using envelope'
print('NO_ENVELOPE')
\"" "envelope_still_present"

# 10. Attestation
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
