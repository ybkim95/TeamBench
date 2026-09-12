#!/usr/bin/env bash
# Seed-aware grader for PIPE3: Message Queue Consumer Fix
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
      "$(dirname "$0")/../../..python3" \
      "python3"; do
    if "$candidate" -c "import json" >/dev/null 2>&1; then
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

# ── Write helper Python scripts to temp files (avoids bash quoting issues) ────

cat > /tmp/_pipe3_check6.py << 'PYEOF'
import json, sys
expected = json.load(open(sys.argv[1]))
wrong_map = expected['wrong_field_map']
consumer_src = open('consumer.py').read()

errors = []
for correct, wrong in wrong_map.items():
    dq = '.get("' + wrong + '")'
    sq = ".get('" + wrong + "')"
    dq2 = '["' + wrong + '"]'
    sq2 = "['" + wrong + "']"
    if dq in consumer_src or sq in consumer_src or dq2 in consumer_src or sq2 in consumer_src:
        errors.append('still uses wrong field ' + repr(wrong) + ' instead of ' + repr(correct))

if errors:
    print('FAIL: ' + '; '.join(errors), file=sys.stderr)
    sys.exit(1)
print('CORRECT_FIELD_NAMES_OK')
PYEOF

cat > /tmp/_pipe3_check7.py << 'PYEOF'
import json, sys
expected = json.load(open(sys.argv[1]))
correct_fields = list(expected['correct_field_map'].keys())
consumer_src = open('consumer.py').read()
present = [f for f in correct_fields if f in consumer_src]
ratio = len(present) / max(1, len(correct_fields))
if ratio < 0.5:
    missing = [f for f in correct_fields if f not in consumer_src]
    print('FAIL: only ' + str(len(present)) + '/' + str(len(correct_fields)) + ' correct field names found; missing: ' + str(missing), file=sys.stderr)
    sys.exit(1)
print('CORRECT_FIELDS_PRESENT_OK')
PYEOF

cat > /tmp/_pipe3_check10.py << 'PYEOF'
import json, re, sys
expected = json.load(open(sys.argv[1]))
id_field = expected['envelope']['id_field']
consumer_src = open('consumer.py').read()
has_id_field = id_field in consumer_src
has_dedup_structure = bool(re.search(r'(set\(\)|seen|processed|dedup|_ids)', consumer_src))
if not (has_id_field or has_dedup_structure):
    print('FAIL: consumer.py must implement deduplication using ' + repr(id_field) + ' or a seen-IDs set', file=sys.stderr)
    sys.exit(1)
print('DEDUP_LOGIC_OK')
PYEOF

cat > /tmp/_pipe3_check11.py << 'PYEOF'
import json, sys
expected = json.load(open(sys.argv[1]))
wrapper_key = expected['envelope']['wrapper_key']
payload_fields = expected['payload_fields']
producer_src = open('producer.py').read()
if wrapper_key not in producer_src:
    print('FAIL: producer.py must use envelope wrapper_key=' + repr(wrapper_key), file=sys.stderr)
    sys.exit(1)
present = [f for f in payload_fields if f in producer_src]
if len(present) < 1:
    print('FAIL: producer.py must reference at least one payload field; found none of ' + str(payload_fields), file=sys.stderr)
    sys.exit(1)
print('PRODUCER_FORMAT_OK')
PYEOF

cat > /tmp/_pipe3_attestation.py << 'PYEOF'
import json, sys
att_path = sys.argv[1] + '/attestation.json'
att = json.load(open(att_path))
assert att.get('verdict') == 'pass', 'attestation verdict is not pass'
print('ATTESTATION_OK')
PYEOF

# ── Check 1: No syntax errors in queue.py ─────────────────────────────────────
check "$PYTHON -m py_compile queue.py && echo QUEUE_SYNTAX_OK" "queue_syntax_error"

# ── Check 2: No syntax errors in producer.py ──────────────────────────────────
check "$PYTHON -m py_compile producer.py && echo PRODUCER_SYNTAX_OK" "producer_syntax_error"

# ── Check 3: No syntax errors in consumer.py ──────────────────────────────────
check "$PYTHON -m py_compile consumer.py && echo CONSUMER_SYNTAX_OK" "consumer_syntax_error"

# ── Check 4: consumer.py imports cleanly ──────────────────────────────────────
check "$PYTHON -c \"
import sys
sys.path.insert(0, '.')
import consumer
print('CONSUMER_IMPORTS_OK')
\"" "consumer_import_error"

# ── Check 5: queue.py has enqueue/dequeue capability (put and get) ────────────
check "$PYTHON -c \"
import sys
sys.path.insert(0, '.')
from queue import MessageQueue
q = MessageQueue('test')
tag = q.put({'msg': 'hello'})
assert tag is not None, 'put() must return a delivery_tag'
dt, body = q.get()
assert dt is not None, 'get() must return a delivery_tag'
assert body == {'msg': 'hello'}, 'get() must return message body'
print('QUEUE_ENQUEUE_DEQUEUE_OK')
\"" "queue_enqueue_dequeue_broken"

# ── Check 6: Wrong field names are NOT used in consumer.py ────────────────────
check "$PYTHON /tmp/_pipe3_check6.py $EXPECTED" "wrong_field_names_not_fixed"

# ── Check 7: Correct field names are present in consumer.py ───────────────────
check "$PYTHON /tmp/_pipe3_check7.py $EXPECTED" "correct_fields_missing_from_consumer"

# ── Check 8: Envelope unwrapping correct (wrapper_key used) ───────────────────
check "$PYTHON -c \"
import json
expected = json.load(open('$EXPECTED'))
wrapper_key = expected['envelope']['wrapper_key']
consumer_src = open('consumer.py').read()
assert wrapper_key in consumer_src, 'consumer.py must unwrap envelope using wrapper_key=' + repr(wrapper_key)
print('ENVELOPE_UNWRAP_OK')
\"" "envelope_unwrapping_wrong"

# ── Check 9: Ack mechanism present in consumer.py ─────────────────────────────
check "$PYTHON -c \"
import re
consumer_src = open('consumer.py').read()
assert re.search(r'\.ack\s*\(', consumer_src), 'consumer.py must call queue.ack(delivery_tag)'
print('ACK_MECHANISM_OK')
\"" "ack_mechanism_missing"

# ── Check 10: Deduplication logic present ─────────────────────────────────────
check "$PYTHON /tmp/_pipe3_check10.py $EXPECTED" "dedup_logic_missing"

# ── Check 11: producer.py sends correctly-formatted messages ──────────────────
check "$PYTHON /tmp/_pipe3_check11.py $EXPECTED" "producer_format_wrong"

# ── Check 12: pytest test suite passes ────────────────────────────────────────
check "$PYTHON -m pytest tests/test_consumer.py -q --tb=no 2>&1 | tail -3 | grep -E '(passed|no tests ran)'" "pytest_tests_failed"

# ── Check 13: Attestation ─────────────────────────────────────────────────────
check "$PYTHON /tmp/_pipe3_attestation.py $SUBMISSION" "bad_attestation"

# ── Write score ────────────────────────────────────────────────────────────────
PARTIAL=$("$PYTHON" -c "print(round($PASSED/max(1,$CHECKS), 2))")
if [ "$PASSED" -eq "$CHECKS" ]; then
    SUCCESS=1; PASS=true
else
    SUCCESS=0; PASS=false
fi
FM=$("$PYTHON" -c "import json; print(json.dumps([x for x in '${FAILURES}'.split(',') if x]))")

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

# hermetic-by: scripts/make_graders_hermetic.py
