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

# 1. Test suite: all 8 tests pass
check "python3 -m pytest tests/test_app.py -q --tb=short 2>&1 | tail -1 | grep -qE '8 passed'" "tests_not_all_passing"

# 2. PUT /users/ correctly updates email
check "python3 -c \"
import json
from app.server import app, Request
from app.routes.users import handle_update_user
app._users['123']['email'] = 'alice@example.com'
req = Request('PUT', '/users/123', json.dumps({'email': 'new@test.com'}))
resp = handle_update_user(req, user_id='123')
assert resp.body['email'] == 'new@test.com', f'Email not updated: {resp.body[\"email\"]}'
app._users['123']['email'] = 'alice@example.com'
print('EMAIL_UPDATE_OK')
\"" "email_update_broken"

# 3. Order total correctly applies discount
check "python3 -c \"
from app.routes.orders import Order
from app.utils.cache import cache
cache.clear()
order = Order([('Widget', 10.0, 3)])
order.apply_discount(20)
assert order.total == 24.0, f'Expected 24.0, got {order.total}'
assert order.total == 24.0, f'Second call: {order.total}'
print('DISCOUNT_OK')
\"" "discount_calculation_wrong"

# 4. Report dates respect timezone
check "python3 -c \"
from datetime import datetime, timezone, timedelta
from app.utils.formatter import format_date
est = timezone(timedelta(hours=-5))
dt = datetime(2024, 12, 31, 23, 0, tzinfo=est)
result = format_date(dt)
assert result == '2024-12-31', f'Expected 2024-12-31, got {result}'
print('TIMEZONE_OK')
\"" "timezone_conversion_wrong"

# 5. Cache properly handled for orders
check "python3 -c \"
from app.utils.cache import cache
cache.clear()
from app.routes.orders import Order
order = Order([('A', 100.0, 1)])
t1 = order.total
order.apply_discount(50)
t2 = order.total
assert t2 == 50.0, f'Cache not invalidated: got {t2}'
print('CACHE_OK')
\"" "cache_not_invalidated"

# 6. No regressions
check "python3 -c \"
from app.server import app, Request
from app.routes.users import handle_get_user
resp = handle_get_user(Request('GET', '/users/123'), user_id='123')
assert resp.status == 200
assert resp.body['name'] == 'Alice'
print('NO_REGRESSION')
\"" "regression_detected"

# 7. Diff is < 25 lines (check files aren't completely rewritten)
check "python3 -c \"
import os
total = 0
for root, dirs, files in os.walk('app'):
    for f in files:
        if f.endswith('.py'):
            total += os.path.getsize(os.path.join(root, f))
# Original is ~3500 bytes
assert total < 6000, f'Too much code change: {total} bytes'
print('DIFF_OK')
\"" "excessive_changes"

# 8. users.py uses correct field name
check "python3 -c \"
with open('app/routes/users.py') as f:
    code = f.read()
assert 'get(\\\"email\\\")' in code or \"get('email')\" in code, 'users.py not using email field'
assert 'get(\\\"username\\\")' not in code and \"get('username')\" not in code, 'users.py still using username'
print('FIELD_NAME_OK')
\"" "wrong_field_name"

# 9. cache.py or orders.py handles discount-cache
check "python3 -c \"
with open('app/routes/orders.py') as f:
    orders_code = f.read()
with open('app/utils/cache.py') as f:
    cache_code = f.read()
has_fix = (
    'delete' in orders_code or 'clear' in orders_code or
    'invalidate' in cache_code or 'pop' in orders_code
)
assert has_fix, 'No evidence of cache fix in orders.py or cache.py'
print('CACHE_FIX_CHECK')
\"" "cache_fix_not_applied"

# 10. formatter.py applies timezone
check "python3 -c \"
with open('app/utils/formatter.py') as f:
    code = f.read()
# Should have timezone handling (astimezone, or tzinfo check)
assert 'astimezone' in code or 'tzinfo' in code, 'No timezone handling in formatter'
print('FORMATTER_OK')
\"" "no_timezone_handling"

# 11. Attestation
check "python3 -c \"
import json, sys
att = json.load(open(sys.argv[1]))
assert att.get('verdict') == 'pass'
\" '$SUBMISSION/attestation.json'" "bad_attestation"

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
