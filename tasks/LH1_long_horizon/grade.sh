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

cd "$WORKSPACE"

check "python3 workflow.py" "workflow_crash"

RESULT="output/final_result.json"
LOG="output/workflow_log.jsonl"

check "test -f '$RESULT'" "missing_result"
check "test -f '$LOG'" "missing_log"

if [ -f "$RESULT" ] && [ -f "$LOG" ]; then
check "python3 -c \"
import json
result = json.load(open('$RESULT'))
assert result['steps_completed'] == 15, f'Only {result[\"steps_completed\"]} steps completed'
\"" "incomplete_steps"

check "python3 -c \"
import json
result = json.load(open('$RESULT'))
assert result['recovered_failures'] == 2, f'Recovered {result[\"recovered_failures\"]} (expected 2)'
\"" "wrong_recovery_count"

check "python3 -c \"
import json, hashlib
outputs = []
for i in range(1, 16):
    with open(f'intermediates/step{i}_output.txt') as f:
        outputs.append(f.read())
expected = hashlib.sha256(''.join(outputs).encode()).hexdigest()
result = json.load(open('$RESULT'))
assert result['checksum'] == expected, 'Checksum mismatch'
\"" "checksum_mismatch"

check "python3 -c \"
import json
with open('$LOG') as f:
    entries = [json.loads(l) for l in f if l.strip()]
assert len(entries) <= 19, f'Too many executions: {len(entries)}'
\"" "budget_exceeded"

check "python3 -c \"
import os
for i in [5, 11]:
    marker = f'intermediates/step{i}_fail'
    assert not os.path.exists(marker), f'Failure marker still exists: {marker}'
\"" "failure_markers_remain"
fi

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
