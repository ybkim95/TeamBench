#!/usr/bin/env bash
# Seed-aware grader for D2: Data Quality + Spec Compliance
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

cd "$WORKSPACE"

# Run the pipeline
check "python3 clean.py" "clean_crash"

RESULT="data/output/clean.csv"
check "test -f '$RESULT'" "missing_output"

if [ -f "$RESULT" ] && [ -f "$EXPECTED" ]; then

# Check columns match expected
check "python3 -c \"
import csv, json
expected = json.load(open('$EXPECTED'))
with open('$RESULT', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    fieldnames = reader.fieldnames
assert list(fieldnames) == expected['columns'], f'Wrong columns: {list(fieldnames)} (expected {expected[\"columns\"]})'
print('COLUMNS_OK')
\"" "wrong_columns"

# Check row count (from expected.json)
check "python3 -c \"
import csv, json
expected = json.load(open('$EXPECTED'))
with open('$RESULT') as f:
    rows = list(csv.DictReader(f))
assert len(rows) == expected['row_count'], f'Expected {expected[\"row_count\"]} rows after dedup+drop, got {len(rows)}'
print('ROW_COUNT_OK')
\"" "wrong_row_count"

# No duplicates by id
check "python3 -c \"
import csv
with open('$RESULT') as f:
    rows = list(csv.DictReader(f))
ids = [r['id'] for r in rows]
assert len(set(ids)) == len(ids), f'Duplicate ids in output: {ids}'
print('NO_DUPLICATES_OK')
\"" "duplicate_ids"

# Range check: no score outside 0-100, out-of-range ids must be absent
check "python3 -c \"
import csv, json
expected = json.load(open('$EXPECTED'))
score_col = expected['score_col']
with open('$RESULT') as f:
    rows = list(csv.DictReader(f))
ids_present = {r['id'] for r in rows}
for oor_id in expected['out_of_range_ids']:
    assert oor_id not in ids_present, f'Out-of-range id={oor_id} should be dropped'
for r in rows:
    s_str = r[score_col]
    if s_str not in ('MISSING', '', 'N/A'):
        s = int(s_str)
        assert 0 <= s <= 100, f'Score out of range for id={r[\"id\"]}: {s}'
print('RANGE_CHECK_OK')
\"" "range_check_fail"

# Missing values replaced with MISSING (not empty or N/A)
check "python3 -c \"
import csv, json
expected = json.load(open('$EXPECTED'))
score_col = expected['score_col']
dept_col = expected['dept_col']
fill = expected['correct_fill']
with open('$RESULT') as f:
    rows = list(csv.DictReader(f))
for r in rows:
    for col in ['name', score_col, dept_col]:
        assert r.get(col) not in ('', 'N/A'), f'Unreplaced missing value in id={r[\"id\"]}, col={col}: \"{r.get(col)}\"'
print('MISSING_VALUES_OK')
\"" "missing_values_not_replaced"

# Dedup: higher score kept
check "python3 -c \"
import csv, json
expected = json.load(open('$EXPECTED'))
score_col = expected['score_col']
with open('$RESULT') as f:
    rows = list(csv.DictReader(f))
id_score = {r['id']: r[score_col] for r in rows}
for did, winner_score in expected['dup_winner_scores'].items():
    got = id_score.get(did)
    assert got == winner_score, f'id={did} should keep score={winner_score}, got {got}'
print('DEDUP_HIGHER_SCORE_OK')
\"" "dedup_higher_score_fail"

# Sort: score desc, then name asc
check "python3 -c \"
import csv, json
expected = json.load(open('$EXPECTED'))
score_col = expected['score_col']
with open('$RESULT') as f:
    rows = list(csv.DictReader(f))
sort_keys = []
for r in rows:
    s_str = r[score_col]
    s = -1 if s_str in ('MISSING', '') else int(s_str)
    sort_keys.append((-s, r['name']))
assert sort_keys == sorted(sort_keys), f'Not sorted correctly (score desc, name asc)'
print('SORT_ORDER_OK')
\"" "sort_order_wrong"

# Department correction: MISSING dept + score < 50 -> review_needed
check "python3 -c \"
import csv, json
expected = json.load(open('$EXPECTED'))
score_col = expected['score_col']
dept_col = expected['dept_col']
review_id = expected.get('review_needed_id')
with open('$RESULT') as f:
    rows = list(csv.DictReader(f))
dept_map = {r['id']: r[dept_col] for r in rows}
score_map = {r['id']: r[score_col] for r in rows}
if review_id:
    assert dept_map.get(review_id) == 'review_needed', \
        f'id={review_id}: expected review_needed, got {dept_map.get(review_id)}'
# Also check no row has MISSING dept with score < 50
for r in rows:
    s_str = r[score_col]
    if s_str not in ('MISSING', ''):
        s = int(s_str)
        if s < 50 and r[dept_col] in ('MISSING', ''):
            assert False, f'id={r[\"id\"]}: department should be review_needed for low score'
print('DEPT_CORRECTION_OK')
\"" "department_correction_fail"

fi

# Attestation
check "python3 -c \"
import json, sys
att = json.load(open(sys.argv[1]))
assert att.get('verdict') == 'pass'
\" '$SUBMISSION/attestation.json'" "bad_attestation"

# Write score
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
