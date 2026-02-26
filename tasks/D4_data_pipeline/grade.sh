#!/usr/bin/env bash
# Seed-aware grader for D4: Data Validation Pipeline
# Reads expected values from expected.json.
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

# ── Check 1: Pipeline runs without crashing ───────────────────────────────
check "python3 pipeline.py" "pipeline_crash"

VALID_OUT="data/output/valid.csv"
INVALID_OUT="data/output/invalid.csv"

# ── Check 2 & 3: Both output files exist ─────────────────────────────────
check "test -f '$VALID_OUT'" "missing_valid_output"
check "test -f '$INVALID_OUT'" "missing_invalid_output"

if [ -f "$VALID_OUT" ] && [ -f "$INVALID_OUT" ] && [ -f "$EXPECTED" ]; then

# ── Check 4: Correct row count in valid.csv ───────────────────────────────
check "python3 -c \"
import csv, json
expected = json.load(open('$EXPECTED'))
with open('$VALID_OUT') as f:
    rows = list(csv.DictReader(f))
assert len(rows) == expected['row_count'], \
    f'Expected {expected[\"row_count\"]} valid rows, got {len(rows)}'
print('ROW_COUNT_OK')
\"" "wrong_row_count"

# ── Check 5: No duplicate IDs in valid.csv ────────────────────────────────
check "python3 -c \"
import csv, json
expected = json.load(open('$EXPECTED'))
id_field = expected['id_field']
with open('$VALID_OUT') as f:
    rows = list(csv.DictReader(f))
ids = [r[id_field] for r in rows]
assert len(set(ids)) == len(ids), f'Duplicate ids in valid output'
print('NO_DUPLICATES_OK')
\"" "duplicate_ids_in_valid"

# ── Check 6: All bad-pattern IDs rejected ────────────────────────────────
check "python3 -c \"
import csv, json
expected = json.load(open('$EXPECTED'))
id_field = expected['id_field']
bad_ids = set(expected.get('bad_pattern_ids', []))
with open('$VALID_OUT') as f:
    rows = list(csv.DictReader(f))
present = {r[id_field] for r in rows}
leaked = bad_ids & present
assert not leaked, f'Bad-pattern IDs should be invalid: {leaked}'
print('PATTERN_VALIDATION_OK')
\"" "pattern_validation_fail"

# ── Check 7: All null/empty-required-field records rejected ──────────────
check "python3 -c \"
import csv, json
expected = json.load(open('$EXPECTED'))
id_field = expected['id_field']
null_ids = set(expected.get('null_ids', []))
with open('$VALID_OUT') as f:
    rows = list(csv.DictReader(f))
present = {r[id_field] for r in rows}
leaked = null_ids & present
assert not leaked, f'Null-field records should be invalid: {leaked}'
print('NULL_CHECK_OK')
\"" "null_check_fail"

# ── Check 8: All range-violation records rejected ─────────────────────────
check "python3 -c \"
import csv, json
expected = json.load(open('$EXPECTED'))
id_field = expected['id_field']
range_ids = set(expected.get('range_ids', []))
with open('$VALID_OUT') as f:
    rows = list(csv.DictReader(f))
present = {r[id_field] for r in rows}
leaked = range_ids & present
assert not leaked, f'Range-violation records should be invalid: {leaked}'
print('RANGE_VALIDATION_OK')
\"" "range_validation_fail"

# ── Check 9: Cross-field constraint violations rejected ───────────────────
check "python3 -c \"
import csv, json
expected = json.load(open('$EXPECTED'))
id_field = expected['id_field']
cross_ids = set(expected.get('cross_field_ids', []))
with open('$VALID_OUT') as f:
    rows = list(csv.DictReader(f))
present = {r[id_field] for r in rows}
leaked = cross_ids & present
assert not leaked, f'Cross-field violation records should be invalid: {leaked}'
print('CROSS_FIELD_OK')
\"" "cross_field_validation_fail"

# ── Check 10: Enum violations rejected ───────────────────────────────────
check "python3 -c \"
import csv, json
expected = json.load(open('$EXPECTED'))
id_field = expected['id_field']
enum_ids = set(expected.get('enum_ids', []))
with open('$VALID_OUT') as f:
    rows = list(csv.DictReader(f))
