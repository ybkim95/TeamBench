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

# ---------------------------------------------------------------------------
# Seed-aware: read expected.json if present (generated tasks)
# ---------------------------------------------------------------------------
EXPECTED_JSON="$REPORTS/expected.json"
if [ ! -f "$EXPECTED_JSON" ]; then
  EXPECTED_JSON="$(dirname "$0")/expected.json"
fi

# Extract values from expected.json, fall back to contract defaults
RESOURCE="todos"
SINGULAR="todo"
F1="title"
TOKEN="supersecret-token-abc123"
PORT="5000"
CORRECT_LIST_KEY="items"
CORRECT_PAG_KEY="total"
CORRECT_ERROR_KEY="error"
CORRECT_URL_SEG="api"
CORRECT_SINGLE_KEY="item"
WRONG_LIST_KEY="data"
WRONG_POST_STATUS="200"
WRONG_PAG_KEY="count"
WRONG_ERROR_KEY="message"
WRONG_URL_SEG="apiv1"
WRONG_SINGLE_KEY="data"

if [ -f "$EXPECTED_JSON" ]; then
  RESOURCE=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('resource','todos'))" 2>/dev/null || echo "todos")
  SINGULAR=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('singular','todo'))" 2>/dev/null || echo "todo")
  F1=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('field1','title'))" 2>/dev/null || echo "title")
  TOKEN=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('auth_token','supersecret-token-abc123'))" 2>/dev/null || echo "supersecret-token-abc123")
  PORT=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('port',5000))" 2>/dev/null || echo "5000")
  CORRECT_LIST_KEY=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('correct_list_key','items'))" 2>/dev/null || echo "items")
  CORRECT_PAG_KEY=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('correct_pagination_key','total'))" 2>/dev/null || echo "total")
  CORRECT_ERROR_KEY=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('correct_error_key','error'))" 2>/dev/null || echo "error")
  CORRECT_URL_SEG=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('correct_url_seg','api'))" 2>/dev/null || echo "api")
  CORRECT_SINGLE_KEY=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('correct_single_key','item'))" 2>/dev/null || echo "item")
  WRONG_LIST_KEY=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('wrong_list_key','data'))" 2>/dev/null || echo "data")
  WRONG_POST_STATUS=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('wrong_post_status',200))" 2>/dev/null || echo "200")
  WRONG_PAG_KEY=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('wrong_pagination_key','count'))" 2>/dev/null || echo "count")
  WRONG_ERROR_KEY=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('wrong_error_key','message'))" 2>/dev/null || echo "message")
  WRONG_URL_SEG=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('wrong_url_seg','apiv1'))" 2>/dev/null || echo "apiv1")
  WRONG_SINGLE_KEY=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('wrong_single_key','data'))" 2>/dev/null || echo "data")
fi

# ---------------------------------------------------------------------------
# Check 1: backend/server.py imports without error
# ---------------------------------------------------------------------------
check "cd '$WORKSPACE/backend' && python3 -c 'import server'" "backend_import_error"

# ---------------------------------------------------------------------------
# Check 2: frontend/app.py imports without error
# ---------------------------------------------------------------------------
check "cd '$WORKSPACE/frontend' && python3 -c 'import app'" "frontend_import_error"

# ---------------------------------------------------------------------------
# Check 3: POST /api/<resource> returns 201
# ---------------------------------------------------------------------------
check "python3 - <<'PYEOF'
import sys, json
sys.path.insert(0, '$WORKSPACE/backend')
import importlib, server as s
importlib.reload(s)
s.app.testing = True
c = s.app.test_client()
r = c.post('/api/${RESOURCE}',
    data=json.dumps({'${F1}': 'grade_test'}),
    content_type='application/json',
    headers={'Authorization': 'Bearer ${TOKEN}'})
assert r.status_code == 201, f'Expected 201, got {r.status_code}'
PYEOF" "post_wrong_status"

