#!/usr/bin/env bash
# Grader for D8: CSV Data Cleanup
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

# 1. clean.py runs without error
check "python3 clean.py" "clean_crash"

# 2. Output file exists
check "test -f data/clean.csv" "missing_output"

if [ -f data/clean.csv ] && [ -f "$EXPECTED" ]; then

# 3. No duplicate IDs
check "python3 -c \"
import csv
with open('data/clean.csv') as f:
    rows = list(csv.DictReader(f))
ids = [r['id'] for r in rows]
assert len(set(ids)) == len(ids), f'Duplicate IDs found: {len(ids)} rows, {len(set(ids))} unique'
\"" "duplicate_ids"

# 4. Correct row count
check "python3 -c \"
import csv, json
expected = json.load(open('$EXPECTED'))
with open('data/clean.csv') as f:
    rows = list(csv.DictReader(f))
assert len(rows) == expected['row_count'], f'Expected {expected[\"row_count\"]} rows, got {len(rows)}'
\"" "wrong_row_count"

# 5. No empty columns (dropped column gone)
check "python3 -c \"
import csv, json
expected = json.load(open('$EXPECTED'))
with open('data/clean.csv') as f:
    reader = csv.DictReader(f)
    cols = reader.fieldnames
for dropped in expected['dropped_columns']:
    assert dropped not in cols, f'Empty column {dropped} not dropped'
\"" "empty_column_kept"

# 6. Dates normalized to YYYY-MM-DD
check "python3 -c \"
import csv, json, re
expected = json.load(open('$EXPECTED'))
with open('data/clean.csv') as f:
    rows = list(csv.DictReader(f))
date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
for row in rows:
    assert date_pattern.match(row['date']), f'Bad date format: {row[\"date\"]} in id={row[\"id\"]}'
# Spot check specific dates
for rid, exp_date in expected['date_checks'].items():
    actual = next((r['date'] for r in rows if r['id'] == rid), None)
    assert actual == exp_date, f'id={rid}: date={actual}, expected={exp_date}'
\"" "date_format_wrong"

# 7. No trailing whitespace
check "python3 -c \"
import csv
with open('data/clean.csv') as f:
    rows = list(csv.DictReader(f))
for row in rows:
    for k, v in row.items():
        assert v == v.strip(), f'Whitespace in id={row[\"id\"]}, field={k}: \"{v}\"'
\"" "whitespace_remaining"

# 8. Sorted by id ascending
check "python3 -c \"
import csv
with open('data/clean.csv') as f:
    rows = list(csv.DictReader(f))
ids = [int(r['id']) for r in rows]
assert ids == sorted(ids), f'Not sorted by id ascending'
\"" "sort_wrong"

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
