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

# 1. search_engine.py imports
check "python3 -c 'from search_engine import SearchEngine'" "import_error"

# 2. Hyphenated words are split
check "python3 -c \"
from search_engine import tokenize
tokens = tokenize('state-of-the-art')
assert 'state' in tokens, f'Hyphens not split: {tokens}'
print('HYPHEN_OK')
\"" "hyphen_not_split"

# 3. Stopwords are removed
check "python3 -c \"
from search_engine import tokenize, STOPWORDS
tokens = tokenize('the quick brown fox')
for sw in ['the']:
    assert sw not in tokens, f'Stopword {sw} still present'
print('STOPWORD_OK')
\"" "stopwords_not_removed"

# 4. Phrase query works
check "python3 -c \"
from search_engine import SearchEngine
engine = SearchEngine()
engine.add_document(1, 'machine learning is great')
engine.add_document(2, 'learning about machines')
results = engine.search('\\\"machine learning\\\"')
ids = [r[0] for r in results]
assert 1 in ids, f'Phrase match missing doc 1: {ids}'
assert 2 not in ids, f'Phrase match should not include doc 2: {ids}'
print('PHRASE_OK')
\"" "phrase_query_broken"

# 5. BM25 k1 is not 0
check "python3 -c \"
source = open('search_engine.py').read()
assert 'k1 = 0.0' not in source and 'k1=0.0' not in source, 'k1 still 0'
print('K1_OK')
\"" "bm25_k1_zero"

# 6. Term frequency affects ranking
check "python3 -c \"
from search_engine import SearchEngine
engine = SearchEngine()
engine.add_document(1, 'python')
engine.add_document(2, 'python python python')
results = engine.search('python')
assert len(results) >= 2, f'Expected 2 results, got {len(results)}'
assert results[0][0] == 2, f'Doc with more term freq should rank first: {results}'
print('TF_RANKING_OK')
\"" "tf_not_affecting_rank"

# 7. Basic search works
check "python3 -c \"
from search_engine import SearchEngine
engine = SearchEngine()
engine.add_document(1, 'hello world')
engine.add_document(2, 'goodbye world')
results = engine.search('hello')
ids = [r[0] for r in results]
assert 1 in ids, f'Basic search failed: {ids}'
print('BASIC_OK')
\"" "basic_search_broken"

# 8. Empty query returns empty
check "python3 -c \"
from search_engine import SearchEngine
engine = SearchEngine()
engine.add_document(1, 'hello world')
results = engine.search('')
assert len(results) == 0, f'Empty query should return nothing: {results}'
print('EMPTY_OK')
\"" "empty_query_returns_results"

# 9. test_search.py passes
check "python3 -m pytest test_search.py -q 2>/dev/null || python3 -m unittest test_search 2>/dev/null" \
      "tests_fail"

# 10. Attestation
# ── Attestation recorded as METADATA, never scored ───────────────────────
# de-scored-by: scripts/repair_graders.py (R3 attestation-is-protocol)
# attestation.json is a PROTOCOL property of the run (already enforced as a
# hard gate in harness/grade_task.py), not a property of the submitted
# artifact. Scoring it let an agent buy partial credit by writing one JSON
# file, which is the confound behind the withdrawn "removing the Verifier
# improves partial score" result. Recorded here, excluded from partial_score.
echo "metadata: attestation_present=$([ -f "${SUBMISSION:-}/attestation.json" ] && echo yes || echo no)"

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
