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
import json
ans = json.load(open('$ANS_PATH', 'r', encoding='utf-8'))
questions = ans.get('questions', [])
assert isinstance(questions, list) and len(questions) >= 1, \
    f'Need at least 1 question entry, got {len(questions)}'
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

# ── Check 5: All expected question IDs are present ────────────────────────────
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

# ── Check 6: Draft docs not used over approved docs (status rule) ─────────────
if [ -f "$EXPECTED_JSON" ]; then
check "python3 -c \"
import json
ans = json.load(open('$ANS_PATH', 'r', encoding='utf-8'))
exp = json.load(open('$EXPECTED_JSON', 'r', encoding='utf-8'))

ans_map = {q['id']: q.get('answer', '').strip() for q in ans.get('questions', [])}

# For each approved-over-draft question, check the answer uses the approved value
violations = []
for q in exp.get('questions', []):
    if q.get('rule_tested') != 'approved_over_draft':
        continue
    qid = q['id']
    variants = q.get('answer_variants', [q['answer']])
    provided = ans_map.get(qid, '')
    # The answer must contain at least one approved-doc variant
    match = any(v.lower() in provided.lower() or provided.lower() in v.lower()
                for v in variants)
    if not match:
        violations.append(qid)
assert len(violations) == 0, f'Draft-over-approved violations in: {violations}'
print(f'DRAFT_NOT_USED_OVER_APPROVED')
\"" "draft_used_over_approved"
fi

# ── Check 7: Founding document rule respected ─────────────────────────────────
if [ -f "$EXPECTED_JSON" ]; then
check "python3 -c \"
import json
ans = json.load(open('$ANS_PATH', 'r', encoding='utf-8'))
exp = json.load(open('$EXPECTED_JSON', 'r', encoding='utf-8'))

ans_map = {q['id']: q.get('answer', '').strip() for q in ans.get('questions', [])}

founding_qs = [q for q in exp.get('questions', [])
               if q.get('rule_tested') == 'founding_doc_always_authoritative']
correct = 0
for q in founding_qs:
    qid = q['id']
    variants = q.get('answer_variants', [q['answer']])
    provided = ans_map.get(qid, '')
    if any(v.lower() in provided.lower() or provided.lower() in v.lower() for v in variants):
        correct += 1