# ---------------------------------------------------------------------------
# Check 4: POST response contains 'item' key
# ---------------------------------------------------------------------------
check "python3 - <<'PYEOF'
import sys, json
sys.path.insert(0, '$WORKSPACE/backend')
import importlib, server as s
importlib.reload(s)
s.app.testing = True
c = s.app.test_client()
r = c.post('/api/${RESOURCE}',
    data=json.dumps({'${F1}': 'key_test'}),
    content_type='application/json',
    headers={'Authorization': 'Bearer ${TOKEN}'})
body = json.loads(r.data)
assert 'item' in body, f'Missing item key, got: {list(body.keys())}'
PYEOF" "post_missing_item_key"

# ---------------------------------------------------------------------------
# Check 5: GET list returns correct list key (not the wrong one)
# ---------------------------------------------------------------------------
check "python3 - <<'PYEOF'
import sys, json
sys.path.insert(0, '$WORKSPACE/backend')
import importlib, server as s
importlib.reload(s)
s.app.testing = True
c = s.app.test_client()
r = c.get('/api/${RESOURCE}', headers={'Authorization': 'Bearer ${TOKEN}'})
assert r.status_code == 200, f'Expected 200, got {r.status_code}'
body = json.loads(r.data)
assert '${CORRECT_LIST_KEY}' in body, f\"Missing '${CORRECT_LIST_KEY}' key, got: {list(body.keys())}\"
assert isinstance(body['${CORRECT_LIST_KEY}'], list), 'items value must be a list'
PYEOF" "get_list_wrong_key"

# ---------------------------------------------------------------------------
# Check 6: GET list includes correct pagination key
# ---------------------------------------------------------------------------
check "python3 - <<'PYEOF'
import sys, json
sys.path.insert(0, '$WORKSPACE/backend')
import importlib, server as s
importlib.reload(s)
s.app.testing = True
c = s.app.test_client()
r = c.get('/api/${RESOURCE}', headers={'Authorization': 'Bearer ${TOKEN}'})
body = json.loads(r.data)
assert '${CORRECT_PAG_KEY}' in body, f\"Missing '${CORRECT_PAG_KEY}' pagination key, got: {list(body.keys())}\"
assert 'page'  in body, 'Missing page field'
assert 'limit' in body, 'Missing limit field'
PYEOF" "get_list_wrong_pagination"

# ---------------------------------------------------------------------------
# Check 7: CORS header present on GET response
# ---------------------------------------------------------------------------
check "python3 - <<'PYEOF'
import sys, json
sys.path.insert(0, '$WORKSPACE/backend')
import importlib, server as s
importlib.reload(s)
s.app.testing = True
c = s.app.test_client()
r = c.get('/api/${RESOURCE}', headers={'Authorization': 'Bearer ${TOKEN}'})
cors = r.headers.get('Access-Control-Allow-Origin', '')
assert cors != '', 'Missing Access-Control-Allow-Origin header'
PYEOF" "cors_header_missing"

# ---------------------------------------------------------------------------
# Check 8: Error responses use correct error key
# ---------------------------------------------------------------------------
check "python3 - <<'PYEOF'
import sys, json
sys.path.insert(0, '$WORKSPACE/backend')
import importlib, server as s
importlib.reload(s)
s.app.testing = True
c = s.app.test_client()
r = c.get('/api/${RESOURCE}')   # no auth -> 401
assert r.status_code == 401, f'Expected 401 without auth, got {r.status_code}'
body = json.loads(r.data)
assert '${CORRECT_ERROR_KEY}' in body, f\"Error response must use '${CORRECT_ERROR_KEY}', got: {list(body.keys())}\"
PYEOF" "error_wrong_key"

# ---------------------------------------------------------------------------
# Check 9: GET single item returns 'item' key
# ---------------------------------------------------------------------------
check "python3 - <<'PYEOF'
import sys, json
sys.path.insert(0, '$WORKSPACE/backend')
import importlib, server as s
importlib.reload(s)
s.app.testing = True
c = s.app.test_client()
auth = {'Authorization': 'Bearer ${TOKEN}'}
cr = c.post('/api/${RESOURCE}',
    data=json.dumps({'${F1}': 'single_test'}),
    content_type='application/json',
    headers=auth)
