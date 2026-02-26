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

ANS_PATH="$WORKSPACE/answer.json"
EXPECTED_JSON="$REPORTS/expected.json"
CORPUS_DIR="$WORKSPACE/corpus"

# ── Check 1: answer.json exists ───────────────────────────────────────────────
check "test -f '$ANS_PATH'" "missing_answer_json"

# ── Check 2: answer.json is valid JSON ───────────────────────────────────────
check "python3 -c \"
import json, sys
json.load(open('$ANS_PATH', 'r', encoding='utf-8'))
print('VALID_JSON')
\"" "invalid_json"

# ── Check 3: answer.json has required structure ───────────────────────────────
check "python3 -c \"
import json, sys
ans = json.load(open('$ANS_PATH', 'r', encoding='utf-8'))
questions = ans.get('questions', [])
assert isinstance(questions, list) and len(questions) >= 1, \
    f'Need at least 1 question, got {len(questions)}'
for q in questions:
    assert isinstance(q, dict), 'Each question entry must be a dict'
    assert 'id' in q, 'Missing id field'
    assert 'answer' in q, 'Missing answer field'
    assert isinstance(q['answer'], str), 'Answer must be a string'
print('STRUCTURE_OK')
\"" "invalid_structure"

# ── Check 4: No blank answers ─────────────────────────────────────────────────
check "python3 -c \"
import json
ans = json.load(open('$ANS_PATH', 'r', encoding='utf-8'))
questions = ans.get('questions', [])
blank = [q['id'] for q in questions if not q.get('answer', '').strip()]
assert len(blank) == 0, f'Blank answers for: {blank}'
print('NO_BLANK_ANSWERS')
\"" "blank_answers"

# ── Check 5: All question IDs present ────────────────────────────────────────
if [ -f "$EXPECTED_JSON" ]; then
check "python3 -c \"
import json
ans = json.load(open('$ANS_PATH', 'r', encoding='utf-8'))
exp = json.load(open('$EXPECTED_JSON', 'r', encoding='utf-8'))
expected_ids = {q['id'] for q in exp.get('questions', [])}
provided_ids = {q['id'] for q in ans.get('questions', [])}
missing = expected_ids - provided_ids
assert len(missing) == 0, f'Missing answers for question IDs: {missing}'
print('ALL_IDS_PRESENT')
\"" "missing_question_ids"
fi

# ── Check 6: Outdated doc is not the sole source for financial answer ─────────
if [ -f "$EXPECTED_JSON" ]; then
check "python3 -c \"
import json
ans = json.load(open('$ANS_PATH', 'r', encoding='utf-8'))
exp = json.load(open('$EXPECTED_JSON', 'r', encoding='utf-8'))

outdated_doc = exp.get('outdated_doc', 'doc_E.txt')
outdated_budget = str(exp.get('outdated_budget', ''))
true_budget = str(exp.get('true_budget', ''))

# Find Q1 (financial budget question) answer
q1_answer = ''
for q in ans.get('questions', []):
    if q['id'] == 'Q1':
        q1_answer = q.get('answer', '').strip()
        break

# The answer should match true_budget, not outdated_budget
if q1_answer and outdated_budget:
    # Reject if answer contains ONLY the outdated figure
    assert outdated_budget not in q1_answer or true_budget in q1_answer, \
        f'Q1 answer uses outdated budget {outdated_budget!r} instead of {true_budget!r}'
print('OUTDATED_DOC_NOT_USED_FOR_BUDGET')
\"" "used_outdated_budget"
fi

# ── Check 7: Financial question answer matches expected ───────────────────────
if [ -f "$EXPECTED_JSON" ]; then
check "python3 -c \"
import json
ans = json.load(open('$ANS_PATH', 'r', encoding='utf-8'))
exp = json.load(open('$EXPECTED_JSON', 'r', encoding='utf-8'))

exp_questions = {q['id']: q for q in exp.get('questions', [])}
ans_questions = {q['id']: q for q in ans.get('questions', [])}

q = exp_questions.get('Q1')
if q:
    expected_answer = q['answer']
    variants = q.get('answer_variants', [expected_answer])
    provided = ans_questions.get('Q1', {}).get('answer', '').strip()
    match = any(v.lower() in provided.lower() or provided.lower() in v.lower()
                for v in variants)
    assert match, f'Q1: got {provided!r}, expected one of {variants}'
print('FINANCIAL_ANSWER_CORRECT')
\"" "wrong_financial_answer"
fi

# ── Check 8: Technical question answer matches expected ───────────────────────
if [ -f "$EXPECTED_JSON" ]; then
check "python3 -c \"
import json
ans = json.load(open('$ANS_PATH', 'r', encoding='utf-8'))
exp = json.load(open('$EXPECTED_JSON', 'r', encoding='utf-8'))

exp_questions = {q['id']: q for q in exp.get('questions', [])}
ans_questions = {q['id']: q for q in ans.get('questions', [])}

# Check all technical questions present in the submitted answer
tech_qs = [q for q in exp.get('questions', []) if q.get('topic') == 'technical']
correct = 0
for q in tech_qs:
    qid = q['id']
    variants = q.get('answer_variants', [q['answer']])
    provided = ans_questions.get(qid, {}).get('answer', '').strip()
    if any(v.lower() in provided.lower() or provided.lower() in v.lower() for v in variants):
        correct += 1
