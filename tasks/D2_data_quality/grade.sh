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

# Run the pipeline
check "python3 clean.py" "clean_crash"

RESULT="data/output/clean.csv"
check "test -f '$RESULT'" "missing_output"

if [ -f "$RESULT" ]; then
check "python3 -c \"
import csv
with open('$RESULT', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    fieldnames = reader.fieldnames
assert fieldnames == ['id', 'name', 'score', 'department'], f'Wrong columns: {fieldnames}'
print('COLUMNS_OK')
\"" "wrong_columns"

# Expected: 6 rows after dedup+drop
check "python3 -c \"
import csv
with open('$RESULT') as f:
    rows = list(csv.DictReader(f))
assert len(rows) == 6, f'Expected 6 rows after dedup+drop, got {len(rows)}'
\"" "wrong_row_count"

# No duplicates by id
check "python3 -c \"
import csv
with open('$RESULT') as f:
    rows = list(csv.DictReader(f))
ids = [r['id'] for r in rows]
assert len(set(ids)) == len(ids), f'Duplicate ids in output: {ids}'
\"" "duplicate_ids"

# Range check: no score outside 0-100
check "python3 -c \"
import csv
with open('$RESULT') as f:
    rows = list(csv.DictReader(f))
for r in rows:
    if r['score'] != 'MISSING':
        s = int(r['score'])
        assert 0 <= s <= 100, f'Score out of range for id={r[\"id\"]}: {s}'
ids = [r['id'] for r in rows]
assert '5' not in ids, 'id=5 (score=105) should be dropped'
assert '8' not in ids, 'id=8 (score=-5) should be dropped'
\"" "range_check_fail"

# Missing values replaced with MISSING
check "python3 -c \"
import csv
with open('$RESULT') as f:
    rows = list(csv.DictReader(f))
for r in rows:
    for col in ['name', 'score', 'department']:
        assert r[col] not in ('', 'N/A'), f'Unreplaced missing value in id={r[\"id\"]}, col={col}: \"{r[col]}\"'
\"" "missing_values_not_replaced"

# Dedup: higher score kept
check "python3 -c \"
import csv
with open('$RESULT') as f:
    rows = list(csv.DictReader(f))
id_score = {r['id']: r['score'] for r in rows}
assert id_score.get('1') == '90', f'id=1 should keep score=90, got {id_score.get(\"1\")}'
assert id_score.get('2') == '92', f'id=2 should keep score=92, got {id_score.get(\"2\")}'
\"" "dedup_higher_score_fail"

# Sort: score desc, then name asc
check "python3 -c \"
import csv
with open('$RESULT') as f:
    rows = list(csv.DictReader(f))
scores = []
for r in rows:
    s = -1 if r['score'] == 'MISSING' else int(r['score'])
    scores.append((-s, r['name']))
assert scores == sorted(scores), f'Not sorted correctly (score desc, name asc)'
\"" "sort_order_wrong"

# Department correction: MISSING + score < 50 -> review_needed
check "python3 -c \"
import csv
with open('$RESULT') as f:
    rows = list(csv.DictReader(f))
for r in rows:
    if r['score'] != 'MISSING':
        s = int(r['score'])
        if s < 50 and r['department'] in ('MISSING', ''):
            assert False, f'id={r[\"id\"]}: department should be review_needed for low score'
# id=6 Frank has score=45, dept was MISSING -> should be review_needed
dept_map = {r['id']: r['department'] for r in rows}
assert dept_map.get('6') == 'review_needed', f'id=6: expected review_needed, got {dept_map.get(\"6\")}'
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
