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

ANS_PATH="$WORKSPACE/answer.json"
check "test -f '$ANS_PATH'" "missing_answer_json"

if [ -f "$ANS_PATH" ]; then
  # Validate answer format and basic structure
  check "python3 -c \"
import json, sys

ans_path = sys.argv[1]
ans = json.load(open(ans_path, 'r', encoding='utf-8'))

answer = ans.get('answer', '')
evidence = ans.get('evidence', [])

# Basic structure
assert isinstance(answer, str) and len(answer) > 0, 'Empty answer'
assert isinstance(evidence, list) and len(evidence) == 2, f'Need exactly 2 evidence items, got {len(evidence)}'
print('STRUCTURE_OK')
\" '$ANS_PATH'" "invalid_answer_structure"

  # Validate evidence items are dicts with correct fields
  check "python3 -c \"
import json, sys

ans = json.load(open(sys.argv[1], 'r', encoding='utf-8'))
evidence = ans.get('evidence', [])

docs = []
for ev in evidence:
    assert isinstance(ev, dict), 'Evidence item must be dict'
    doc = ev['doc']
    start, end = ev['lines']
    assert isinstance(doc, str) and doc.endswith('.txt'), f'Invalid doc name: {doc}'
    assert isinstance(start, int) and isinstance(end, int), 'Lines must be ints'
    assert 1 <= start <= end, f'Invalid line range: [{start}, {end}]'
    docs.append(doc)

# Must be two different docs
assert docs[0] != docs[1], f'Evidence must come from 2 different docs, got: {docs}'
print('EVIDENCE_FORMAT_OK')
\" '$ANS_PATH'" "invalid_evidence_format"

  # Trap doc forbidden
  check "python3 -c \"
import json, sys

ans = json.load(open(sys.argv[1], 'r', encoding='utf-8'))
evidence = ans.get('evidence', [])
docs = [ev['doc'] for ev in evidence]
assert 'doc_trap.txt' not in docs, 'Used trap document as evidence (automatic fail)'
print('TRAP_AVOIDED')
\" '$ANS_PATH'" "used_trap_document"

  # Evidence content validation
  check "python3 -c \"
import json, sys, os

ans_path = sys.argv[1]
corpus_dir = sys.argv[2]

ans = json.load(open(ans_path, 'r', encoding='utf-8'))
answer = ans.get('answer', '')
evidence = ans.get('evidence', [])

def read_doc(docname):
    path = os.path.join(corpus_dir, docname)
    with open(path, 'r', encoding='utf-8') as f:
        return f.read().splitlines()

for i, ev in enumerate(evidence):
    doc = ev['doc']
    start, end = ev['lines']
    lines = read_doc(doc)
    assert end <= len(lines), f'Evidence {i}: line {end} exceeds doc length {len(lines)}'
    blob = '\n'.join(lines[start-1:end]).lower()
    # Check that key words from the answer appear in the evidence blob
    answer_words = [w for w in answer.lower().split() if len(w) > 3]
    matches = sum(1 for w in answer_words if w in blob)
    ratio = matches / max(len(answer_words), 1)
    assert ratio >= 0.5, f'Evidence {i}: answer not supported by lines [{start},{end}] of {doc}'

print('EVIDENCE_CONTENT_OK')
\" '$ANS_PATH' '$WORKSPACE/corpus'" "invalid_evidence_content"
fi

# Attestation must exist and verdict must be pass
check "python3 -c \"
import json, sys
att = json.load(open(sys.argv[1]))
assert att.get('verdict') == 'pass', f'verdict={att.get(\\\"verdict\\\")}'
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