item_id = json.loads(cr.data)['item']['id']
r = c.get(f'/api/${RESOURCE}/{item_id}', headers=auth)
assert r.status_code == 200, f'Expected 200, got {r.status_code}'
body = json.loads(r.data)
assert 'item' in body, f\"GET single missing 'item' key, got: {list(body.keys())}\"
PYEOF" "get_single_wrong_key"

# ---------------------------------------------------------------------------
# Check 10: GET non-existent returns 404 with correct error key
# ---------------------------------------------------------------------------
check "python3 - <<'PYEOF'
import sys, json
sys.path.insert(0, '$WORKSPACE/backend')
import importlib, server as s
importlib.reload(s)
s.app.testing = True
c = s.app.test_client()
r = c.get('/api/${RESOURCE}/99999', headers={'Authorization': 'Bearer ${TOKEN}'})
assert r.status_code == 404, f'Expected 404, got {r.status_code}'
body = json.loads(r.data)
assert '${CORRECT_ERROR_KEY}' in body, f\"404 must use '${CORRECT_ERROR_KEY}', got: {list(body.keys())}\"
PYEOF" "get_404_wrong_key"

# ---------------------------------------------------------------------------
# Check 11: frontend BASE_URL uses correct path '/api/<resource>'
# ---------------------------------------------------------------------------
check "grep -q '/api/${RESOURCE}' '$WORKSPACE/frontend/app.py'" "frontend_wrong_url_path"

# ---------------------------------------------------------------------------
# Check 12: frontend HEADERS contain Authorization Bearer token
# ---------------------------------------------------------------------------
check "grep -q 'Authorization' '$WORKSPACE/frontend/app.py' && grep -q 'Bearer' '$WORKSPACE/frontend/app.py'" \
      "frontend_missing_auth_header"

# ---------------------------------------------------------------------------
# Check 13: frontend reads correct list key from response
# ---------------------------------------------------------------------------
check "grep -q '\"${CORRECT_LIST_KEY}\"' '$WORKSPACE/frontend/app.py' && ! grep -q '\"${WRONG_LIST_KEY}\"' '$WORKSPACE/frontend/app.py'" \
      "frontend_wrong_list_field"

# ---------------------------------------------------------------------------
# Check 14: frontend error handling reads correct error key
# ---------------------------------------------------------------------------
check "grep -q \"'${CORRECT_ERROR_KEY}'\" '$WORKSPACE/frontend/app.py'" \
      "frontend_wrong_error_field"

# ---------------------------------------------------------------------------
# Check 15: frontend reads correct single-item key
# ---------------------------------------------------------------------------
check "grep -q '\"${CORRECT_SINGLE_KEY}\"' '$WORKSPACE/frontend/app.py'" \
      "frontend_wrong_single_field"

# ---------------------------------------------------------------------------
# Check 16: full unittest suite passes
# ---------------------------------------------------------------------------
check "python3 -m pytest '$WORKSPACE/test_contract.py' -q --tb=no 2>/dev/null || \
       python3 -m unittest discover -s '$WORKSPACE' -p 'test_contract.py' -q 2>/dev/null" \
      "test_suite_failures"

# ---------------------------------------------------------------------------
# Check 17: no wrong list key still present in server.py
# ---------------------------------------------------------------------------
check "! grep -q '\"${WRONG_LIST_KEY}\": items' '$WORKSPACE/backend/server.py' 2>/dev/null && \
       ! grep -q \"'${WRONG_LIST_KEY}': items\" '$WORKSPACE/backend/server.py' 2>/dev/null" \
      "backend_wrong_list_key_remains"

# ---------------------------------------------------------------------------
# Check 18: attestation.json verdict=pass
# ---------------------------------------------------------------------------
check "python3 -c \"
import json, sys
att = json.load(open(sys.argv[1]))
assert att.get('verdict') == 'pass', f'verdict={att.get(\\\"verdict\\\")}'
\" '$SUBMISSION/attestation.json'" "bad_attestation"

# ---------------------------------------------------------------------------
# Write score
# ---------------------------------------------------------------------------
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
