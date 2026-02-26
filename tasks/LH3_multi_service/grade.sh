#!/usr/bin/env bash
# grade.sh for LH3_multi_service
# Args: WORKSPACE REPORTS SUBMISSION TASK_DIR
# Runs 12+ checks covering: startup, health, contracts, data flow, error handling, partial scoring
set -o pipefail

WORKSPACE="$1"
REPORTS="$2"
SUBMISSION="$3"
TASK_DIR="$4"

mkdir -p "$REPORTS"

CHECKS=0; PASSED=0; FAILURES=""

check() {
  CHECKS=$((CHECKS + 1))
  local label="$2"
  if eval "$1" 2>/dev/null; then
    PASSED=$((PASSED + 1))
  else
    FAILURES="${FAILURES:+${FAILURES},}${label}"
  fi
}

cd "$WORKSPACE"

# ── Helper: load expected.json from REPORTS ────────────────────────────────
EXPECTED="$REPORTS/expected.json"

# ── 1. Each service server.py is syntactically valid Python ───────────────
for svc_dir in service_a service_b service_c service_d; do
  if [ -f "$svc_dir/server.py" ]; then
    check "python3 -m py_compile '$svc_dir/server.py'" "${svc_dir}_syntax_error"
  fi
done

# ── 2. Each service has a config.json that is valid JSON ──────────────────
for svc_dir in service_a service_b service_c service_d; do
  if [ -f "$svc_dir/config.json" ]; then
    check "python3 -c \"import json; json.load(open('$svc_dir/config.json'))\"" \
      "${svc_dir}_config_invalid_json"
  fi
done

# ── 3. Start all present services and verify they boot without crashing ────
# We start each service, wait briefly, check /health, then kill it.
PIDS=""
PORTS_STARTED=""

_start_service() {
  local svc="$1"
  local port
  port=$(python3 -c "import json; c=json.load(open('$svc/config.json')); print(c['port'])" 2>/dev/null || echo "")
  if [ -z "$port" ]; then return; fi
  python3 "$svc/server.py" >/tmp/"$svc".log 2>&1 &
  local pid=$!
  PIDS="$PIDS $pid"
  PORTS_STARTED="$PORTS_STARTED $port"
  sleep 0.8
  # Health check
  check "python3 -c \"
import urllib.request, json
resp = urllib.request.urlopen('http://localhost:$port/health', timeout=3)
data = json.loads(resp.read())
assert data.get('status') == 'ok', f'Bad health: {data}'
\"" "${svc}_health_fail"
}

for svc in service_a service_b service_c service_d; do
  if [ -d "$svc" ]; then
    _start_service "$svc"
  fi
done

sleep 0.5

# ── 4. Each service's health endpoint returns the correct service name ─────
for svc_dir in service_a service_b service_c service_d; do
  if [ -d "$svc_dir" ]; then
    port=$(python3 -c "import json; c=json.load(open('$svc_dir/config.json')); print(c['port'])" 2>/dev/null || echo "")
    if [ -n "$port" ]; then
      check "python3 -c \"
import urllib.request, json
resp = urllib.request.urlopen('http://localhost:$port/health', timeout=3)
data = json.loads(resp.read())
assert data.get('service') == '$svc_dir', f'Wrong service name: {data}'
\"" "${svc_dir}_health_wrong_name"
    fi
  fi
done

