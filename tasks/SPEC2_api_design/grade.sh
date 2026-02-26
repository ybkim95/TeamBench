#!/usr/bin/env bash
# Seed-aware grader for SPEC2: API Design from OpenAPI Spec
#
# Reads domain and expected values from expected.json.
# Runs the agent's Flask API against acceptance criteria that cannot be
# inferred from the workspace skeleton or tests alone.
#
# Args: $1=WORKSPACE $2=REPORTS $3=SUBMISSION $4=TASK_DIR [$5=EXPECTED_JSON]
set -o pipefail
WORKSPACE="$1"
REPORTS="$2"
SUBMISSION="$3"
TASK_DIR="$4"
EXPECTED="${5:-$REPORTS/expected.json}"

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

# ── Read domain from expected.json ───────────────────────────────────────────
DOMAIN=$(python3 -c "
import json
e = json.load(open('$EXPECTED'))
print(e.get('domain', 'unknown'))
" 2>/dev/null || echo "unknown")

# ── 1. app.py is syntactically valid Python ──────────────────────────────────
check "python3 -m py_compile app.py" "app_syntax_error"

# ── 2. Basic tests pass (skeleton-level checks from test_api.py) ─────────────
check "python3 -m pytest test_api.py -q --tb=no 2>/dev/null | tail -1 | grep -E '^[0-9]+ passed'" \
  "basic_tests_fail"

# ── Domain-specific checks ────────────────────────────────────────────────────

if [ "$DOMAIN" = "task_management" ]; then

  MAX_TITLE=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e['max_title_len'])" 2>/dev/null || echo "80")
  MAX_DESC=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e['max_desc_len'])" 2>/dev/null || echo "300")
  PRIORITIES_JSON=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(json.dumps(e['allowed_priorities']))" 2>/dev/null || echo '["HIGH","MEDIUM","LOW"]')
  FIRST_PRIORITY=$(python3 -c "import json; print(json.loads('$PRIORITIES_JSON')[0])" 2>/dev/null || echo "HIGH")
  LAST_PRIORITY=$(python3 -c "import json; p=json.loads('$PRIORITIES_JSON'); print(p[-1])" 2>/dev/null || echo "LOW")

  # 3. POST missing required field returns 400
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from app import app
c = app.test_client()
app.config['TESTING'] = True
# missing title
r = c.post('/api/v1/tasks', json={'priority': '$FIRST_PRIORITY'})
assert r.status_code == 400, f'Expected 400 for missing title, got {r.status_code}'
# missing priority
r2 = c.post('/api/v1/tasks', json={'title': 'Test'})
assert r2.status_code == 400, f'Expected 400 for missing priority, got {r2.status_code}'
print('MISSING_FIELD_400_OK')
\"" "missing_required_field_not_400"

  # 4. POST with valid data returns 201 with correct schema fields
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from app import app, store
store._tasks.clear(); store._next_id = 1
app.config['TESTING'] = True
c = app.test_client()
r = c.post('/api/v1/tasks', json={'title': 'Schema test', 'priority': '$FIRST_PRIORITY'})
assert r.status_code == 201, f'Expected 201, got {r.status_code}'
d = r.get_json()
for field in ('id', 'title', 'priority', 'status', 'created_at'):
    assert field in d, f'Missing field: {field}'
