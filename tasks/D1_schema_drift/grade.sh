#!/usr/bin/env bash
# Seed-aware grader for D1: Schema Drift ETL Repair
# Reads expected values from expected.json instead of hardcoded assertions.
# This is the reference implementation for the seed-aware grading pattern.
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

# Run the ETL pipeline
check "python3 etl.py" "etl_crash"

RESULT="data/output/result.csv"
check "test -f '$RESULT'" "missing_output"

if [ -f "$RESULT" ] && [ -f "$EXPECTED" ]; then
# Check columns (from expected.json)
check "python3 -c \"
import csv, json
expected = json.load(open('$EXPECTED'))
with open('$RESULT', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    fieldnames = reader.fieldnames
assert fieldnames == expected['columns'], f'Wrong columns: {fieldnames}'
print('COLUMNS_OK')
\"" "wrong_columns"

# Check row count (from expected.json)
check "python3 -c \"
import csv, json
expected = json.load(open('$EXPECTED'))
with open('$RESULT') as f:
    rows = list(csv.DictReader(f))
assert len(rows) == expected['row_count'], f'Expected {expected[\"row_count\"]} rows, got {len(rows)}'
print('ROW_COUNT_OK')
\"" "wrong_row_count"

# Check no duplicates by id
check "python3 -c \"
import csv
with open('$RESULT') as f:
    rows = list(csv.DictReader(f))
ids = [r['id'] for r in rows]
assert len(set(ids)) == len(ids), f'Duplicate ids found'
print('NO_DUPLICATES_OK')
\"" "duplicate_ids"

# Check renamed column mapping (batch_003: e.g., full_name -> name)
check "python3 -c \"
import csv, json
expected = json.load(open('$EXPECTED'))
with open('$RESULT') as f:
    rows = list(csv.DictReader(f))
name_map = {r['id']: r['name'] for r in rows}
for rid, expected_name in expected['batch3_check'].items():
    assert name_map.get(rid) == expected_name, f'Name not mapped for id={rid}: got {name_map.get(rid)}'
print('NAME_MAPPING_OK')
\"" "name_mapping_fail"

# Check id/value rename mapping (batch_004)
check "python3 -c \"
import csv, json
expected = json.load(open('$EXPECTED'))
with open('$RESULT') as f:
    rows = list(csv.DictReader(f))
ids = [r['id'] for r in rows]
for rid in expected['batch4_check_ids']:
    assert rid in ids, f'Renamed id={rid} not found'
print('ID_MAPPING_OK')
\"" "id_mapping_fail"

check "python3 -c \"
import csv, json
expected = json.load(open('$EXPECTED'))
with open('$RESULT') as f:
    rows = list(csv.DictReader(f))
val_map = {r['id']: r['value'] for r in rows}
for rid, expected_val in expected['batch4_check_values'].items():
    assert val_map.get(rid) == expected_val, f'Value not mapped for id={rid}: got {val_map.get(rid)}'
print('VALUE_MAPPING_OK')
\"" "value_mapping_fail"

# Check missing category filled with "unknown"
check "python3 -c \"
import csv, json
expected = json.load(open('$EXPECTED'))
with open('$RESULT') as f:
    rows = list(csv.DictReader(f))
cat_map = {r['id']: r['category'] for r in rows}
for rid in expected['batch1_missing_category_ids']:
    assert cat_map.get(rid) == 'unknown', f'Missing category not filled for id={rid}: got {cat_map.get(rid)}'
print('MISSING_CATEGORY_OK')
\"" "missing_category_fill_fail"

# Check dedup: higher value kept
check "python3 -c \"
import csv, json
expected = json.load(open('$EXPECTED'))
with open('$RESULT') as f:
    rows = list(csv.DictReader(f))
val_map = {r['id']: r['value'] for r in rows}
dedup_id = expected['dedup_id']
assert val_map.get(dedup_id) == expected['dedup_value'], f'id={dedup_id} should keep value={expected[\"dedup_value\"]}, got {val_map.get(dedup_id)}'
print('DEDUP_HIGHER_OK')
\"" "dedup_higher_value_fail"

# Check dedup category matches
check "python3 -c \"
import csv, json
expected = json.load(open('$EXPECTED'))
with open('$RESULT') as f:
    rows = list(csv.DictReader(f))
cat_map = {r['id']: r['category'] for r in rows}
dedup_id = expected['dedup_id']
assert cat_map.get(dedup_id) == expected['dedup_category'], f'id={dedup_id} category should be {expected[\"dedup_category\"]}, got {cat_map.get(dedup_id)}'
print('DEDUP_CATEGORY_OK')
\"" "dedup_category_wrong"

# Check non-numeric value replaced with 0
check "python3 -c \"
import csv, json
expected = json.load(open('$EXPECTED'))
with open('$RESULT') as f:
    rows = list(csv.DictReader(f))
val_map = {r['id']: r['value'] for r in rows}
nid = expected['nonnumeric_id']
assert val_map.get(nid) == expected['nonnumeric_expected_value'], f'Non-numeric value for id={nid} should be {expected[\"nonnumeric_expected_value\"]}, got {val_map.get(nid)}'
print('NONNUMERIC_OK')
\"" "nonnumeric_value_not_replaced"

# Check negative value replaced with 0
check "python3 -c \"
import csv, json
expected = json.load(open('$EXPECTED'))
with open('$RESULT') as f:
    rows = list(csv.DictReader(f))
val_map = {r['id']: r['value'] for r in rows}
nid = expected['negative_id']
assert val_map.get(nid) == expected['negative_expected_value'], f'Negative value for id={nid} should be 0, got {val_map.get(nid)}'
print('NEGATIVE_OK')
\"" "negative_value_not_replaced"

# Check sort order: category ascending, then id ascending
check "python3 -c \"
import csv
with open('$RESULT') as f:
    rows = list(csv.DictReader(f))
sort_keys = [(r['category'], int(r['id'])) for r in rows]
assert sort_keys == sorted(sort_keys), f'Not sorted by category asc, id asc'
print('SORT_ORDER_OK')
\"" "sort_order_wrong"

# Check extra columns dropped
check "python3 -c \"
import csv, json
expected = json.load(open('$EXPECTED'))
with open('$RESULT') as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
for extra in expected['extra_columns']:
    assert extra not in fieldnames, f'Extra column {extra} not dropped'
assert len(fieldnames) == 4, f'Expected 4 columns, got {len(fieldnames)}'
print('EXTRA_COLUMNS_OK')
\"" "extra_columns_not_dropped"
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