# ── 5. Entry service accepts POST /api/process and returns 200 ────────────
ENTRY_PORT=$(python3 -c "
import json, os
for svc in ['service_a']:
    cfg = json.load(open(f'{svc}/config.json'))
    print(cfg['port'])
    break
" 2>/dev/null || echo "")

if [ -n "$ENTRY_PORT" ]; then
  # Load id_field and data_field from expected.json if available
  ID_FIELD=$(python3 -c "
import json, sys
try:
    e = json.load(open('$EXPECTED'))
    domain = e.get('domain','payments')
    fields = {'payments':'payment_id','orders':'order_id','events':'event_id','users':'user_id','inventory':'product_id'}
    print(fields.get(domain,'payment_id'))
except: print('payment_id')
" 2>/dev/null || echo "payment_id")

  DATA_FIELD=$(python3 -c "
import json, sys
try:
    e = json.load(open('$EXPECTED'))
    domain = e.get('domain','payments')
    fields = {'payments':'amount','orders':'total','events':'payload','users':'user_data','inventory':'quantity'}
    print(fields.get(domain,'amount'))
except: print('amount')
" 2>/dev/null || echo "amount")

  check "python3 -c \"
import urllib.request, json
payload = json.dumps({'$ID_FIELD': 'grade-001', '$DATA_FIELD': 42}).encode()
req = urllib.request.Request(
    'http://localhost:$ENTRY_PORT/api/process',
    data=payload,
    headers={'Content-Type': 'application/json'},
    method='POST',
)
resp = urllib.request.urlopen(req, timeout=10)
assert resp.status == 200, f'Expected 200 got {resp.status}'
data = json.loads(resp.read())
assert 'error' not in data or data.get('result') is not None, f'Response has error: {data}'
\"" "entry_service_e2e_fail"

  # ── 6. End-to-end response contains result field ──────────────────────
  check "python3 -c \"
import urllib.request, json
payload = json.dumps({'$ID_FIELD': 'grade-002', '$DATA_FIELD': 99}).encode()
req = urllib.request.Request(
    'http://localhost:$ENTRY_PORT/api/process',
    data=payload,
    headers={'Content-Type': 'application/json'},
    method='POST',
)
resp = urllib.request.urlopen(req, timeout=10)
data = json.loads(resp.read())
assert 'result' in data, f'Missing result field: {data}'
\"" "e2e_missing_result_field"

  # ── 7. Second request succeeds (no state corruption) ─────────────────
  check "python3 -c \"
import urllib.request, json
for i in range(2):
    payload = json.dumps({'$ID_FIELD': f'grade-seq-{i}', '$DATA_FIELD': i*10}).encode()
    req = urllib.request.Request(
        'http://localhost:$ENTRY_PORT/api/process',
        data=payload,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    resp = urllib.request.urlopen(req, timeout=10)
    assert resp.status == 200, f'Request {i} failed with {resp.status}'
\"" "sequential_requests_fail"

  # ── 8. Malformed request returns graceful error (not 500) ─────────────
  check "python3 -c \"
import urllib.request, json
payload = b'not-json'
req = urllib.request.Request(
    'http://localhost:$ENTRY_PORT/api/process',
    data=payload,
    headers={'Content-Type': 'application/json'},
    method='POST',
)
try:
    resp = urllib.request.urlopen(req, timeout=5)
    code = resp.status
except urllib.error.HTTPError as e:
    code = e.code
assert code in (400, 422, 200), f'Expected graceful error, got {code}'
\"" "malformed_request_crashes"
fi

# ── 9. Check inter-service URLs are correct (static analysis) ─────────────
# Read expected contracts from expected.json and verify server.py uses correct URLs
if [ -f "$EXPECTED" ]; then
  check "python3 -c \"
import json, re, sys

expected = json.load(open('$EXPECTED'))
contracts = expected.get('edge_contracts', {})
topology = expected.get('topology', 'chain')
num_services = expected.get('num_services', 3)

errors = []
for edge_key, contract in contracts.items():
    # edge_key is like 'service_a_to_service_b'
    parts = edge_key.split('_to_')
    if len(parts) != 2:
        continue
    caller = parts[0]
    correct_ep = contract.get('correct_endpoint', '')
    wrong_ep   = contract.get('wrong_endpoint', '')
    if not correct_ep or not wrong_ep:
        continue
    server_path = f'{caller}/server.py'
    try:
        src = open(server_path).read()
    except FileNotFoundError:
        continue
    # The correct endpoint must appear, the wrong one must not
    if correct_ep not in src:
        errors.append(f'{caller}: missing correct endpoint {correct_ep}')
    if wrong_ep in src and correct_ep not in src:
        errors.append(f'{caller}: still uses wrong endpoint {wrong_ep}')

assert not errors, 'Endpoint URL bugs: ' + '; '.join(errors)
\"" "wrong_endpoint_urls_remain"

  # ── 10. Correct response field names used ────────────────────────────
  check "python3 -c \"
import json, re

expected = json.load(open('$EXPECTED'))
contracts = expected.get('edge_contracts', {})
errors = []

for edge_key, contract in contracts.items():
    parts = edge_key.split('_to_')
    if len(parts) != 2:
        continue
    caller = parts[0]
    correct_field = contract.get('correct_field', '')
    wrong_field   = contract.get('wrong_field', '')
    if not correct_field or not wrong_field or correct_field == wrong_field:
        continue
    server_path = f'{caller}/server.py'
    try:
        src = open(server_path).read()
    except FileNotFoundError:
        continue
    # Check that wrong_field is not used where correct_field should be
    # We look for resp.get(\"wrong_field\") which would be the bug
    bug_pattern = f'resp.get(\"{wrong_field}\")'
    fix_pattern = f'resp.get(\"{correct_field}\")'
    if bug_pattern in src and fix_pattern not in src:
        errors.append(f'{caller}: still reads wrong field \"{wrong_field}\" instead of \"{correct_field}\"')

assert not errors, 'Wrong response fields: ' + '; '.join(errors)
\"" "wrong_response_fields_remain"

  # ── 11. Error handling present in services that had missing_error_handling bug ──
  check "python3 -c \"
import json

expected = json.load(open('$EXPECTED'))
bugs = expected.get('bugs', {})
errors = []

for svc, bug_info in bugs.items():
    bug_types = bug_info.get('types', [bug_info.get('type', '')])
    if 'missing_error_handling' in bug_types:
        server_path = f'{svc}/server.py'
        try:
            src = open(server_path).read()
        except FileNotFoundError:
            continue
        if 'try:' not in src or 'except' not in src:
            errors.append(f'{svc}: missing_error_handling bug not fixed (no try/except found)')

assert not errors, '; '.join(errors)
\"" "missing_error_handling_not_fixed"

  # ── 12. Correct HTTP methods used ────────────────────────────────────
  check "python3 -c \"
import json

expected = json.load(open('$EXPECTED'))
bugs = expected.get('bugs', {})
contracts = expected.get('edge_contracts', {})
errors = []

for edge_key, contract in contracts.items():
    parts = edge_key.split('_to_')
    if len(parts) != 2:
        continue
    caller = parts[0]
    bug_info = bugs.get(caller, {})
    bug_types = bug_info.get('types', [bug_info.get('type', '')])
    if 'wrong_http_method' not in bug_types:
        continue
    wrong_method  = contract.get('wrong_method', 'GET')
    correct_method = contract.get('correct_method', 'POST')
    server_path = f'{caller}/server.py'
    try:
        src = open(server_path).read()
    except FileNotFoundError:
        continue
    # Check method= argument in _http_post call
    bug_str = f'method=\"{wrong_method}\"'
    fix_str = f'method=\"{correct_method}\"'
    if bug_str in src and fix_str not in src:
        errors.append(f'{caller}: still uses wrong HTTP method {wrong_method} instead of {correct_method}')

assert not errors, '; '.join(errors)
\"" "wrong_http_methods_remain"
fi

# ── Kill all started services ─────────────────────────────────────────────
for pid in $PIDS; do
  kill "$pid" 2>/dev/null || true
done
wait 2>/dev/null || true

# ── Scoring ───────────────────────────────────────────────────────────────
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
