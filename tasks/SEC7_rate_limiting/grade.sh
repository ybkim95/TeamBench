#!/usr/bin/env bash
set -o pipefail
WORKSPACE="$1"; REPORTS="$2"; SUBMISSION="$3"; TASK_DIR="$4"

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

# ── 1. Syntax check ───────────────────────────────────────────────────────────
check "python3 -c \"
import py_compile, os
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ('__pycache__', '.git')]
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            py_compile.compile(path, doraise=True)
print('SYNTAX_OK')
\"" "syntax_error"

# ── 2. Rate limiting logic exists in app.py ───────────────────────────────────
check "python3 -c \"
with open('app.py') as f:
    code = f.read()
import re
# Must have counter/window tracking: time.time(), _rate_state usage, 429
has_time       = bool(re.search(r'time\.time\(\)', code))
has_rate_state = bool(re.search(r'_rate_state', code))
has_429        = '429' in code
# Also accept: check_count, window_start, request_count, counter
has_counter    = bool(re.search(r'(count|counter|window_start|request_count)', code))
assert has_time or (has_rate_state and has_counter), \
    'No time-based rate limiting logic found in app.py'
assert has_429, 'HTTP 429 not referenced in app.py'
print('RATE_LIMIT_LOGIC_EXISTS')
\"" "rate_limit_logic_missing"

# ── 3. X-RateLimit headers are set on responses ───────────────────────────────
check "python3 -c \"
with open('app.py') as f:
    code = f.read()
import re
has_limit_hdr     = bool(re.search(r'X-RateLimit-Limit', code))
has_remaining_hdr = bool(re.search(r'X-RateLimit-Remaining', code))
has_reset_hdr     = bool(re.search(r'X-RateLimit-Reset', code))
assert has_limit_hdr,     'X-RateLimit-Limit header not set in app.py'
assert has_remaining_hdr, 'X-RateLimit-Remaining header not set in app.py'
assert has_reset_hdr,     'X-RateLimit-Reset header not set in app.py'
print('RATE_LIMIT_HEADERS_SET')
\"" "rate_limit_headers_missing"

# ── 4. 401 returned for unauthenticated requests ──────────────────────────────
check "python3 -c \"
import subprocess, sys, os, time, signal, json

ws = os.getcwd()
# Start server in background
proc = subprocess.Popen(
    [sys.executable, 'app.py'],
    cwd=ws, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
)
time.sleep(1.5)
try:
    import urllib.request, urllib.error
    # Try each common endpoint path until we get a response
    paths = ['/api/search', '/api/query', '/api/lookup', '/api/items', '/api/records', '/api/products']
    got_401 = False
    for path in paths:
        try:
            req = urllib.request.Request('http://127.0.0.1:5000' + path)
            try:
                urllib.request.urlopen(req, timeout=3)
            except urllib.error.HTTPError as e:
                if e.code == 401:
                    got_401 = True
                    break
        except Exception:
            continue
    assert got_401, 'No endpoint returned 401 for unauthenticated request'
    print('UNAUTHENTICATED_REJECTED_401')
finally:
    proc.terminate()
    proc.wait()
\"" "unauthenticated_not_rejected"

# ── 5. Valid API key is accepted (200) ────────────────────────────────────────
check "python3 -c \"
import subprocess, sys, os, time, json, ast

ws = os.getcwd()
# Extract first non-internal API key and header from app.py
with open('app.py') as f:
    code = f.read()
import re
# Find the API_KEYS dict literal and extract first key
m = re.search(r'API_KEYS\s*=\s*\{([^}]+)\}', code, re.DOTALL)
assert m, 'Cannot find API_KEYS dict in app.py'
keys_block = m.group(1)
# Extract first key string
key_m = re.search(r'\"([^\"]+)\"', keys_block)
assert key_m, 'No API key found in API_KEYS'
first_key = key_m.group(1)

# Find API key header name
hdr_m = re.search(r'headers\.get\s*\(\s*\"([^\"]+)\"', code)
assert hdr_m, 'Cannot find API key header name in app.py'
api_hdr = hdr_m.group(1)

