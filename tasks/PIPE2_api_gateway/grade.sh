#!/usr/bin/env bash
# Seed-aware grader for PIPE2: API Gateway Routing Fix
#
# Args: $1=WORKSPACE $2=REPORTS $3=SUBMISSION $4=TASK_DIR [$5=EXPECTED_JSON]
set -o pipefail
WORKSPACE="$1"
REPORTS="$2"
SUBMISSION="$3"
TASK_DIR="$4"
EXPECTED="${5:-$REPORTS/expected.json}"

mkdir -p "$REPORTS"

# Prefer venv python (has pytest); fall back to system python3
PYTHON="${PYTHON:-}"
if [ -z "$PYTHON" ]; then
  for candidate in \
      "$(dirname "$0")/../../../../venv/bin/python" \
      "<HOME>/TeamBench/venv/bin/python" \
      "python3"; do
    if "$candidate" -m pytest --version >/dev/null 2>&1; then
      PYTHON="$candidate"
      break
    fi
  done
  PYTHON="${PYTHON:-python3}"
fi

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

# ── Check 1: config.json exists and is valid JSON ─────────────────────────────
check "python3 -c \"
import json
with open('gateway/config.json', 'r') as f:
    cfg = json.load(f)
assert isinstance(cfg, dict), 'config.json must be a JSON object'
assert 'routes' in cfg, 'config.json must have routes key'
assert 'services' in cfg, 'config.json must have services key'
print('CONFIG_VALID')
\"" "config_json_invalid"

# ── Check 2: router.py imports without error ──────────────────────────────────
check "python3 -c \"
import sys, os
sys.path.insert(0, 'gateway')
import router
print('ROUTER_IMPORTS_OK')
\"" "router_import_error"

# Only run deeper checks if config loads
if python3 -c "import json; json.load(open('gateway/config.json'))" 2>/dev/null; then

# ── Check 3: All correct upstreams present ────────────────────────────────────
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
cfg = json.load(open('gateway/config.json'))

correct = {r['path_prefix']: r['upstream'] for r in expected['correct_routes']}
actual  = {r['path_prefix']: r['upstream'] for r in cfg['routes']}

errors = []
for path, upstream in correct.items():
    got = actual.get(path)
    if got != upstream:
        errors.append(f'{path}: upstream should be {upstream!r}, got {got!r}')
assert not errors, 'Wrong upstreams: ' + '; '.join(errors)
print('UPSTREAMS_OK')
\"" "wrong_upstreams"

# ── Check 4: All path rewrites correct ───────────────────────────────────────
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
cfg = json.load(open('gateway/config.json'))

correct = {r['path_prefix']: r['path_rewrite'] for r in expected['correct_routes']}
actual  = {r['path_prefix']: r['path_rewrite'] for r in cfg['routes']}

errors = []
for path, rewrite in correct.items():
    got = actual.get(path)
    if got != rewrite:
        errors.append(f'{path}: path_rewrite should be {rewrite!r}, got {got!r}')
assert not errors, 'Wrong path rewrites: ' + '; '.join(errors)
print('PATH_REWRITES_OK')
\"" "wrong_path_rewrites"

# ── Check 5: All auth methods correct ────────────────────────────────────────
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
cfg = json.load(open('gateway/config.json'))

correct = {r['path_prefix']: r['auth'] for r in expected['correct_routes']}
actual  = {r['path_prefix']: r['auth'] for r in cfg['routes']}

errors = []
for path, auth in correct.items():
    got = actual.get(path)
    if got != auth:
        errors.append(f'{path}: auth should be {auth!r}, got {got!r}')
assert not errors, 'Wrong auth methods: ' + '; '.join(errors)
print('AUTH_METHODS_OK')
\"" "wrong_auth_methods"

# ── Check 6: All rate limit tiers correct ────────────────────────────────────
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
cfg = json.load(open('gateway/config.json'))

correct = {r['path_prefix']: r['rate_limit_tier'] for r in expected['correct_routes']}
actual  = {r['path_prefix']: r['rate_limit_tier'] for r in cfg['routes']}

errors = []
for path, tier in correct.items():
    got = actual.get(path)
    if got != tier:
        errors.append(f'{path}: rate_limit_tier should be {tier!r}, got {got!r}')
assert not errors, 'Wrong rate limit tiers: ' + '; '.join(errors)
print('RATE_LIMITS_OK')
\"" "wrong_rate_limits"

# ── Check 7: All services registered with correct host/port ──────────────────
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
cfg = json.load(open('gateway/config.json'))

errors = []
for svc in expected['services']:
    name = svc['name']
    reg  = cfg.get('services', {}).get(name)
    if reg is None:
        errors.append(f'{name}: not in services registry')
        continue
    if reg.get('host') != svc['host']:
        errors.append(f'{name}: host should be {svc[\"host\"]!r}, got {reg.get(\"host\")!r}')
    if reg.get('port') != svc['port']:
        errors.append(f'{name}: port should be {svc[\"port\"]}, got {reg.get(\"port\")}')
assert not errors, 'Service registry errors: ' + '; '.join(errors)
print('SERVICES_REGISTRY_OK')
\"" "services_registry_wrong"

# ── Check 8: Health check paths configured for all services ──────────────────
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
cfg = json.load(open('gateway/config.json'))

errors = []
for svc in expected['services']:
    name = svc['name']
    reg  = cfg.get('services', {}).get(name, {})
    hc   = reg.get('health_check_path')
    if hc != svc['health']:
        errors.append(f'{name}: health_check_path should be {svc[\"health\"]!r}, got {hc!r}')
assert not errors, 'Health check errors: ' + '; '.join(errors)
print('HEALTH_CHECKS_OK')
\"" "health_checks_wrong"

# ── Check 9: Rate limit tier definitions present ──────────────────────────────
check "python3 -c \"
import json
cfg = json.load(open('gateway/config.json'))
tiers = cfg.get('rate_limit_tiers', {})
for tier in ['low', 'standard', 'high', 'none']:
    assert tier in tiers, f'Rate limit tier {tier!r} missing from config'
    assert 'requests_per_minute' in tiers[tier], f'Tier {tier!r} missing requests_per_minute'
    assert 'burst' in tiers[tier], f'Tier {tier!r} missing burst'
print('RATE_TIER_DEFS_OK')
\"" "rate_tier_defs_missing"

# ── Check 10: No dangling upstreams (every upstream is a registered service) ──
check "python3 -c \"
import json
cfg = json.load(open('gateway/config.json'))
registered = set(cfg.get('services', {}).keys())
errors = []
for route in cfg.get('routes', []):
    upstream = route.get('upstream')
    if upstream not in registered:
        errors.append(f'{route[\"path_prefix\"]}: upstream {upstream!r} not in services')
assert not errors, 'Dangling upstreams: ' + '; '.join(errors)
print('NO_DANGLING_UPSTREAMS_OK')
\"" "dangling_upstreams"

# ── Check 11: pytest test suite passes ───────────────────────────────────────
check "python3 -m pytest tests/test_routes.py -q --tb=no 2>&1 | tail -1 | grep -E 'passed|no tests'" "pytest_tests_failed"

fi  # end if config loads

# ── Check 12: Attestation ─────────────────────────────────────────────────────
check "python3 -c \"
import json, sys
att_path = sys.argv[1] + '/attestation.json'
att = json.load(open(att_path))
assert att.get('verdict') == 'pass'
\" '$SUBMISSION'" "bad_attestation"

# ── Write score ───────────────────────────────────────────────────────────────
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