assert d['status'] == 'TODO', f'Initial status must be TODO, got {d[\"status\"]}'
print('SCHEMA_FIELDS_OK')
\"" "post_schema_fields_wrong"

  # 5. POST duplicate title returns 409 with DUPLICATE_TITLE error code
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from app import app, store
store._tasks.clear(); store._next_id = 1
app.config['TESTING'] = True
c = app.test_client()
c.post('/api/v1/tasks', json={'title': 'Unique task', 'priority': '$FIRST_PRIORITY'})
r = c.post('/api/v1/tasks', json={'title': 'Unique task', 'priority': '$FIRST_PRIORITY'})
assert r.status_code == 409, f'Expected 409 for duplicate, got {r.status_code}'
d = r.get_json()
assert d.get('error') == 'DUPLICATE_TITLE', f'Wrong error code: {d.get(\"error\")}'
print('DUPLICATE_409_OK')
\"" "duplicate_title_not_409"

  # 6. Duplicate title check is case-insensitive
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from app import app, store
store._tasks.clear(); store._next_id = 1
app.config['TESTING'] = True
c = app.test_client()
c.post('/api/v1/tasks', json={'title': 'Hello Task', 'priority': '$FIRST_PRIORITY'})
r = c.post('/api/v1/tasks', json={'title': 'hello task', 'priority': '$FIRST_PRIORITY'})
assert r.status_code == 409, f'Expected 409 for case-insensitive duplicate, got {r.status_code}'
print('CASE_INSENSITIVE_DUPLICATE_OK')
\"" "duplicate_title_case_sensitive"

  # 7. GET non-existent task returns 404 with TASK_NOT_FOUND error code
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from app import app, store
store._tasks.clear(); store._next_id = 1
app.config['TESTING'] = True
c = app.test_client()
r = c.get('/api/v1/tasks/9999')
assert r.status_code == 404, f'Expected 404, got {r.status_code}'
d = r.get_json()
assert d.get('error') == 'TASK_NOT_FOUND', f'Wrong error code: {d.get(\"error\")}'
print('NOT_FOUND_CODE_OK')
\"" "not_found_wrong_error_code"

  # 8. POST title exceeding max_title_len returns 400
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from app import app, store
store._tasks.clear(); store._next_id = 1
app.config['TESTING'] = True
c = app.test_client()
long_title = 'x' * ($MAX_TITLE + 1)
r = c.post('/api/v1/tasks', json={'title': long_title, 'priority': '$FIRST_PRIORITY'})
assert r.status_code == 400, f'Expected 400 for too-long title ({$MAX_TITLE+1} chars), got {r.status_code}'
print('TITLE_LEN_VALIDATION_OK')
\"" "title_length_not_validated"

  # 9. POST with invalid priority returns 400
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from app import app, store
store._tasks.clear(); store._next_id = 1
app.config['TESTING'] = True
c = app.test_client()
r = c.post('/api/v1/tasks', json={'title': 'Test', 'priority': 'SUPER_URGENT'})
assert r.status_code == 400, f'Expected 400 for invalid priority, got {r.status_code}'
d = r.get_json()
assert d.get('error') == 'VALIDATION_ERROR', f'Wrong error code: {d.get(\"error\")}'
print('INVALID_PRIORITY_400_OK')
\"" "invalid_priority_not_400"

  # 10. PUT update returns 200 and reflects changes
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from app import app, store
store._tasks.clear(); store._next_id = 1
app.config['TESTING'] = True
c = app.test_client()
c.post('/api/v1/tasks', json={'title': 'Old title', 'priority': '$FIRST_PRIORITY'})
r = c.put('/api/v1/tasks/1', json={'title': 'New title', 'status': 'IN_PROGRESS'})
assert r.status_code == 200, f'Expected 200 from PUT, got {r.status_code}'
d = r.get_json()
assert d['title'] == 'New title', f'Title not updated: {d[\"title\"]}'
assert d['status'] == 'IN_PROGRESS', f'Status not updated: {d[\"status\"]}'
print('PUT_UPDATE_OK')
\"" "put_update_fails"

  # 11. DELETE returns 200 with deleted task object; subsequent GET returns 404
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from app import app, store
store._tasks.clear(); store._next_id = 1
app.config['TESTING'] = True
c = app.test_client()
c.post('/api/v1/tasks', json={'title': 'Delete me', 'priority': '$FIRST_PRIORITY'})
r = c.delete('/api/v1/tasks/1')
assert r.status_code == 200, f'Expected 200 from DELETE, got {r.status_code}'
d = r.get_json()
assert d['title'] == 'Delete me', f'Deleted task not returned: {d}'
r2 = c.get('/api/v1/tasks/1')
assert r2.status_code == 404, f'Task should be gone after DELETE, got {r2.status_code}'
print('DELETE_OK')
\"" "delete_wrong_behavior"

  # 12. Attestation check
  check "python3 -c \"
import json, sys
att = json.load(open('$SUBMISSION/attestation.json'))
assert att.get('verdict') == 'pass', f'Attestation verdict: {att.get(\"verdict\")}'
\" " "bad_attestation"

elif [ "$DOMAIN" = "inventory" ]; then

  MAX_NAME=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e['max_name_len'])" 2>/dev/null || echo "80")
  MAX_QTY=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e['max_qty'])" 2>/dev/null || echo "1000")
  CATEGORIES_JSON=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(json.dumps(e['categories']))" 2>/dev/null || echo '["electronics"]')
  FIRST_CAT=$(python3 -c "import json; print(json.loads('$CATEGORIES_JSON')[0])" 2>/dev/null || echo "electronics")
  LOW_STOCK=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e['low_stock_threshold'])" 2>/dev/null || echo "10")

  # 3. POST missing required field returns 400
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from app import app, store
store._products.clear(); store._next_id = 1
app.config['TESTING'] = True
c = app.test_client()
r = c.post('/api/v1/products', json={'name': 'Widget', 'category': '$FIRST_CAT'})
assert r.status_code == 400, f'Expected 400 for missing quantity/price, got {r.status_code}'
print('MISSING_FIELD_400_OK')
\"" "missing_required_field_not_400"

  # 4. POST valid product returns 201 with correct schema including low_stock field
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from app import app, store
store._products.clear(); store._next_id = 1
app.config['TESTING'] = True
c = app.test_client()
r = c.post('/api/v1/products', json={
    'name': 'Widget', 'category': '$FIRST_CAT', 'quantity': 50, 'price': 9.99
})
assert r.status_code == 201, f'Expected 201, got {r.status_code}'
d = r.get_json()
for field in ('id', 'name', 'category', 'quantity', 'price', 'low_stock'):
    assert field in d, f'Missing field: {field}'
