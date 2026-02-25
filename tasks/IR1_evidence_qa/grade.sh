#!/usr/bin/env bash
# Seed-aware grader for IR1: Offline Browse — Evidence-Required QA
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

ANS_PATH="$WORKSPACE/answer.json"
check "test -f '$ANS_PATH'" "missing_answer_json"

if [ -f "$ANS_PATH" ] && [ -f "$EXPECTED" ]; then

# Answer must contain the correct budget value (from expected.json)
check "python3 -c \"
import json, os, sys

ans = json.load(open('$ANS_PATH'))
expected = json.load(open('$EXPECTED'))
answer = ans.get('answer', '')

variants = expected.get('primary_answer_variants', [expected.get('primary_answer', '')])
matched = any(v in answer for v in variants if v)
assert matched, f'Wrong answer: {answer!r}. Expected one of: {variants}'
print('ANSWER_OK')
\"" "wrong_answer"

# Exactly 2 evidence items
check "python3 -c \"
import json
ans = json.load(open('$ANS_PATH'))
evidence = ans.get('evidence', [])
assert isinstance(evidence, list) and len(evidence) == 2, f'Need 2 evidence items, got {len(evidence)}'
print('EVIDENCE_COUNT_OK')
\"" "wrong_evidence_count"

# Evidence from 2 different docs
check "python3 -c \"
import json
ans = json.load(open('$ANS_PATH'))
evidence = ans.get('evidence', [])
docs = []
for ev in evidence:
    doc = ev['doc']
    assert isinstance(doc, str) and doc.endswith('.txt'), f'Invalid doc: {doc}'
    docs.append(doc)
assert docs[0] != docs[1], f'Evidence must be from 2 different docs: {docs}'
print('EVIDENCE_DOCS_OK')
\"" "evidence_not_from_different_docs"

# Evidence content must mention the target project and be budget-related
check "python3 -c \"
import json, os

ans = json.load(open('$ANS_PATH'))
expected = json.load(open('$EXPECTED'))
evidence = ans.get('evidence', [])
corpus_dir = '$WORKSPACE/corpus'
target = expected.get('target_project', '').lower()
final_budget = expected.get('final_budget', '')
# Extract numeric part (e.g. '8.8' from '\$8.8M')
import re
budget_num = re.sub(r'[^\d.]', '', final_budget)

for ev in evidence:
    doc = ev['doc']
    if doc.startswith('corpus/'):
        doc = doc[len('corpus/'):]
    start, end = ev['lines']
    path = os.path.join(corpus_dir, doc)
    assert os.path.isfile(path), f'Doc not found: {doc}'
    with open(path) as f:
        lines = f.read().splitlines()
    assert end <= len(lines), f'Line {end} exceeds {doc} length {len(lines)}'
    blob = ' '.join(lines[start-1:end]).lower()
    assert target in blob, f'Evidence from {doc} does not mention target project ({target})'
    has_budget_info = any(t in blob for t in [budget_num, 'budget', 'approved', 'allocated', 'revised'])
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