# Start server
proc = subprocess.Popen(
    [sys.executable, 'app.py'],
    cwd=ws, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
)
time.sleep(1.5)
try:
    import urllib.request, urllib.error
    paths = ['/api/search', '/api/query', '/api/lookup', '/api/items', '/api/records', '/api/products']
    got_200 = False
    for path in paths:
        try:
            req = urllib.request.Request('http://127.0.0.1:5000' + path,
                                          headers={api_hdr: first_key})
            try:
                resp = urllib.request.urlopen(req, timeout=3)
                if resp.status == 200:
                    got_200 = True
                    break
            except urllib.error.HTTPError as e:
                if e.code == 200:
                    got_200 = True
                    break
        except Exception:
            continue
    assert got_200, f'No endpoint returned 200 for valid key {first_key!r} via header {api_hdr!r}'
    print('VALID_KEY_ACCEPTED')
finally:
    proc.terminate()
    proc.wait()
\"" "valid_key_rejected"

# ── 6. Rate limit enforced: exceeding limit returns 429 ───────────────────────
check "python3 -c \"
import subprocess, sys, os, time, re

ws = os.getcwd()
with open('app.py') as f:
    code = f.read()

# Extract first key and tier limit
m = re.search(r'API_KEYS\s*=\s*\{([^}]+)\}', code, re.DOTALL)
assert m, 'Cannot find API_KEYS'
keys_block = m.group(1)
key_m = re.search(r'\"([^\"]+)\"', keys_block)
first_key = key_m.group(1)

hdr_m = re.search(r'headers\.get\s*\(\s*\"([^\"]+)\"', code)
api_hdr = hdr_m.group(1)

proc = subprocess.Popen(
    [sys.executable, 'app.py'],
    cwd=ws, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
)
time.sleep(1.5)
try:
    import urllib.request, urllib.error
    # Find a working path
    paths = ['/api/search', '/api/query', '/api/lookup', '/api/items', '/api/records', '/api/products']
    working_path = None
    for path in paths:
        try:
            req = urllib.request.Request('http://127.0.0.1:5000' + path,
                                          headers={api_hdr: first_key})
            resp = urllib.request.urlopen(req, timeout=3)
            if resp.status == 200:
                working_path = path
                break
        except urllib.error.HTTPError as e:
            if e.code == 200:
                working_path = path
                break
        except Exception:
            continue
    assert working_path, 'No working endpoint found'

    # Read limit from header
    req = urllib.request.Request('http://127.0.0.1:5000' + working_path,
                                  headers={api_hdr: first_key})
    try:
        resp = urllib.request.urlopen(req, timeout=3)
        limit = int(resp.headers.get('X-RateLimit-Limit', '0'))
    except urllib.error.HTTPError as e:
        limit = int(e.headers.get('X-RateLimit-Limit', '0'))

    assert limit > 0, f'X-RateLimit-Limit not set or zero; got {limit}'
    assert limit <= 200, f'Limit {limit} too high to test exhaustion (cap 200)'

    # Exhaust the limit (already made 1 request)
    got_429 = False
    for i in range(limit + 5):
        req2 = urllib.request.Request('http://127.0.0.1:5000' + working_path,
                                       headers={api_hdr: first_key})
        try:
            urllib.request.urlopen(req2, timeout=3)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                got_429 = True
                break
    assert got_429, f'Never got 429 after {limit+5} requests on tier with limit {limit}'
    print('RATE_LIMIT_ENFORCED_429')
finally:
    proc.terminate()
    proc.wait()
\"" "rate_limit_not_enforced"

# ── 7. 429 response body has error and retry_after ───────────────────────────
check "python3 -c \"
import subprocess, sys, os, time, re, json

ws = os.getcwd()
with open('app.py') as f:
    code = f.read()

m = re.search(r'API_KEYS\s*=\s*\{([^}]+)\}', code, re.DOTALL)
keys_block = m.group(1)
key_m = re.search(r'\"([^\"]+)\"', keys_block)
first_key = key_m.group(1)
hdr_m = re.search(r'headers\.get\s*\(\s*\"([^\"]+)\"', code)
api_hdr = hdr_m.group(1)