assert d['low_stock'] == False, f'low_stock should be False for qty=50'
print('SCHEMA_AND_LOW_STOCK_OK')
\"" "post_schema_or_low_stock_wrong"

  # 5. POST duplicate name (case-insensitive) returns 409 with DUPLICATE_NAME
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from app import app, store
store._products.clear(); store._next_id = 1
app.config['TESTING'] = True
c = app.test_client()
c.post('/api/v1/products', json={'name': 'Widget', 'category': '$FIRST_CAT', 'quantity': 5, 'price': 1.0})
r = c.post('/api/v1/products', json={'name': 'widget', 'category': '$FIRST_CAT', 'quantity': 5, 'price': 1.0})
assert r.status_code == 409, f'Expected 409 for duplicate name, got {r.status_code}'
d = r.get_json()
assert d.get('error') == 'DUPLICATE_NAME', f'Wrong error code: {d.get(\"error\")}'
print('DUPLICATE_NAME_OK')
\"" "duplicate_name_not_409"

  # 6. POST quantity > max_qty returns 400
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from app import app, store
store._products.clear(); store._next_id = 1
app.config['TESTING'] = True
c = app.test_client()
r = c.post('/api/v1/products', json={
    'name': 'Overstock', 'category': '$FIRST_CAT', 'quantity': $MAX_QTY + 1, 'price': 1.0
})
assert r.status_code == 400, f'Expected 400 for qty > {$MAX_QTY}, got {r.status_code}'
print('MAX_QTY_VALIDATION_OK')
\"" "max_qty_not_validated"

  # 7. POST price <= 0 returns 400
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from app import app, store
store._products.clear(); store._next_id = 1
app.config['TESTING'] = True
c = app.test_client()
r = c.post('/api/v1/products', json={
    'name': 'FreeProduct', 'category': '$FIRST_CAT', 'quantity': 10, 'price': 0
})
assert r.status_code == 400, f'Expected 400 for price=0, got {r.status_code}'
print('ZERO_PRICE_VALIDATION_OK')
\"" "zero_price_not_rejected"

  # 8. GET /api/v1/products/999 returns 404 with PRODUCT_NOT_FOUND
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from app import app, store
store._products.clear(); store._next_id = 1
app.config['TESTING'] = True
c = app.test_client()
r = c.get('/api/v1/products/9999')
assert r.status_code == 404, f'Expected 404, got {r.status_code}'
d = r.get_json()
assert d.get('error') == 'PRODUCT_NOT_FOUND', f'Wrong error code: {d.get(\"error\")}'
print('NOT_FOUND_OK')
\"" "product_not_found_wrong_code"

  # 9. low_stock computed field: quantity <= threshold → True; quantity > threshold → False
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from app import app, store
store._products.clear(); store._next_id = 1
app.config['TESTING'] = True
c = app.test_client()
c.post('/api/v1/products', json={'name': 'Low', 'category': '$FIRST_CAT', 'quantity': $LOW_STOCK, 'price': 1.0})
c.post('/api/v1/products', json={'name': 'High', 'category': '$FIRST_CAT', 'quantity': $LOW_STOCK + 1, 'price': 1.0})
r1 = c.get('/api/v1/products/1').get_json()
r2 = c.get('/api/v1/products/2').get_json()
assert r1['low_stock'] == True, f'qty={$LOW_STOCK} should be low_stock=True, got {r1[\"low_stock\"]}'
assert r2['low_stock'] == False, f'qty={$LOW_STOCK+1} should be low_stock=False, got {r2[\"low_stock\"]}'
print('LOW_STOCK_COMPUTED_OK')
\"" "low_stock_computed_wrong"

  # 10. GET /api/v1/products/low-stock returns only low-stock items sorted by qty asc then id asc
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from app import app, store
store._products.clear(); store._next_id = 1
app.config['TESTING'] = True
c = app.test_client()
c.post('/api/v1/products', json={'name': 'A', 'category': '$FIRST_CAT', 'quantity': $LOW_STOCK + 5, 'price': 1.0})
c.post('/api/v1/products', json={'name': 'B', 'category': '$FIRST_CAT', 'quantity': 1, 'price': 1.0})
c.post('/api/v1/products', json={'name': 'C', 'category': '$FIRST_CAT', 'quantity': 0, 'price': 1.0})
r = c.get('/api/v1/products/low-stock')
assert r.status_code == 200, f'Expected 200, got {r.status_code}'
items = r.get_json()
names = [i['name'] for i in items]
assert 'A' not in names, f'Product A should not be in low-stock list: {names}'
assert names.index('C') < names.index('B'), f'Should be sorted by qty asc: {names}'
print('LOW_STOCK_ENDPOINT_OK')
\"" "low_stock_endpoint_wrong"

  # 11. PUT update returns 200 with updated values
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from app import app, store
store._products.clear(); store._next_id = 1
app.config['TESTING'] = True
c = app.test_client()
c.post('/api/v1/products', json={'name': 'Widget', 'category': '$FIRST_CAT', 'quantity': 50, 'price': 9.99})
r = c.put('/api/v1/products/1', json={'quantity': 3, 'price': 4.99})
assert r.status_code == 200, f'Expected 200 from PUT, got {r.status_code}'
d = r.get_json()
assert d['quantity'] == 3, f'quantity not updated: {d[\"quantity\"]}'
assert abs(d['price'] - 4.99) < 0.01, f'price not updated: {d[\"price\"]}'
print('PUT_UPDATE_OK')
\"" "put_update_fails"

  # 12. Attestation check
  check "python3 -c \"
