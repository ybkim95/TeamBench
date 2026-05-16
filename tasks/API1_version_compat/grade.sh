#!/usr/bin/env bash
# API1_version_compat grader
set -uo pipefail

WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
REPORTS="${2:-${REPORTS_DIR:-/reports}}"
SUBMISSION="${3:-/submission}"
TASK_DIR="${4:-/task}"

source /usr/local/lib/venv/bin/activate 2>/dev/null || true

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

cd "${WORKSPACE}"

# ── Install dependencies ──────────────────────────────────────────────
pip install flask pytest 2>/dev/null || true

# Load expected values
EXPECTED_JSON="${REPORTS}/expected.json"
E1_V1_FIELD=$(python3 -c "import json; d=json.load(open('${EXPECTED_JSON}')); print(d.get('e1_v1_field', 'full_name'))" 2>/dev/null || echo "full_name")
E1_V2_FIELD=$(python3 -c "import json; d=json.load(open('${EXPECTED_JSON}')); print(d.get('e1_v2_field', 'display_name'))" 2>/dev/null || echo "display_name")
E3_PARAM=$(python3 -c "import json; d=json.load(open('${EXPECTED_JSON}')); print(d.get('e3_v2_param', 'page'))" 2>/dev/null || echo "page")
E3_DEFAULT=$(python3 -c "import json; d=json.load(open('${EXPECTED_JSON}')); print(d.get('e3_v1_default', '1'))" 2>/dev/null || echo "1")

# ── C1: v1 compat tests pass ─────────────────────────────────────────
if python3 -m pytest tests/test_v1_compat.py -q --tb=no 2>/dev/null | grep -q "passed"; then
    check "C1" "v1 compatibility tests pass" "pass"
else
    check "C1" "v1 compatibility tests failed" "fail"
fi

# ── C2: v2 regression tests pass ─────────────────────────────────────
if python3 -m pytest tests/test_v2_endpoints.py -q --tb=no 2>/dev/null | grep -q "passed"; then
    check "C2" "v2 regression tests pass" "pass"
else
    check "C2" "v2 regression tests failed" "fail"
fi

