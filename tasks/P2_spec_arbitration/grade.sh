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

CONFIG="$WORKSPACE/output/resolved_config.json"
check "test -f '$CONFIG'" "missing_resolved_config"

if [ -f "$CONFIG" ]; then
# Check each of the 8 keys
check "python3 -c \"
import json
cfg = json.load(open('$CONFIG'))
assert cfg.get('cache_ttl') == 3600, f'cache_ttl: expected 3600, got {cfg.get(\"cache_ttl\")}'
\"" "cache_ttl_wrong"

check "python3 -c \"
import json
cfg = json.load(open('$CONFIG'))
assert cfg.get('max_payload_mb') == 10, f'max_payload_mb: expected 10, got {cfg.get(\"max_payload_mb\")}'
\"" "max_payload_mb_wrong"

check "python3 -c \"
import json
cfg = json.load(open('$CONFIG'))
assert cfg.get('compression') == 'gzip', f'compression: expected gzip, got {cfg.get(\"compression\")}'
\"" "compression_wrong"

check "python3 -c \"
import json
cfg = json.load(open('$CONFIG'))
assert cfg.get('encryption') == 'aes256', f'encryption: expected aes256, got {cfg.get(\"encryption\")}'
\"" "encryption_wrong"

check "python3 -c \"
import json
cfg = json.load(open('$CONFIG'))
assert cfg.get('log_format') == 'json', f'log_format: expected json, got {cfg.get(\"log_format\")}'
\"" "log_format_wrong"

check "python3 -c \"
import json
cfg = json.load(open('$CONFIG'))
assert cfg.get('backup_enabled') is True, f'backup_enabled: expected true, got {cfg.get(\"backup_enabled\")}'
\"" "backup_enabled_wrong"

# retry_timeout: footnote exception means 60 wins (not 30)
check "python3 -c \"
import json
cfg = json.load(open('$CONFIG'))
assert cfg.get('retry_timeout') == 60, f'retry_timeout: expected 60 (footnote exception), got {cfg.get(\"retry_timeout\")}'
\"" "retry_timeout_wrong"

check "python3 -c \"
import json
cfg = json.load(open('$CONFIG'))
assert cfg.get('log_retention_days') == 30, f'log_retention_days: expected 30, got {cfg.get(\"log_retention_days\")}'
\"" "log_retention_days_wrong"

# Check exactly 8 keys
check "python3 -c \"
import json
cfg = json.load(open('$CONFIG'))
expected_keys = {'cache_ttl', 'max_payload_mb', 'compression', 'encryption', 'log_format', 'backup_enabled', 'retry_timeout', 'log_retention_days'}
assert set(cfg.keys()) == expected_keys, f'Wrong keys: {set(cfg.keys())} vs {expected_keys}'
\"" "wrong_key_count"
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