import json, sys
att = json.load(open('$SUBMISSION/attestation.json'))
assert att.get('verdict') == 'pass', f'Attestation verdict: {att.get(\"verdict\")}'
\" " "bad_attestation"

elif [ "$DOMAIN" = "booking" ]; then

  MIN_ADV_HRS=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e['min_advance_hours'])" 2>/dev/null || echo "2")
  MAX_ADV_DAYS=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e['max_advance_days'])" 2>/dev/null || echo "14")
  MAX_CAP=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e['max_capacity'])" 2>/dev/null || echo "10")
  ROOM_TYPES_JSON=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(json.dumps(e['room_types']))" 2>/dev/null || echo '["conference"]')
  FIRST_ROOM_TYPE=$(python3 -c "import json; print(json.loads('$ROOM_TYPES_JSON')[0])" 2>/dev/null || echo "conference")

  # 3. POST room missing required field returns 400
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from app import app, store
store._rooms.clear(); store._reservations.clear(); store._room_next_id = 1; store._res_next_id = 1
app.config['TESTING'] = True
c = app.test_client()
r = c.post('/api/v1/rooms', json={'name': 'Room A'})
assert r.status_code == 400, f'Expected 400 for missing type/capacity, got {r.status_code}'
print('ROOM_MISSING_FIELD_OK')
\"" "room_missing_field_not_400"

  # 4. POST reservation returns 201 with CONFIRMED status and correct schema
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from datetime import datetime, timezone, timedelta
from app import app, store
store._rooms.clear(); store._reservations.clear(); store._room_next_id = 1; store._res_next_id = 1
app.config['TESTING'] = True
c = app.test_client()
c.post('/api/v1/rooms', json={'name': 'R1', 'type': '$FIRST_ROOM_TYPE', 'capacity': 2})
now = datetime.now(timezone.utc)
start = (now + timedelta(hours=$MIN_ADV_HRS + 2)).strftime('%Y-%m-%dT%H:%M:%S')
end = (now + timedelta(hours=$MIN_ADV_HRS + 3)).strftime('%Y-%m-%dT%H:%M:%S')
r = c.post('/api/v1/reservations', json={'room_id': 1, 'user_id': 'alice', 'start_time': start, 'end_time': end})
assert r.status_code == 201, f'Expected 201, got {r.status_code}: {r.get_data(as_text=True)}'
d = r.get_json()
assert d.get('status') == 'CONFIRMED', f'Expected CONFIRMED, got {d.get(\"status\")}'
for field in ('id', 'room_id', 'user_id', 'start_time', 'end_time', 'status'):
    assert field in d, f'Missing field: {field}'