present = {r[id_field] for r in rows}
leaked = enum_ids & present
assert not leaked, f'Enum-violation records should be invalid: {leaked}'
print('ENUM_VALIDATION_OK')
\"" "enum_validation_fail"

# ── Check 11: Dedup winner is correct priority record ────────────────────
check "python3 -c \"
import csv, json
expected = json.load(open('$EXPECTED'))
id_field = expected['id_field']
dedup_priority = expected['dedup_priority']
winners = expected.get('dup_winner_priorities', {})
with open('$VALID_OUT') as f:
    rows = list(csv.DictReader(f))
id_map = {r[id_field]: r for r in rows}
for dup_id, winner_prio in winners.items():
    row = id_map.get(dup_id)
    assert row is not None, f'Dedup id {dup_id} missing from valid output'
    got = row.get(dedup_priority)
    assert got == winner_prio, \
        f'id={dup_id}: expected priority {dedup_priority}={winner_prio}, got {got}'
print('DEDUP_WINNER_OK')
\"" "dedup_winner_fail"

# ── Check 12: Valid records are not in invalid.csv (no false positives) ───
check "python3 -c \"
import csv, json
expected = json.load(open('$EXPECTED'))
id_field = expected['id_field']
all_invalid_ids = set(expected.get('invalid_ids', []))
with open('$VALID_OUT') as fv:
    valid_ids = {r[id_field] for r in csv.DictReader(fv)}
# None of the valid-output IDs should appear in the known-invalid set
overlap = valid_ids & all_invalid_ids
assert not overlap, f'Records that should be invalid appear in valid.csv: {overlap}'
print('NO_FALSE_POSITIVES_OK')
\"" "false_positives_in_valid"

# ── Check 13: Invalid records appear in invalid.csv ──────────────────────
check "python3 -c \"
import csv, json
expected = json.load(open('$EXPECTED'))
id_field = expected['id_field']
all_invalid_ids = set(expected.get('invalid_ids', []))
with open('$INVALID_OUT') as fi:
    invalid_present = {r[id_field] for r in csv.DictReader(fi)}
missing = all_invalid_ids - invalid_present
assert not missing, f'Some invalid records missing from invalid.csv: {missing}'
print('INVALID_CSV_COMPLETE_OK')
\"" "missing_from_invalid_csv"

# ── Check 14: invalid.csv has _errors column with content ────────────────
check "python3 -c \"
import csv
with open('$INVALID_OUT') as f:
    reader = csv.DictReader(f)
    assert '_errors' in (reader.fieldnames or []), 'invalid.csv missing _errors column'
    rows = list(reader)
    for r in rows:
        assert r.get('_errors'), f'Empty _errors for id {list(r.values())[0]}'
print('ERRORS_COLUMN_OK')
\"" "invalid_errors_column_fail"

# ── Check 15: Output sorted by id_field ascending ────────────────────────
check "python3 -c \"
import csv, json
expected = json.load(open('$EXPECTED'))
id_field = expected['id_field']
with open('$VALID_OUT') as f:
    rows = list(csv.DictReader(f))
ids = [r[id_field] for r in rows]
assert ids == sorted(ids), f'valid.csv not sorted by {id_field}'
print('SORT_ORDER_OK')
\"" "sort_order_wrong"

# ── Check 16: Column order matches schema ────────────────────────────────
check "python3 -c \"
import csv, json
expected = json.load(open('$EXPECTED'))
with open('$VALID_OUT') as f:
    reader = csv.DictReader(f)
    actual_cols = list(reader.fieldnames or [])
expected_cols = expected['columns']
assert actual_cols == expected_cols, \
    f'Wrong column order. Expected {expected_cols}, got {actual_cols}'
print('COLUMNS_OK')
\"" "wrong_columns"

fi

# ── Check 17: Attestation ─────────────────────────────────────────────────
check "python3 -c \"
import json, sys
att = json.load(open(sys.argv[1]))
assert att.get('verdict') == 'pass'
\" '$SUBMISSION/attestation.json'" "bad_attestation"

# ── Write score ───────────────────────────────────────────────────────────
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