proc = subprocess.Popen(
    [sys.executable, 'app.py'],
    cwd=ws, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
)
time.sleep(1.5)
try:
    import urllib.request, urllib.error
    paths = ['/api/search', '/api/query', '/api/lookup', '/api/items', '/api/records', '/api/products']
    working_path = None
    for path in paths:
        try:
            req = urllib.request.Request('http://127.0.0.1:5000' + path,
                                          headers={api_hdr: first_key})
            resp = urllib.request.urlopen(req, timeout=3)
            if resp.status == 200:
                limit = int(resp.headers.get('X-RateLimit-Limit', '0'))
                if 0 < limit <= 200:
                    working_path = path
                    break
        except urllib.error.HTTPError as e:
            if e.code == 200:
                limit = int(e.headers.get('X-RateLimit-Limit', '0'))
                if 0 < limit <= 200:
                    working_path = path
                    break
        except Exception:
            continue

    assert working_path, 'No working endpoint with finite limit found'

    # Exhaust limit
    body_429 = None
    for _ in range(limit + 10):
        req2 = urllib.request.Request('http://127.0.0.1:5000' + working_path,
                                       headers={api_hdr: first_key})
        try:
            urllib.request.urlopen(req2, timeout=3)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                raw = e.read()
                body_429 = json.loads(raw)
                break

    assert body_429 is not None, '429 response not received'
    assert 'error' in body_429, f'429 body missing error key: {body_429}'
    assert 'retry_after' in body_429, f'429 body missing retry_after key: {body_429}'
    print('429_BODY_FORMAT_OK')
finally:
    proc.terminate()
    proc.wait()
\"" "429_body_missing_fields"

# ── 8. X-RateLimit-Remaining decrements ───────────────────────────────────────
check "python3 -c \"
import subprocess, sys, os, time, re

ws = os.getcwd()
with open('app.py') as f:
    code = f.read()

m = re.search(r'API_KEYS\s*=\s*\{([^}]+)\}', code, re.DOTALL)
keys_block = m.group(1)
key_m = re.search(r'\"([^\"]+)\"', keys_block)
first_key = key_m.group(1)
hdr_m = re.search(r'headers\.get\s*\(\s*\"([^\"]+)\"', code)
api_hdr = hdr_m.group(1)

proc = subprocess.Popen(
    [sys.executable, 'app.py'],
    cwd=ws, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
)
time.sleep(1.5)
try:
    import urllib.request, urllib.error
    paths = ['/api/search', '/api/query', '/api/lookup', '/api/items', '/api/records', '/api/products']
    remaining_vals = []
    for path in paths:
        remaining_vals = []
        try:
            for _ in range(3):
                req = urllib.request.Request('http://127.0.0.1:5000' + path,
                                              headers={api_hdr: first_key})
                try:
                    resp = urllib.request.urlopen(req, timeout=3)
                    remaining_vals.append(int(resp.headers.get('X-RateLimit-Remaining', -1)))
                except urllib.error.HTTPError as e:
                    if e.code == 200:
                        remaining_vals.append(int(e.headers.get('X-RateLimit-Remaining', -1)))
            if len(remaining_vals) >= 2 and remaining_vals[0] != -1:
                break
        except Exception:
            continue

    assert len(remaining_vals) >= 3, f'Could not collect 3 responses: {remaining_vals}'
    assert remaining_vals[0] > remaining_vals[1], \
        f'Remaining did not decrement: {remaining_vals}'
    assert remaining_vals[1] > remaining_vals[2], \
        f'Remaining did not decrement on 3rd request: {remaining_vals}'
    print('REMAINING_DECREMENTS_OK')
finally:
    proc.terminate()
    proc.wait()
\"" "remaining_not_decrementing"

# ── 9. Unlimited tier never gets 429 ─────────────────────────────────────────
check "python3 -c \"
import subprocess, sys, os, time, re

ws = os.getcwd()
with open('app.py') as f:
    code = f.read()