print('RESERVATION_SCHEMA_OK')
\"" "reservation_schema_wrong"

  # 5. POST reservation for non-existent room returns 404 ROOM_NOT_FOUND
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from datetime import datetime, timezone, timedelta
from app import app, store
store._rooms.clear(); store._reservations.clear(); store._room_next_id = 1; store._res_next_id = 1
app.config['TESTING'] = True
c = app.test_client()
now = datetime.now(timezone.utc)
start = (now + timedelta(hours=$MIN_ADV_HRS + 2)).strftime('%Y-%m-%dT%H:%M:%S')
end = (now + timedelta(hours=$MIN_ADV_HRS + 3)).strftime('%Y-%m-%dT%H:%M:%S')
r = c.post('/api/v1/reservations', json={'room_id': 9999, 'user_id': 'alice', 'start_time': start, 'end_time': end})
assert r.status_code == 404, f'Expected 404, got {r.status_code}'
d = r.get_json()
assert d.get('error') == 'ROOM_NOT_FOUND', f'Wrong code: {d.get(\"error\")}'
print('ROOM_NOT_FOUND_OK')
\"" "room_not_found_wrong_code"

  # 6. Overlapping reservation returns 409 TIME_CONFLICT
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from datetime import datetime, timezone, timedelta
from app import app, store
store._rooms.clear(); store._reservations.clear(); store._room_next_id = 1; store._res_next_id = 1
app.config['TESTING'] = True
c = app.test_client()
c.post('/api/v1/rooms', json={'name': 'R1', 'type': '$FIRST_ROOM_TYPE', 'capacity': 2})
now = datetime.now(timezone.utc)
start = (now + timedelta(hours=$MIN_ADV_HRS + 2)).strftime('%Y-%m-%dT%H:%M:%S')
end = (now + timedelta(hours=$MIN_ADV_HRS + 4)).strftime('%Y-%m-%dT%H:%M:%S')
c.post('/api/v1/reservations', json={'room_id': 1, 'user_id': 'alice', 'start_time': start, 'end_time': end})
r = c.post('/api/v1/reservations', json={'room_id': 1, 'user_id': 'bob', 'start_time': start, 'end_time': end})
assert r.status_code == 409, f'Expected 409 for conflict, got {r.status_code}'
d = r.get_json()
assert d.get('error') == 'TIME_CONFLICT', f'Wrong code: {d.get(\"error\")}'
print('TIME_CONFLICT_OK')
\"" "time_conflict_wrong_code"

  # 7. Booking too soon returns 400 BOOKING_TOO_SOON
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from datetime import datetime, timezone, timedelta
from app import app, store
store._rooms.clear(); store._reservations.clear(); store._room_next_id = 1; store._res_next_id = 1
app.config['TESTING'] = True
c = app.test_client()
c.post('/api/v1/rooms', json={'name': 'R1', 'type': '$FIRST_ROOM_TYPE', 'capacity': 2})
now = datetime.now(timezone.utc)
# start_time less than min_advance_hours from now
start = (now + timedelta(minutes=10)).strftime('%Y-%m-%dT%H:%M:%S')
end = (now + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S')
r = c.post('/api/v1/reservations', json={'room_id': 1, 'user_id': 'alice', 'start_time': start, 'end_time': end})
assert r.status_code == 400, f'Expected 400 for too-soon booking, got {r.status_code}'
d = r.get_json()
assert d.get('error') == 'BOOKING_TOO_SOON', f'Wrong code: {d.get(\"error\")}'
print('BOOKING_TOO_SOON_OK')
\"" "booking_too_soon_wrong_code"

  # 8. Booking too far ahead returns 400 BOOKING_TOO_FAR_AHEAD
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from datetime import datetime, timezone, timedelta
from app import app, store
store._rooms.clear(); store._reservations.clear(); store._room_next_id = 1; store._res_next_id = 1
app.config['TESTING'] = True
c = app.test_client()
c.post('/api/v1/rooms', json={'name': 'R1', 'type': '$FIRST_ROOM_TYPE', 'capacity': 2})
now = datetime.now(timezone.utc)
start = (now + timedelta(days=$MAX_ADV_DAYS + 1)).strftime('%Y-%m-%dT%H:%M:%S')
end = (now + timedelta(days=$MAX_ADV_DAYS + 1, hours=1)).strftime('%Y-%m-%dT%H:%M:%S')
r = c.post('/api/v1/reservations', json={'room_id': 1, 'user_id': 'alice', 'start_time': start, 'end_time': end})
assert r.status_code == 400, f'Expected 400 for too-far booking, got {r.status_code}'
d = r.get_json()
assert d.get('error') == 'BOOKING_TOO_FAR_AHEAD', f'Wrong code: {d.get(\"error\")}'
print('BOOKING_TOO_FAR_OK')
\"" "booking_too_far_wrong_code"

  # 9. end_time before start_time returns 400 VALIDATION_ERROR
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from datetime import datetime, timezone, timedelta
from app import app, store
store._rooms.clear(); store._reservations.clear(); store._room_next_id = 1; store._res_next_id = 1
app.config['TESTING'] = True
c = app.test_client()
c.post('/api/v1/rooms', json={'name': 'R1', 'type': '$FIRST_ROOM_TYPE', 'capacity': 2})
now = datetime.now(timezone.utc)
start = (now + timedelta(hours=$MIN_ADV_HRS + 3)).strftime('%Y-%m-%dT%H:%M:%S')
end = (now + timedelta(hours=$MIN_ADV_HRS + 2)).strftime('%Y-%m-%dT%H:%M:%S')
r = c.post('/api/v1/reservations', json={'room_id': 1, 'user_id': 'alice', 'start_time': start, 'end_time': end})
assert r.status_code == 400, f'Expected 400 for end before start, got {r.status_code}'
print('END_BEFORE_START_OK')
\"" "end_before_start_not_rejected"

  # 10. DELETE (cancel) sets status to CANCELLED, does not delete record
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from datetime import datetime, timezone, timedelta
from app import app, store
store._rooms.clear(); store._reservations.clear(); store._room_next_id = 1; store._res_next_id = 1
app.config['TESTING'] = True
c = app.test_client()
c.post('/api/v1/rooms', json={'name': 'R1', 'type': '$FIRST_ROOM_TYPE', 'capacity': 2})
now = datetime.now(timezone.utc)
start = (now + timedelta(hours=$MIN_ADV_HRS + 2)).strftime('%Y-%m-%dT%H:%M:%S')
end = (now + timedelta(hours=$MIN_ADV_HRS + 3)).strftime('%Y-%m-%dT%H:%M:%S')
c.post('/api/v1/reservations', json={'room_id': 1, 'user_id': 'alice', 'start_time': start, 'end_time': end})
r = c.delete('/api/v1/reservations/1')
assert r.status_code == 200, f'Expected 200, got {r.status_code}'
d = r.get_json()
assert d.get('status') == 'CANCELLED', f'Expected CANCELLED, got {d.get(\"status\")}'
# Record must still be retrievable
r2 = c.get('/api/v1/reservations/1')
assert r2.status_code == 200, 'Record should still exist after cancellation'
print('CANCEL_SETS_STATUS_OK')
\"" "cancel_wrong_behavior"

  # 11. Reservation list filter by room_id
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from datetime import datetime, timezone, timedelta
from app import app, store
store._rooms.clear(); store._reservations.clear(); store._room_next_id = 1; store._res_next_id = 1
app.config['TESTING'] = True
c = app.test_client()
c.post('/api/v1/rooms', json={'name': 'R1', 'type': '$FIRST_ROOM_TYPE', 'capacity': 2})
c.post('/api/v1/rooms', json={'name': 'R2', 'type': '$FIRST_ROOM_TYPE', 'capacity': 2})
now = datetime.now(timezone.utc)
s1 = (now + timedelta(hours=$MIN_ADV_HRS + 2)).strftime('%Y-%m-%dT%H:%M:%S')
e1 = (now + timedelta(hours=$MIN_ADV_HRS + 3)).strftime('%Y-%m-%dT%H:%M:%S')
s2 = (now + timedelta(hours=$MIN_ADV_HRS + 5)).strftime('%Y-%m-%dT%H:%M:%S')
e2 = (now + timedelta(hours=$MIN_ADV_HRS + 6)).strftime('%Y-%m-%dT%H:%M:%S')
c.post('/api/v1/reservations', json={'room_id': 1, 'user_id': 'alice', 'start_time': s1, 'end_time': e1})
c.post('/api/v1/reservations', json={'room_id': 2, 'user_id': 'bob', 'start_time': s2, 'end_time': e2})
r = c.get('/api/v1/reservations?room_id=1')
items = r.get_json()
assert all(i['room_id'] == 1 for i in items), f'Filter by room_id failed: {items}'
print('FILTER_BY_ROOM_ID_OK')
\"" "filter_by_room_id_fails"

  # 12. Attestation check
  check "python3 -c \"
import json, sys
att = json.load(open('$SUBMISSION/attestation.json'))
assert att.get('verdict') == 'pass', f'Attestation verdict: {att.get(\"verdict\")}'
\" " "bad_attestation"

elif [ "$DOMAIN" = "user_management" ]; then

  MAX_USER=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e['max_username_len'])" 2>/dev/null || echo "30")
  MAX_BIO=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e['max_bio_len'])" 2>/dev/null || echo "200")
  MIN_PWD=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e['min_password_len'])" 2>/dev/null || echo "8")
  ROLES_JSON=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(json.dumps(e['roles']))" 2>/dev/null || echo '["admin","viewer"]')
  FIRST_ROLE=$(python3 -c "import json; print(json.loads('$ROLES_JSON')[0])" 2>/dev/null || echo "admin")

  # 3. POST missing required field returns 400
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from app import app, store
store._users.clear(); store._next_id = 1
app.config['TESTING'] = True
c = app.test_client()
r = c.post('/api/v1/users', json={'username': 'alice'})
assert r.status_code == 400, f'Expected 400, got {r.status_code}'
print('MISSING_FIELD_400_OK')
\"" "missing_required_field_not_400"

  # 4. POST returns 201 and password NOT in response
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from app import app, store
store._users.clear(); store._next_id = 1
app.config['TESTING'] = True
c = app.test_client()
r = c.post('/api/v1/users', json={
    'username': 'alice_ok', 'email': 'alice@example.com',
    'password': 'supersecret99', 'role': '$FIRST_ROLE'
})
assert r.status_code == 201, f'Expected 201, got {r.status_code}: {r.get_data(as_text=True)}'
d = r.get_json()
assert 'password' not in d, 'password must NOT be in response'
for field in ('id', 'username', 'email', 'role', 'active'):
    assert field in d, f'Missing field: {field}'
