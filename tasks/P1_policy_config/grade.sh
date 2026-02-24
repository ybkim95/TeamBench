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

CONFIG="$WORKSPACE/output/config.json"
check "test -f '$CONFIG'" "missing_config_json"

if [ -f "$CONFIG" ]; then
  # Exactly 8 keys, no extras
  check "python3 -c \"
import json
cfg = json.load(open('$CONFIG'))
allowed = {'max_connections','timeout_sec','ssl_enabled','log_level','retry_count','cors_origins','rate_limit_rpm','auth_method'}
assert set(cfg.keys()) == allowed, f'Wrong keys: {set(cfg.keys())} (expected {allowed})'
print('KEYS_OK')
\"" "wrong_keys"

  # Rule 1: max_connections
  check "python3 -c \"
import json
cfg = json.load(open('$CONFIG'))
assert isinstance(cfg['max_connections'], int) and 100 <= cfg['max_connections'] <= 500, f'max_connections={cfg[\"max_connections\"]}'
print('RULE1_OK')
\"" "rule1_max_connections"

  # Rule 2: timeout_sec
  check "python3 -c \"
import json
cfg = json.load(open('$CONFIG'))
assert cfg['timeout_sec'] == 30, f'timeout_sec={cfg[\"timeout_sec\"]}'
print('RULE2_OK')
\"" "rule2_timeout_sec"

  # Rule 3: ssl_enabled
  check "python3 -c \"
import json
cfg = json.load(open('$CONFIG'))
assert cfg['ssl_enabled'] is True, f'ssl_enabled={cfg[\"ssl_enabled\"]}'
print('RULE3_OK')
\"" "rule3_ssl_enabled"

  # Rule 4: log_level
  check "python3 -c \"
import json
cfg = json.load(open('$CONFIG'))
assert cfg['log_level'] in ('warn', 'error'), f'log_level={cfg[\"log_level\"]}'
print('RULE4_OK')
\"" "rule4_log_level"

  # Rule 5: retry_count
  check "python3 -c \"
import json
cfg = json.load(open('$CONFIG'))
assert cfg['retry_count'] == 3, f'retry_count={cfg[\"retry_count\"]}'
print('RULE5_OK')
\"" "rule5_retry_count"

  # Rule 6: cors_origins
  check "python3 -c \"
import json
cfg = json.load(open('$CONFIG'))
assert cfg['cors_origins'] == [], f'cors_origins={cfg[\"cors_origins\"]}'
print('RULE6_OK')
\"" "rule6_cors_origins"

  # Rule 7: rate_limit_rpm
  check "python3 -c \"
import json
cfg = json.load(open('$CONFIG'))
assert isinstance(cfg['rate_limit_rpm'], int) and 60 <= cfg['rate_limit_rpm'] <= 120, f'rate_limit_rpm={cfg[\"rate_limit_rpm\"]}'
print('RULE7_OK')
\"" "rule7_rate_limit_rpm"

  # Rule 8: auth_method
  check "python3 -c \"
import json
cfg = json.load(open('$CONFIG'))
assert cfg['auth_method'] == 'jwt', f'auth_method={cfg[\"auth_method\"]}'
print('RULE8_OK')
\"" "rule8_auth_method"
fi

# Attestation
check "python3 -c \"
import json, sys
att = json.load(open(sys.argv[1]))
assert att.get('verdict') == 'pass'
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
