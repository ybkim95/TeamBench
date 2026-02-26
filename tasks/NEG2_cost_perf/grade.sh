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

# 1. config.json is valid JSON
check "python3 -c \"
import json, sys
with open('config.json') as f:
    cfg = json.load(f)
assert isinstance(cfg, dict), 'config.json must be a JSON object'
print('CONFIG_VALID_JSON')
\"" "invalid_json"

# 2. config.json contains required keys
check "python3 -c \"
import json
with open('config.json') as f:
    cfg = json.load(f)
required = ['instance_type', 'instance_count', 'cache_size_mb',
            'thread_count', 'batch_size', 'connection_pool_size',
            'enable_compression', 'enable_keep_alive']
missing = [k for k in required if k not in cfg]
assert not missing, f'Missing keys: {missing}'
print('CONFIG_KEYS_OK')
\"" "missing_config_keys"

# 3. Cost within budget
check "python3 -c \"
import json, sys
sys.path.insert(0, '.')
from simulator import compute_cost, BUDGET_PER_MONTH
with open('config.json') as f:
    cfg = json.load(f)
cost = compute_cost(cfg)
assert cost <= BUDGET_PER_MONTH, f'Cost \${cost:.2f} exceeds budget \${BUDGET_PER_MONTH}'
print(f'COST_OK: \${cost:.2f}')
\"" "cost_exceeds_budget"

# 4. p50 latency meets target
check "python3 -c \"
import json, sys
sys.path.insert(0, '.')
from simulator import compute_performance, P50_TARGET_MS
with open('config.json') as f:
    cfg = json.load(f)
perf = compute_performance(cfg)
assert perf['p50_ms'] <= P50_TARGET_MS, f'p50={perf[\"p50_ms\"]}ms exceeds target {P50_TARGET_MS}ms'
print(f'P50_OK: {perf[\"p50_ms\"]}ms')
\"" "p50_target_missed"

# 5. p99 latency meets target
check "python3 -c \"
import json, sys
sys.path.insert(0, '.')
from simulator import compute_performance, P99_TARGET_MS
with open('config.json') as f:
    cfg = json.load(f)
perf = compute_performance(cfg)
assert perf['p99_ms'] <= P99_TARGET_MS, f'p99={perf[\"p99_ms\"]}ms exceeds target {P99_TARGET_MS}ms'
print(f'P99_OK: {perf[\"p99_ms\"]}ms')
\"" "p99_target_missed"

# 6. Throughput meets target
check "python3 -c \"
import json, sys
sys.path.insert(0, '.')
from simulator import compute_performance, THROUGHPUT_TARGET_RPS
with open('config.json') as f:
    cfg = json.load(f)
perf = compute_performance(cfg)
assert perf['throughput_rps'] >= THROUGHPUT_TARGET_RPS, \
    f'throughput={perf[\"throughput_rps\"]}rps below target {THROUGHPUT_TARGET_RPS}rps'
print(f'THROUGHPUT_OK: {perf[\"throughput_rps\"]}rps')
\"" "throughput_target_missed"

# 7. Reliability above threshold
check "python3 -c \"
import json, sys
sys.path.insert(0, '.')
from simulator import compute_performance, RELIABILITY_TARGET
with open('config.json') as f:
    cfg = json.load(f)
perf = compute_performance(cfg)
assert perf['reliability'] >= RELIABILITY_TARGET, \
    f'reliability={perf[\"reliability\"]} below target {RELIABILITY_TARGET}'
print(f'RELIABILITY_OK: {perf[\"reliability\"]}')
\"" "reliability_below_threshold"

# 8. Weighted score above baseline (0.40)
check "python3 -c \"
import json, sys
sys.path.insert(0, '.')
from simulator import compute_cost, compute_performance, weighted_score
with open('config.json') as f:
    cfg = json.load(f)
cost = compute_cost(cfg)
perf = compute_performance(cfg)
ws = weighted_score(cost, perf)
assert ws > 0.40, f'Weighted score {ws:.4f} not above baseline 0.40'
print(f'SCORE_OK: {ws:.4f}')
\"" "score_below_baseline"

# 9. Not over-provisioned (cost <= 95% of budget)
check "python3 -c \"
import json, sys
sys.path.insert(0, '.')
from simulator import compute_cost, BUDGET_PER_MONTH
with open('config.json') as f:
    cfg = json.load(f)
cost = compute_cost(cfg)
cap = BUDGET_PER_MONTH * 0.95
assert cost <= cap, f'Over-provisioned: cost \${cost:.2f} > 95% budget \${cap:.2f}'
print(f'EFFICIENCY_OK: \${cost:.2f}')
\"" "over_provisioned"

# 10. instance_type is valid
check "python3 -c \"
import json, sys
sys.path.insert(0, '.')
from simulator import INSTANCE_TYPES
with open('config.json') as f:
    cfg = json.load(f)
itype = cfg.get('instance_type', '')
assert itype in INSTANCE_TYPES, f'Invalid instance_type: {itype}'
print(f'INSTANCE_TYPE_OK: {itype}')
\"" "invalid_instance_type"

# 11. instance_count >= 1
check "python3 -c \"
import json
with open('config.json') as f:
    cfg = json.load(f)
count = cfg.get('instance_count', 0)
assert isinstance(count, int) and count >= 1, f'instance_count must be int >= 1, got {count}'
print(f'INSTANCE_COUNT_OK: {count}')
\"" "invalid_instance_count"

# 12. All targets pass simultaneously via simulator --check
check "python3 simulator.py --check" "simulator_check_fail"

# Partial scoring
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