assert d['active'] == True, f'active should default to True, got {d[\"active\"]}'
print('SCHEMA_NO_PASSWORD_OK')
\"" "password_in_response_or_schema_wrong"

  # 5. POST duplicate username (case-insensitive) returns 409 USERNAME_TAKEN
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from app import app, store
store._users.clear(); store._next_id = 1
app.config['TESTING'] = True
c = app.test_client()
c.post('/api/v1/users', json={'username': 'Alice', 'email': 'a@x.com', 'password': 'pass1234x', 'role': '$FIRST_ROLE'})
r = c.post('/api/v1/users', json={'username': 'alice', 'email': 'b@x.com', 'password': 'pass1234x', 'role': '$FIRST_ROLE'})
assert r.status_code == 409, f'Expected 409, got {r.status_code}'
d = r.get_json()
assert d.get('error') == 'USERNAME_TAKEN', f'Wrong code: {d.get(\"error\")}'
print('USERNAME_TAKEN_OK')
\"" "username_taken_wrong_code"

  # 6. POST invalid role returns 400 VALIDATION_ERROR
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from app import app, store
store._users.clear(); store._next_id = 1
app.config['TESTING'] = True
c = app.test_client()
r = c.post('/api/v1/users', json={
    'username': 'bob', 'email': 'bob@x.com', 'password': 'pass1234x', 'role': 'superadmin'
})
assert r.status_code == 400, f'Expected 400 for invalid role, got {r.status_code}'
d = r.get_json()
assert d.get('error') == 'VALIDATION_ERROR', f'Wrong code: {d.get(\"error\")}'
print('INVALID_ROLE_400_OK')
\"" "invalid_role_not_400"

  # 7. POST username with special chars (not alphanumeric/underscore) returns 400
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from app import app, store
store._users.clear(); store._next_id = 1
app.config['TESTING'] = True
c = app.test_client()
r = c.post('/api/v1/users', json={
    'username': 'alice@bad', 'email': 'ok@x.com', 'password': 'pass1234x', 'role': '$FIRST_ROLE'
})
assert r.status_code == 400, f'Expected 400 for invalid username chars, got {r.status_code}'
print('USERNAME_CHARS_VALIDATION_OK')
\"" "username_chars_not_validated"

  # 8. POST password shorter than min_password_len returns 400
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from app import app, store
store._users.clear(); store._next_id = 1
app.config['TESTING'] = True
c = app.test_client()
short_pwd = 'x' * ($MIN_PWD - 1)
r = c.post('/api/v1/users', json={
    'username': 'carol', 'email': 'carol@x.com', 'password': short_pwd, 'role': '$FIRST_ROLE'
})
assert r.status_code == 400, f'Expected 400 for short password ({$MIN_PWD-1} chars), got {r.status_code}'
print('SHORT_PASSWORD_400_OK')
\"" "short_password_not_rejected"

  # 9. GET user returns 404 USER_NOT_FOUND for missing user
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from app import app, store
store._users.clear(); store._next_id = 1
app.config['TESTING'] = True
c = app.test_client()
r = c.get('/api/v1/users/9999')
assert r.status_code == 404, f'Expected 404, got {r.status_code}'
d = r.get_json()
assert d.get('error') == 'USER_NOT_FOUND', f'Wrong code: {d.get(\"error\")}'
print('USER_NOT_FOUND_OK')
\"" "user_not_found_wrong_code"

  # 10. POST duplicate email (case-insensitive) returns 409 EMAIL_TAKEN
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from app import app, store
store._users.clear(); store._next_id = 1
app.config['TESTING'] = True
c = app.test_client()
c.post('/api/v1/users', json={'username': 'user1', 'email': 'Test@X.COM', 'password': 'pass1234x', 'role': '$FIRST_ROLE'})
r = c.post('/api/v1/users', json={'username': 'user2', 'email': 'test@x.com', 'password': 'pass1234x', 'role': '$FIRST_ROLE'})
assert r.status_code == 409, f'Expected 409 for duplicate email, got {r.status_code}'
d = r.get_json()
assert d.get('error') == 'EMAIL_TAKEN', f'Wrong code: {d.get(\"error\")}'
print('EMAIL_TAKEN_OK')
\"" "email_taken_wrong_code"

  # 11. PUT update is reflected; password field still not returned
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from app import app, store
store._users.clear(); store._next_id = 1
app.config['TESTING'] = True
c = app.test_client()
c.post('/api/v1/users', json={'username': 'dave', 'email': 'd@x.com', 'password': 'pass1234x', 'role': '$FIRST_ROLE'})
r = c.put('/api/v1/users/1', json={'bio': 'Hello!'})
assert r.status_code == 200, f'Expected 200, got {r.status_code}'
d = r.get_json()
assert d['bio'] == 'Hello!', f'Bio not updated: {d.get(\"bio\")}'
assert 'password' not in d, 'password must not appear in PUT response'
print('PUT_NO_PASSWORD_OK')
\"" "put_exposes_password_or_fails"

  # 12. Attestation check
  check "python3 -c \"
