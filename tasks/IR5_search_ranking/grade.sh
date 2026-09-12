#!/usr/bin/env bash
# Grader for IR5: Search Ranking Fix
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

cd "$WORKSPACE"
source /usr/local/lib/venv/bin/activate 2>/dev/null || true

# 1. search.py exists
check "test -f search.py" "missing_search"

# 2. Corpus files exist
check "test -d corpus && ls corpus/*.txt >/dev/null 2>&1" "missing_corpus"

# 3. search.py runs without error
check "python3 search.py --query 'test' >/dev/null 2>&1" "search_crash"

if [ -f "$EXPECTED" ]; then

# 4. IDF formula corrected (smoothed IDF)
check "python3 -c \"
with open('search.py') as f:
    content = f.read()
# Should have N+1 and df+1 in the IDF formula (smoothed)
assert '+ 1' in content or '+1' in content, 'No smoothing in IDF formula'
\"" "idf_not_smoothed"

# 5. Length normalization present
check "python3 -c \"
with open('search.py') as f:
    content = f.read()
assert 'len(' in content or 'length' in content.lower() or 'norm' in content.lower(), 'No length normalization'
\"" "no_length_norm"

# 6-8. Ranking correctness for test queries
check "python3 -c \"
import json, subprocess, sys
expected = json.load(open('$EXPECTED'))
for qtest in expected['query_tests']:
    query = qtest['query']
    result = subprocess.run([sys.executable, 'search.py', '--query', query],
        capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, f'Query failed: {query}'
    output = json.loads(result.stdout)
    result_ids = [r['doc_id'] for r in output[:3]]
    expected_top = qtest['expected_top3']
    assert result_ids == expected_top, f'Query \"{query}\": got {result_ids}, expected {expected_top}'
\"" "ranking_wrong_q1"

check "python3 -c \"
import json, subprocess, sys
expected = json.load(open('$EXPECTED'))
# Check tie-breaking: same-score docs ordered by doc_id ascending
qtest = expected['tiebreak_test']
query = qtest['query']
result = subprocess.run([sys.executable, 'search.py', '--query', query],
    capture_output=True, text=True, timeout=30)
output = json.loads(result.stdout)
# Find adjacent pairs with same score and verify id ordering
for i in range(len(output) - 1):
    if round(output[i]['score'], 4) == round(output[i+1]['score'], 4):
        assert output[i]['doc_id'] < output[i+1]['doc_id'], f'Tie-break wrong: {output[i][\"doc_id\"]} should come before {output[i+1][\"doc_id\"]}'
\"" "tiebreak_wrong"

check "python3 -c \"
import json, subprocess, sys
expected = json.load(open('$EXPECTED'))
# Verify scores are rounded to 4 decimal places
query = expected['query_tests'][0]['query']
result = subprocess.run([sys.executable, 'search.py', '--query', query],
    capture_output=True, text=True, timeout=30)
output = json.loads(result.stdout)
for r in output:
    score_str = str(r['score'])
    if '.' in score_str:
        decimals = len(score_str.split('.')[1])
        assert decimals <= 4, f'Score {r[\"score\"]} has {decimals} decimal places, max 4'
\"" "score_precision_wrong"

fi

# Attestation
# ── Attestation recorded as METADATA, never scored ───────────────────────
# de-scored-by: scripts/repair_graders.py (R3 attestation-is-protocol)
# attestation.json is a PROTOCOL property of the run (already enforced as a
# hard gate in harness/grade_task.py), not a property of the submitted
# artifact. Scoring it let an agent buy partial credit by writing one JSON
# file, which is the confound behind the withdrawn "removing the Verifier
# improves partial score" result. Recorded here, excluded from partial_score.
echo "metadata: attestation_present=$([ -f "${SUBMISSION:-}/attestation.json" ] && echo yes || echo no)"

PARTIAL=$(python3 -c "print(round($PASSED/max(1,$CHECKS), 2))")
if [ "$PASSED" -eq "$CHECKS" ]; then
    PASS=true
else
    PASS=false
fi
FM=$(python3 -c "import json; print(json.dumps([x for x in '${FAILURES}'.split(',') if x]))")

cat > "$REPORTS/score.json" <<JSON
{
  "pass": $PASS,
  "primary": {"success": $([ "$PASS" = "true" ] && echo 1 || echo 0)},
  "secondary": {
    "checks_passed": $PASSED,
    "checks_total": $CHECKS,
    "partial_score": $PARTIAL
  },
  "failure_modes": $FM
}
JSON