total = len(tech_qs)
assert total == 0 or correct >= max(1, total // 2), \
    f'Too few technical answers correct: {correct}/{total}'
print(f'TECHNICAL_ANSWERS_OK:{correct}/{total}')
\"" "wrong_technical_answers"
fi

# ── Check 9: Personnel question answer matches expected ───────────────────────
if [ -f "$EXPECTED_JSON" ]; then
check "python3 -c \"
import json
ans = json.load(open('$ANS_PATH', 'r', encoding='utf-8'))
exp = json.load(open('$EXPECTED_JSON', 'r', encoding='utf-8'))

exp_questions = {q['id']: q for q in exp.get('questions', [])}
ans_questions = {q['id']: q for q in ans.get('questions', [])}

personnel_qs = [q for q in exp.get('questions', []) if q.get('topic') == 'personnel']
correct = 0
for q in personnel_qs:
    qid = q['id']
    variants = q.get('answer_variants', [q['answer']])
    provided = ans_questions.get(qid, {}).get('answer', '').strip()
    if any(v.lower() in provided.lower() or provided.lower() in v.lower() for v in variants):
        correct += 1
total = len(personnel_qs)
assert total == 0 or correct >= max(1, total // 2), \
    f'Too few personnel answers correct: {correct}/{total}'
print(f'PERSONNEL_ANSWERS_OK:{correct}/{total}')
\"" "wrong_personnel_answers"
fi

# ── Check 10: Timeline question answer matches expected ───────────────────────
if [ -f "$EXPECTED_JSON" ]; then
check "python3 -c \"
import json
ans = json.load(open('$ANS_PATH', 'r', encoding='utf-8'))
exp = json.load(open('$EXPECTED_JSON', 'r', encoding='utf-8'))

exp_questions = {q['id']: q for q in exp.get('questions', [])}
ans_questions = {q['id']: q for q in ans.get('questions', [])}

timeline_qs = [q for q in exp.get('questions', []) if q.get('topic') == 'timeline']
correct = 0
for q in timeline_qs:
    qid = q['id']
    variants = q.get('answer_variants', [q['answer']])
    provided = ans_questions.get(qid, {}).get('answer', '').strip()
    if any(v.lower() in provided.lower() or provided.lower() in v.lower() for v in variants):
        correct += 1
total = len(timeline_qs)
assert total == 0 or correct >= max(1, total // 2), \
    f'Too few timeline answers correct: {correct}/{total}'
print(f'TIMELINE_ANSWERS_OK:{correct}/{total}')
\"" "wrong_timeline_answers"
fi

# ── Check 11: Overall majority of answers correct (partial scoring) ───────────
if [ -f "$EXPECTED_JSON" ]; then
check "python3 -c \"
import json
ans = json.load(open('$ANS_PATH', 'r', encoding='utf-8'))
exp = json.load(open('$EXPECTED_JSON', 'r', encoding='utf-8'))

exp_questions = {q['id']: q for q in exp.get('questions', [])}
ans_questions = {q['id']: q for q in ans.get('questions', [])}

correct = 0
total = len(exp_questions)
for qid, q in exp_questions.items():
    variants = q.get('answer_variants', [q['answer']])
    provided = ans_questions.get(qid, {}).get('answer', '').strip()
    if any(v.lower() in provided.lower() or provided.lower() in v.lower() for v in variants):
        correct += 1

ratio = correct / max(1, total)
assert ratio >= 0.5, f'Only {correct}/{total} answers correct ({ratio:.0%}); need at least 50%'
print(f'MAJORITY_CORRECT:{correct}/{total}')
\"" "insufficient_correct_answers"
fi

# ── Check 12: Corpus files accessible ────────────────────────────────────────
check "python3 -c \"
import os
corpus_dir = '$CORPUS_DIR'
assert os.path.isdir(corpus_dir), f'Corpus directory missing: {corpus_dir}'
docs = [f for f in os.listdir(corpus_dir) if f.endswith('.txt')]
assert len(docs) >= 5, f'Expected at least 5 corpus docs, found {len(docs)}: {docs}'
# doc_A through doc_E must always be present
required = ['doc_A.txt', 'doc_B.txt', 'doc_C.txt', 'doc_D.txt', 'doc_E.txt']
for r in required:
    assert r in docs, f'Required corpus doc missing: {r}'
print(f'CORPUS_OK:{len(docs)}_docs')
\"" "corpus_files_missing"

# ── Compute per-question partial score ────────────────────────────────────────
PER_QUESTION_SCORE="0.0"
if [ -f "$EXPECTED_JSON" ] && [ -f "$ANS_PATH" ]; then
  PER_QUESTION_SCORE=$(python3 -c "
import json
ans = json.load(open('$ANS_PATH', 'r', encoding='utf-8'))
exp = json.load(open('$EXPECTED_JSON', 'r', encoding='utf-8'))
exp_questions = {q['id']: q for q in exp.get('questions', [])}
ans_questions = {q['id']: q for q in ans.get('questions', [])}
correct = 0
total = len(exp_questions)
for qid, q in exp_questions.items():
    variants = q.get('answer_variants', [q['answer']])
    provided = ans_questions.get(qid, {}).get('answer', '').strip()
    if any(v.lower() in provided.lower() or provided.lower() in v.lower() for v in variants):
        correct += 1
print(round(correct / max(1, total), 2))
" 2>/dev/null || echo "0.0")
fi

# ── Attestation check ─────────────────────────────────────────────────────────
check "python3 -c \"
import json, sys
att = json.load(open(sys.argv[1]))
assert att.get('verdict') == 'pass', f'verdict={att.get(\\\"verdict\\\")}'
\" '$SUBMISSION/attestation.json'" "bad_attestation"

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
    "partial_score": $PARTIAL,
    "per_question_score": $PER_QUESTION_SCORE
  },
  "failure_modes": $FM
}
JSON