import json, sys
att = json.load(open('$SUBMISSION/attestation.json'))
assert att.get('verdict') == 'pass', f'Attestation verdict: {att.get(\"verdict\")}'
\" " "bad_attestation"

else
  # Domain: blog (seed % 5 == 4)

  MAX_TITLE=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e['max_title_len'])" 2>/dev/null || echo "150")
  MAX_TAGS=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e['max_tags_per_post'])" 2>/dev/null || echo "5")
  MAX_CONTENT_KB=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e['max_content_kb'])" 2>/dev/null || echo "50")
  MAX_CONTENT_BYTES=$((MAX_CONTENT_KB * 1024))

  # 3. Slug generation: spaces->hyphens, lowercase, strip special chars
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from app import app, store
store._tags.clear(); store._posts.clear(); store._tag_next_id = 1; store._post_next_id = 1
app.config['TESTING'] = True
c = app.test_client()
r = c.post('/api/v1/posts', json={'title': 'Hello, World! 2024', 'content': 'Body', 'author': 'alice'})
assert r.status_code == 201, f'Expected 201, got {r.status_code}: {r.get_data(as_text=True)}'
d = r.get_json()
assert d['slug'] == 'hello-world-2024', f'Wrong slug: {d[\"slug\"]}'
print('SLUG_GENERATION_OK')
\"" "slug_generation_wrong"

  # 4. Duplicate slug returns 409 DUPLICATE_SLUG
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from app import app, store
store._tags.clear(); store._posts.clear(); store._tag_next_id = 1; store._post_next_id = 1
app.config['TESTING'] = True
c = app.test_client()
c.post('/api/v1/posts', json={'title': 'My Post', 'content': 'A', 'author': 'alice'})
r = c.post('/api/v1/posts', json={'title': 'My Post', 'content': 'B', 'author': 'bob'})
assert r.status_code == 409, f'Expected 409 for duplicate slug, got {r.status_code}'
d = r.get_json()
assert d.get('error') == 'DUPLICATE_SLUG', f'Wrong code: {d.get(\"error\")}'
print('DUPLICATE_SLUG_OK')
\"" "duplicate_slug_not_409"

  # 5. POST with non-existent tag returns 404 TAG_NOT_FOUND
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from app import app, store
store._tags.clear(); store._posts.clear(); store._tag_next_id = 1; store._post_next_id = 1
app.config['TESTING'] = True
c = app.test_client()
r = c.post('/api/v1/posts', json={
    'title': 'Tagged post', 'content': 'Body', 'author': 'alice', 'tags': ['nonexistent']
})
assert r.status_code == 404, f'Expected 404, got {r.status_code}'
d = r.get_json()
assert d.get('error') == 'TAG_NOT_FOUND', f'Wrong code: {d.get(\"error\")}'
print('TAG_NOT_FOUND_OK')
\"" "tag_not_found_wrong_code"

  # 6. POST with existing tag succeeds; tags appear in response
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from app import app, store
store._tags.clear(); store._posts.clear(); store._tag_next_id = 1; store._post_next_id = 1
app.config['TESTING'] = True
c = app.test_client()
c.post('/api/v1/tags', json={'name': 'python'})
r = c.post('/api/v1/posts', json={
    'title': 'Python Tips', 'content': 'Body', 'author': 'alice', 'tags': ['python']
})
assert r.status_code == 201, f'Expected 201, got {r.status_code}'
d = r.get_json()
assert 'python' in d['tags'], f'Tag not in response: {d[\"tags\"]}'
print('TAG_IN_POST_OK')
\"" "tag_in_post_wrong"

  # 7. POST content exceeding max KB returns 400
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from app import app, store
store._tags.clear(); store._posts.clear(); store._tag_next_id = 1; store._post_next_id = 1
app.config['TESTING'] = True
c = app.test_client()
big_content = 'x' * ($MAX_CONTENT_BYTES + 1)
r = c.post('/api/v1/posts', json={
    'title': 'Big post', 'content': big_content, 'author': 'alice'
})
assert r.status_code == 400, f'Expected 400 for oversized content, got {r.status_code}'
print('CONTENT_SIZE_VALIDATION_OK')
\"" "content_size_not_validated"

  # 8. POST with invalid status returns 400
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from app import app, store
store._tags.clear(); store._posts.clear(); store._tag_next_id = 1; store._post_next_id = 1
app.config['TESTING'] = True
c = app.test_client()
r = c.post('/api/v1/posts', json={
    'title': 'Status test', 'content': 'Body', 'author': 'alice', 'status': 'INVALID_STATUS'
})
assert r.status_code == 400, f'Expected 400 for invalid status, got {r.status_code}'
print('INVALID_STATUS_400_OK')
\"" "invalid_status_not_rejected"

  # 9. Default status is 'draft' when not provided
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from app import app, store
store._tags.clear(); store._posts.clear(); store._tag_next_id = 1; store._post_next_id = 1
app.config['TESTING'] = True
c = app.test_client()
r = c.post('/api/v1/posts', json={'title': 'Draft post', 'content': 'Body', 'author': 'alice'})
assert r.status_code == 201, f'Expected 201, got {r.status_code}'
d = r.get_json()
assert d['status'] == 'draft', f'Default status should be draft, got {d[\"status\"]}'
print('DEFAULT_DRAFT_OK')
\"" "default_status_not_draft"

  # 10. PUT update regenerates slug when title changes
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from app import app, store
store._tags.clear(); store._posts.clear(); store._tag_next_id = 1; store._post_next_id = 1
app.config['TESTING'] = True
c = app.test_client()
c.post('/api/v1/posts', json={'title': 'Old Title', 'content': 'Body', 'author': 'alice'})
r = c.put('/api/v1/posts/1', json={'title': 'New Title Here'})
assert r.status_code == 200, f'Expected 200, got {r.status_code}'
d = r.get_json()
assert d['slug'] == 'new-title-here', f'Slug not regenerated: {d[\"slug\"]}'
print('SLUG_REGENERATED_OK')
\"" "slug_not_regenerated_on_title_update"

  # 11. GET /api/v1/posts?status=published filters correctly
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from app import app, store
store._tags.clear(); store._posts.clear(); store._tag_next_id = 1; store._post_next_id = 1
app.config['TESTING'] = True
c = app.test_client()
c.post('/api/v1/posts', json={'title': 'Draft One', 'content': 'Body', 'author': 'alice', 'status': 'draft'})
c.post('/api/v1/posts', json={'title': 'Published One', 'content': 'Body', 'author': 'bob', 'status': 'published'})
r = c.get('/api/v1/posts?status=published')
items = r.get_json()
assert all(i['status'] == 'published' for i in items), f'Filter failed: {items}'
assert len(items) == 1, f'Expected 1 published post, got {len(items)}'
print('FILTER_BY_STATUS_OK')
\"" "filter_by_status_fails"

  # 12. Attestation check
  check "python3 -c \"
import json, sys
att = json.load(open('$SUBMISSION/attestation.json'))
assert att.get('verdict') == 'pass', f'Attestation verdict: {att.get(\"verdict\")}'
\" " "bad_attestation"

fi

# ── Score ─────────────────────────────────────────────────────────────────────
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
    "partial_score": $PARTIAL,
    "domain": "$DOMAIN"
  },
  "failure_modes": $FM
}
JSON