total = len(founding_qs)
assert total == 0 or correct >= max(1, total // 2), \
    f'Too few founding-doc questions correct: {correct}/{total}'
print(f'FOUNDING_DOC_RULE_OK:{correct}/{total}')
\"" "founding_doc_rule_violated"
fi

# ── Check 8: Temporal (most-recent approved) rule respected ───────────────────
if [ -f "$EXPECTED_JSON" ]; then
check "python3 -c \"
import json
ans = json.load(open('$ANS_PATH', 'r', encoding='utf-8'))
exp = json.load(open('$EXPECTED_JSON', 'r', encoding='utf-8'))

ans_map = {q['id']: q.get('answer', '').strip() for q in ans.get('questions', [])}

temporal_qs = [q for q in exp.get('questions', [])
               if q.get('rule_tested') == 'temporal_most_recent']
correct = 0
for q in temporal_qs:
    qid = q['id']
    variants = q.get('answer_variants', [q['answer']])
    provided = ans_map.get(qid, '')
    if any(v.lower() in provided.lower() or provided.lower() in v.lower() for v in variants):
        correct += 1
total = len(temporal_qs)
assert total == 0 or correct >= max(1, total // 2), \
    f'Too few temporal questions correct: {correct}/{total}'
print(f'TEMPORAL_RULE_OK:{correct}/{total}')
\"" "temporal_rule_violated"
fi

# ── Check 9: Correct values used for founding-topic questions ─────────────────
if [ -f "$EXPECTED_JSON" ]; then
check "python3 -c \"
import json
ans = json.load(open('$ANS_PATH', 'r', encoding='utf-8'))
exp = json.load(open('$EXPECTED_JSON', 'r', encoding='utf-8'))

ans_map = {q['id']: q.get('answer', '').strip() for q in ans.get('questions', [])}
founding_topic = exp.get('founding_topic', '')

# Find questions whose topic matches the founding topic
topic_qs = [q for q in exp.get('questions', []) if q.get('topic') == founding_topic]
correct = 0
for q in topic_qs:
    qid = q['id']
    variants = q.get('answer_variants', [q['answer']])
    provided = ans_map.get(qid, '')
    if any(v.lower() in provided.lower() or provided.lower() in v.lower() for v in variants):
        correct += 1
total = len(topic_qs)
assert total == 0 or correct >= max(1, total // 2), \
    f'Too few founding-topic answers correct: {correct}/{total}'
print(f'FOUNDING_TOPIC_ANSWERS_OK:{correct}/{total}')
\"" "founding_topic_answers_wrong"
fi

# ── Check 10: Conflict topic answers use approved (not draft) values ──────────
if [ -f "$EXPECTED_JSON" ]; then
check "python3 -c \"
import json
ans = json.load(open('$ANS_PATH', 'r', encoding='utf-8'))
exp = json.load(open('$EXPECTED_JSON', 'r', encoding='utf-8'))

ans_map = {q['id']: q.get('answer', '').strip() for q in ans.get('questions', [])}
conflict_topics = exp.get('conflict_topics', [])
doc_configs = exp.get('doc_configs', [])

# For each conflict topic, find the draft value and ensure it's NOT the sole answer
violations = []
for topic in conflict_topics:
    draft_docs = [d for d in doc_configs if d['topic'] == topic and d['status'] == 'draft']
    approved_docs = [d for d in doc_configs if d['topic'] == topic and d['status'] == 'approved']
    if not draft_docs or not approved_docs:
        continue
    draft_value = draft_docs[0]['value'].lower()
    approved_value = approved_docs[0]['value'].lower()
    if draft_value == approved_value:
        continue
    # Find questions about this conflict topic with a value answer (not meta questions)
    topic_qs = [q for q in exp.get('questions', [])
                if q.get('topic') == topic and q.get('rule_tested') == 'approved_over_draft']
    for q in topic_qs:
        provided = ans_map.get(q['id'], '').lower()
        # If provided answer contains ONLY the draft value (not the approved value), fail
        if draft_value in provided and approved_value not in provided:
            violations.append(q['id'])
assert len(violations) == 0, f'Draft value used instead of approved in: {violations}'
print(f'CONFLICT_TOPIC_APPROVED_VALUES_USED')
\"" "conflict_topic_uses_draft_value"
fi

# ── Check 11: Overall majority of answers correct (partial scoring) ───────────
if [ -f "$EXPECTED_JSON" ]; then
check "python3 -c \"
import json
ans = json.load(open('$ANS_PATH', 'r', encoding='utf-8'))
exp = json.load(open('$EXPECTED_JSON', 'r', encoding='utf-8'))

ans_map = {q['id']: q.get('answer', '').strip() for q in ans.get('questions', [])}
correct = 0
total = len(exp.get('questions', []))
for q in exp.get('questions', []):
    variants = q.get('answer_variants', [q['answer']])
    provided = ans_map.get(q['id'], '')
    if any(v.lower() in provided.lower() or provided.lower() in v.lower() for v in variants):
        correct += 1
ratio = correct / max(1, total)
assert ratio >= 0.5, f'Only {correct}/{total} correct ({ratio:.0%}); need >= 50%'
print(f'MAJORITY_CORRECT:{correct}/{total}')
\"" "insufficient_correct_answers"
fi

# ── Check 12: Corpus files accessible and minimum count met ──────────────────
check "python3 -c \"
import os
corpus_dir = '$CORPUS_DIR'
assert os.path.isdir(corpus_dir), f'Corpus directory missing: {corpus_dir}'
docs = [f for f in os.listdir(corpus_dir) if f.endswith('.txt')]
assert len(docs) >= 4, f'Expected at least 4 corpus docs, found {len(docs)}: {docs}'
required = ['doc_A.txt', 'doc_B.txt', 'doc_C.txt', 'doc_D.txt']
for r in required:
    assert r in docs, f'Required corpus doc missing: {r}'
print(f'CORPUS_OK:{len(docs)}_docs')
\"" "corpus_files_missing"

# ── Check 13: Each corpus doc has date and status headers ─────────────────────
check "python3 -c \"
import os, re
corpus_dir = '$CORPUS_DIR'
docs = [f for f in os.listdir(corpus_dir) if f.endswith('.txt')]
for doc in docs:
    path = os.path.join(corpus_dir, doc)
    content = open(path, 'r', encoding='utf-8').read()
    assert 'Date:' in content, f'{doc} missing Date: header'
    assert 'Status:' in content, f'{doc} missing Status: header'
print(f'DOC_HEADERS_OK:{len(docs)}_docs')
\"" "corpus_docs_missing_headers"

# ── Check 14: Meta rule questions answered correctly ──────────────────────────
if [ -f "$EXPECTED_JSON" ]; then
check "python3 -c \"
import json
ans = json.load(open('$ANS_PATH', 'r', encoding='utf-8'))
exp = json.load(open('$EXPECTED_JSON', 'r', encoding='utf-8'))

ans_map = {q['id']: q.get('answer', '').strip() for q in ans.get('questions', [])}
meta_qs = [q for q in exp.get('questions', []) if q.get('topic') == 'meta']
correct = 0
for q in meta_qs:
    qid = q['id']
    variants = q.get('answer_variants', [q['answer']])
    provided = ans_map.get(qid, '')
    if any(v.lower() in provided.lower() or provided.lower() in v.lower() for v in variants):
        correct += 1
total = len(meta_qs)
# Meta questions test rule understanding — partial credit: need at least half
assert total == 0 or correct >= max(1, (total + 1) // 2), \
    f'Too few meta-rule questions correct: {correct}/{total}'
print(f'META_RULE_QUESTIONS_OK:{correct}/{total}')
\"" "meta_rule_questions_wrong"
fi

# ── Compute per-question partial score ────────────────────────────────────────
PER_QUESTION_SCORE="0.0"
if [ -f "$EXPECTED_JSON" ] && [ -f "$ANS_PATH" ]; then
  PER_QUESTION_SCORE=$(python3 -c "
import json
ans = json.load(open('$ANS_PATH', 'r', encoding='utf-8'))
exp = json.load(open('$EXPECTED_JSON', 'r', encoding='utf-8'))
ans_map = {q['id']: q.get('answer', '').strip() for q in ans.get('questions', [])}
correct = 0
total = len(exp.get('questions', []))
for q in exp.get('questions', []):
    variants = q.get('answer_variants', [q['answer']])
    provided = ans_map.get(q['id'], '')
    if any(v.lower() in provided.lower() or provided.lower() in v.lower() for v in variants):
        correct += 1
print(round(correct / max(1, total), 2))
" 2>/dev/null || echo "0.0")
fi

# ── Attestation check ─────────────────────────────────────────────────────────
# ── Attestation recorded as METADATA, never scored ───────────────────────
# de-scored-by: scripts/repair_graders.py (R3 attestation-is-protocol)
# attestation.json is a PROTOCOL property of the run (already enforced as a
# hard gate in harness/grade_task.py), not a property of the submitted
# artifact. Scoring it let an agent buy partial credit by writing one JSON
# file, which is the confound behind the withdrawn "removing the Verifier
# improves partial score" result. Recorded here, excluded from partial_score.
echo "metadata: attestation_present=$([ -f "${SUBMISSION:-}/attestation.json" ] && echo yes || echo no)"

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
