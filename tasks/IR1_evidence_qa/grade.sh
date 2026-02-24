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
check "python3 -c \"
import json, os, sys

ans = json.load(open('$ANS_PATH'))
answer = ans.get('answer', '')

# Answer must contain \\\$4.2M
assert '\\\$4.2M' in answer or '4.2M' in answer or '4,200,000' in answer or '4200000' in answer, \
    f'Wrong answer: {answer}'
print('ANSWER_OK')
\"" "wrong_answer"

check "python3 -c \"
import json
ans = json.load(open('$ANS_PATH'))
evidence = ans.get('evidence', [])
assert isinstance(evidence, list) and len(evidence) == 2, f'Need 2 evidence items, got {len(evidence)}'
print('EVIDENCE_COUNT_OK')
\"" "wrong_evidence_count"

check "python3 -c \"
import json
ans = json.load(open('$ANS_PATH'))
evidence = ans.get('evidence', [])
docs = []
for ev in evidence:
    doc = ev['doc']
    assert isinstance(doc, str) and doc.endswith('.txt')
    docs.append(doc)
assert docs[0] != docs[1], f'Evidence must be from 2 different docs: {docs}'
print('EVIDENCE_DOCS_OK')
\"" "evidence_not_from_different_docs"

check "python3 -c \"
import json, os

ans = json.load(open('$ANS_PATH'))
evidence = ans.get('evidence', [])
corpus_dir = '$WORKSPACE/corpus'
for ev in evidence:
    doc = ev['doc']
    # Normalize: strip leading corpus/ if agent included it
    if doc.startswith('corpus/'):
        doc = doc[len('corpus/'):]
    start, end = ev['lines']
    path = os.path.join(corpus_dir, doc)
    assert os.path.isfile(path), f'Doc not found: {doc}'
    with open(path) as f:
        lines = f.read().splitlines()
    assert end <= len(lines), f'Line {end} exceeds {doc} length {len(lines)}'
    blob = ' '.join(lines[start-1:end]).lower()
    assert 'titan' in blob, f'Evidence from {doc} does not mention Titan'
    has_budget_info = any(t in blob for t in ['4.2', 'budget', 'approved', 'allocated'])
    assert has_budget_info, f'Evidence from {doc} not budget-related'
print('EVIDENCE_CONTENT_OK')
\"" "invalid_evidence_content"
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