# ── C3: E1 v1 shim — uses old field name ─────────────────────────────
result=$(python3 -c "
import sys
sys.path.insert(0, '.')
from app import app
client = app.test_client()
app.config['TESTING'] = True
# Try common path patterns for E1
for path in ['/v1/users/1', '/v1/products/1', '/v1/orders/1', '/v1/reports/1', '/v1/auth/session/abc']:
    resp = client.get(path)
    if resp.status_code == 200:
        data = resp.get_json() or {}
        if '${E1_V1_FIELD}' in data:
            print('pass')
            break
        elif '${E1_V2_FIELD}' in data:
            print('fail')
            break
else:
    print('fail')
" 2>/dev/null || echo "fail")
check "C3" "E1 v1 shim: response uses old field '${E1_V1_FIELD}'" "${result}"

# ── C4: E1 v1 shim — does NOT include new field name ─────────────────
result=$(python3 -c "
import sys
sys.path.insert(0, '.')
from app import app
client = app.test_client()
app.config['TESTING'] = True
for path in ['/v1/users/1', '/v1/products/1', '/v1/orders/1', '/v1/reports/1', '/v1/auth/session/abc']:
    resp = client.get(path)
    if resp.status_code == 200:
        data = resp.get_json() or {}
        if '${E1_V2_FIELD}' not in data:
            print('pass')
        else:
            print('fail')
        break
else:
    print('fail')
" 2>/dev/null || echo "fail")
check "C4" "E1 v1 shim: response does not contain new field '${E1_V2_FIELD}'" "${result}"

# ── C5: E2 v1 shim — flat response (no nested dict values) ───────────
result=$(python3 -c "
import sys
sys.path.insert(0, '.')
from app import app
client = app.test_client()
app.config['TESTING'] = True
for path in ['/v1/users/1/preferences', '/v1/products/1/pricing', '/v1/orders/1/items',
             '/v1/reports/1/summary', '/v1/auth/session/abc/claims']:
    resp = client.get(path)
    if resp.status_code == 200:
        data = resp.get_json() or {}
        nested = [k for k, v in data.items() if isinstance(v, dict)]
        print('pass' if not nested else 'fail')
        break
else:
    print('fail')
" 2>/dev/null || echo "fail")
check "C5" "E2 v1 shim: response is flat (no nested dict values)" "${result}"

# ── C6: E3 v1 shim — works without required param ────────────────────
result=$(python3 -c "
import sys
sys.path.insert(0, '.')
from app import app
client = app.test_client()
app.config['TESTING'] = True
for path in ['/v1/users/search', '/v1/products/search', '/v1/orders/history',
             '/v1/reports/list', '/v1/auth/verify']:
    resp = client.get(path)
    if resp.status_code in (200, 404):
        print('pass' if resp.status_code == 200 else 'fail')
        break
else:
    print('fail')
" 2>/dev/null || echo "fail")
check "C6" "E3 v1 shim: works without '${E3_PARAM}' parameter" "${result}"

# ── C7: E4 — no v1 shim exists (returns 404) ─────────────────────────
result=$(python3 -c "
import sys
sys.path.insert(0, '.')
from app import app
client = app.test_client()
app.config['TESTING'] = True
for path in ['/v1/users/1/tokens', '/v1/products/1/inventory', '/v1/orders/1/cancel',
             '/v1/reports/1/raw', '/v1/auth/admin/sessions']:
    resp = client.get(path)
    if resp.status_code in (200, 401, 403, 404):
        print('pass' if resp.status_code == 404 else 'fail')
        break
else:
    print('pass')  # not found at all = 404 = correct
" 2>/dev/null || echo "fail")
check "C7" "E4 no-shim: v1 security endpoint returns 404" "${result}"

# ── C8: E5 — stale shim removed (returns 404) ────────────────────────
result=$(python3 -c "
import sys
sys.path.insert(0, '.')
from app import app
client = app.test_client()
app.config['TESTING'] = True
for path in ['/v1/users/legacy_export', '/v1/products/v1_bulk', '/v1/orders/legacy_status',
             '/v1/reports/v1_download', '/v1/auth/legacy_login']:
    resp = client.get(path)
    if resp.status_code in (200, 404):
        print('pass' if resp.status_code == 404 else 'fail')
        break
else:
    print('pass')
" 2>/dev/null || echo "fail")
check "C8" "E5 stale shim removed: legacy v1 path returns 404" "${result}"

# ── C9: E4 v2 still enforces authentication ───────────────────────────
result=$(python3 -c "
import sys
sys.path.insert(0, '.')
from app import app
client = app.test_client()
app.config['TESTING'] = True
for path in ['/v2/users/1/tokens', '/v2/products/1/inventory', '/v2/orders/1/cancel',
             '/v2/reports/1/raw', '/v2/auth/admin/sessions']:
    resp = client.get(path)
    if resp.status_code in (200, 401, 403, 404):
        print('pass' if resp.status_code == 401 else 'fail')
        break
else:
    print('fail')
" 2>/dev/null || echo "fail")
check "C9" "E4 v2: unauthenticated request returns 401" "${result}"

# ── C10: app.py imports and loads without error ───────────────────────
result=$(python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from app import app
    assert app is not None
    print('pass')
except Exception as e:
    print('fail')
" 2>/dev/null || echo "fail")
check "C10" "app.py imports and Flask app initializes without error" "${result}"

partial_score=$(python3 -c "print(round($partial / $total, 2))")
findings="${findings%,}"

mkdir -p "${REPORTS}"
cat > "${REPORTS}/score.json" <<EOF
{
  "pass": $( [ "$pass" = "true" ] && echo "true" || echo "false" ),
  "secondary": {
    "partial_score": $partial_score,
    "checks_passed": $partial,
    "checks_total": $total
  },
  "failure_modes": [],
  "checklist": [$findings]
}
EOF