# Extract internal/unlimited key — always last tier, key named 'key-{tier}-001'
# Find all keys and pick one containing 'internal'
m = re.search(r'API_KEYS\s*=\s*\{([^}]+)\}', code, re.DOTALL)
keys_block = m.group(1)
internal_key_m = re.search(r'\"(key-internal[^\"]*|key-[^\"]*-001)\"', keys_block)
# Get all keys
all_keys = re.findall(r'\"(key-[^\"]+)\"', keys_block)
# Last key in dict corresponds to internal/unlimited tier
assert all_keys, 'No API keys found'
internal_key = all_keys[-1]

hdr_m = re.search(r'headers\.get\s*\(\s*\"([^\"]+)\"', code)
api_hdr = hdr_m.group(1)

proc = subprocess.Popen(
    [sys.executable, 'app.py'],
    cwd=ws, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
)
time.sleep(1.5)
try:
    import urllib.request, urllib.error
    # Make 60 requests with internal key
    got_429 = False
    for i in range(60):
        req = urllib.request.Request('http://127.0.0.1:5000/api/health',
                                      headers={api_hdr: internal_key})
        try:
            urllib.request.urlopen(req, timeout=3)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                got_429 = True
                break
        except Exception:
            break
    assert not got_429, f'Internal/unlimited tier received 429 — must never be blocked'
    print('UNLIMITED_TIER_NEVER_429')
finally:
    proc.terminate()
    proc.wait()
\"" "unlimited_tier_gets_429"

# ── 10. Health endpoint always returns 200 ────────────────────────────────────
check "python3 -c \"
import subprocess, sys, os, time

ws = os.getcwd()
proc = subprocess.Popen(
    [sys.executable, 'app.py'],
    cwd=ws, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
)
time.sleep(1.5)
try:
    import urllib.request
    resp = urllib.request.urlopen('http://127.0.0.1:5000/api/health', timeout=3)
    assert resp.status == 200, f'Health endpoint returned {resp.status}'
    print('HEALTH_ALWAYS_200')
finally:
    proc.terminate()
    proc.wait()
\"" "health_endpoint_broken"

# ── 11. app.py still importable without errors ───────────────────────────────
check "python3 -c \"
import importlib.util, sys, os
spec = importlib.util.spec_from_file_location('app', os.path.join(os.getcwd(), 'app.py'))
mod = importlib.util.module_from_spec(spec)
# Override app.run to prevent server start
import flask
orig_run = flask.Flask.run
flask.Flask.run = lambda *a, **k: None
try:
    spec.loader.exec_module(mod)
finally:
    flask.Flask.run = orig_run
assert hasattr(mod, 'app'), 'app object missing from app.py'
assert hasattr(mod, '_rate_state'), '_rate_state dict missing from app.py'
print('APP_IMPORTABLE_OK')
\"" "app_not_importable"

# ── 12. No external rate-limiting libraries added ─────────────────────────────
check "python3 -c \"
with open('requirements.txt') as f:
    reqs = f.read().lower()
# Must not add flask-limiter, limits, redis, slowapi, etc.
forbidden = ['flask-limiter', 'flask_limiter', 'slowapi', 'limits']
for pkg in forbidden:
    assert pkg not in reqs, f'Forbidden external package {pkg!r} found in requirements.txt'
print('NO_FORBIDDEN_PACKAGES')
\"" "forbidden_package_added"

# ── 13. No new dangerous calls introduced ────────────────────────────────────
check "python3 -c \"
import os
for fname in ('app.py',):
    fpath = os.path.join(os.getcwd(), fname)
    if not os.path.exists(fpath):
        continue
    with open(fpath) as f:
        code = f.read()
    assert 'eval(' not in code,      f'eval() found in {fname}'
    assert 'exec(' not in code,      f'exec() found in {fname}'
    assert '__import__' not in code, f'__import__ found in {fname}'
    assert 'os.system(' not in code, f'os.system() found in {fname}'
print('NO_NEW_VULNS')
\"" "new_vulnerability_introduced"

# ── 14. Tests pass (pytest) ───────────────────────────────────────────────────
check "python3 -m pytest tests/test_rate_limiting.py -x -q --tb=no 2>&1 | tail -5 | grep -E '(passed|no tests ran)'" \
  "tests_failing"

# ── 15. Attestation check ─────────────────────────────────────────────────────
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
