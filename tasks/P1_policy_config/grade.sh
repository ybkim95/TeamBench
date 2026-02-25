#!/usr/bin/env bash
# Seed-aware grader for P1: Policy-Driven Config Change
# Reads expected values from expected.json instead of hardcoded assertions.
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

CONFIG="$WORKSPACE/output/config.json"
check "test -f '$CONFIG'" "missing_config_json"

if [ -f "$CONFIG" ] && [ -f "$EXPECTED" ]; then

# Exactly the required keys, no extras
check "python3 -c \"
import json
cfg = json.load(open('$CONFIG'))
expected = json.load(open('$EXPECTED'))
required = set(expected['required_keys'])
assert set(cfg.keys()) == required, f'Wrong keys: {set(cfg.keys())} (expected {required})'
print('KEYS_OK')
\"" "wrong_keys"

# Validate every rule from expected.json policy_rules
check "python3 -c \"
import json
cfg = json.load(open('$CONFIG'))
expected = json.load(open('$EXPECTED'))
rules = expected['policy_rules']
for key, spec in rules.items():
    val = cfg.get(key)
    t = spec['type']
    if t == 'int_range':
        assert isinstance(val, int) and spec['min'] <= val <= spec['max'], \
            f'{key}={val} not in [{spec[\"min\"]}, {spec[\"max\"]}]'
    elif t == 'exact_int':
        assert val == spec['value'], f'{key}={val} must be exactly {spec[\"value\"]}'
    elif t == 'exact_bool':
        assert val is spec['value'], f'{key}={val} must be exactly {spec[\"value\"]}'
    elif t == 'enum':
        assert val in spec['allowed'], f'{key}={val!r} not in allowed {spec[\"allowed\"]}'
    elif t == 'exact_list':
        assert val == spec['value'], f'{key}={val} must be exactly {spec[\"value\"]}'
    elif t == 'exact_string':
        assert val == spec['value'], f'{key}={val!r} must be exactly {spec[\"value\"]!r}'
print('ALL_RULES_OK')
\"" "policy_rules_fail"

# Individual rule checks (mirrors policy_rules but one check per rule for granular feedback)
check "python3 -c \"
import json
cfg = json.load(open('$CONFIG'))
expected = json.load(open('$EXPECTED'))
spec = expected['policy_rules']['max_connections']
v = cfg['max_connections']
assert isinstance(v, int) and spec['min'] <= v <= spec['max'], f'max_connections={v}'
print('RULE_MAX_CONNECTIONS_OK')
\"" "rule_max_connections"

check "python3 -c \"
import json
cfg = json.load(open('$CONFIG'))
expected = json.load(open('$EXPECTED'))
assert cfg['timeout_sec'] == expected['policy_rules']['timeout_sec']['value'], \
    f'timeout_sec={cfg[\"timeout_sec\"]}'
print('RULE_TIMEOUT_OK')
\"" "rule_timeout_sec"

check "python3 -c \"
import json
cfg = json.load(open('$CONFIG'))
assert cfg['ssl_enabled'] is True, f'ssl_enabled={cfg[\"ssl_enabled\"]}'
print('RULE_SSL_OK')
\"" "rule_ssl_enabled"

check "python3 -c \"
import json
cfg = json.load(open('$CONFIG'))
expected = json.load(open('$EXPECTED'))
allowed = expected['policy_rules']['log_level']['allowed']
assert cfg['log_level'] in allowed, f'log_level={cfg[\"log_level\"]!r} not in {allowed}'
print('RULE_LOG_LEVEL_OK')
\"" "rule_log_level"

check "python3 -c \"
import json
cfg = json.load(open('$CONFIG'))
expected = json.load(open('$EXPECTED'))
assert cfg['retry_count'] == expected['policy_rules']['retry_count']['value'], \
    f'retry_count={cfg[\"retry_count\"]}'
print('RULE_RETRY_OK')
\"" "rule_retry_count"

check "python3 -c \"
import json
cfg = json.load(open('$CONFIG'))
expected = json.load(open('$EXPECTED'))
assert cfg['cors_origins'] == expected['policy_rules']['cors_origins']['value'], \
    f'cors_origins={cfg[\"cors_origins\"]}'
print('RULE_CORS_OK')
\"" "rule_cors_origins"

check "python3 -c \"
import json
cfg = json.load(open('$CONFIG'))
expected = json.load(open('$EXPECTED'))
spec = expected['policy_rules']['rate_limit_rpm']
v = cfg['rate_limit_rpm']
assert isinstance(v, int) and spec['min'] <= v <= spec['max'], f'rate_limit_rpm={v}'
print('RULE_RATE_LIMIT_OK')
\"" "rule_rate_limit_rpm"

check "python3 -c \"
import json
cfg = json.load(open('$CONFIG'))
expected = json.load(open('$EXPECTED'))
allowed = expected['policy_rules']['auth_method']['allowed']
assert cfg['auth_method'] in allowed, f'auth_method={cfg[\"auth_method\"]!r} not in {allowed}'
print('RULE_AUTH_OK')
\"" "rule_auth_method"

check "python3 -c \"
import json
cfg = json.load(open('$CONFIG'))
expected = json.load(open('$EXPECTED'))
assert cfg['session_timeout_min'] == expected['policy_rules']['session_timeout_min']['value'], \
    f'session_timeout_min={cfg[\"session_timeout_min\"]}'
print('RULE_SESSION_TIMEOUT_OK')
\"" "rule_session_timeout_min"

check "python3 -c \"
import json
cfg = json.load(open('$CONFIG'))
expected = json.load(open('$EXPECTED'))
assert cfg['min_password_length'] == expected['policy_rules']['min_password_length']['value'], \
    f'min_password_length={cfg[\"min_password_length\"]}'
print('RULE_PASSWORD_LENGTH_OK')
\"" "rule_min_password_length"

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
