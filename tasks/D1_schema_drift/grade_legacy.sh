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

# Run the ETL pipeline
check "python3 etl.py" "etl_crash"

RESULT="data/output/result.csv"
check "test -f '$RESULT'" "missing_output"

if [ -f "$RESULT" ]; then
# Check columns
check "python3 -c \"
import csv
with open('$RESULT', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    fieldnames = reader.fieldnames
assert fieldnames == ['id', 'name', 'value', 'category'], f'Wrong columns: {fieldnames}'
print('COLUMNS_OK')
\"" "wrong_columns"

# Check row count (23 unique ids after dedup)
check "python3 -c \"
import csv
with open('$RESULT') as f:
    rows = list(csv.DictReader(f))
assert len(rows) == 23, f'Expected 23 rows, got {len(rows)}'
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

# Check full_name -> name mapping (batch_003 rows should have names)
check "python3 -c \"
import csv
with open('$RESULT') as f:
    rows = list(csv.DictReader(f))
name_map = {r['id']: r['name'] for r in rows}
assert name_map.get('11') == 'Karl', f'full_name not mapped for id=11: got {name_map.get(\"11\")}'
assert name_map.get('12') == 'Liam', f'full_name not mapped for id=12: got {name_map.get(\"12\")}'
print('FULLNAME_MAPPING_OK')
\"" "fullname_mapping_fail"

# Check record_id -> id mapping (batch_004)
check "python3 -c \"
import csv
with open('$RESULT') as f:
    rows = list(csv.DictReader(f))
ids = [r['id'] for r in rows]
assert '16' in ids, 'record_id=16 not mapped to id'
assert '17' in ids, 'record_id=17 not mapped to id'
assert '18' in ids, 'record_id=18 not mapped to id'
assert '19' in ids, 'record_id=19 not mapped to id'
print('RECORDID_MAPPING_OK')
\"" "recordid_mapping_fail"

# Check amount -> value mapping (batch_004)
check "python3 -c \"
import csv
with open('$RESULT') as f:
    rows = list(csv.DictReader(f))
val_map = {r['id']: r['value'] for r in rows}
assert val_map.get('16') == '550', f'amount not mapped for id=16: got {val_map.get(\"16\")}'
assert val_map.get('17') == '430', f'amount not mapped for id=17: got {val_map.get(\"17\")}'
print('AMOUNT_MAPPING_OK')
\"" "amount_mapping_fail"

# Check missing category filled with "unknown"
check "python3 -c \"
import csv
with open('$RESULT') as f:
    rows = list(csv.DictReader(f))
for r in rows:
    assert r['category'].strip() != '', f'Empty category for id={r[\"id\"]}'
cat_map = {r['id']: r['category'] for r in rows}
for i in ['1', '2', '4', '5']:
    assert cat_map.get(i) == 'unknown', f'Missing category not filled for id={i}: got {cat_map.get(i)}'
print('MISSING_CATEGORY_OK')
\"" "missing_category_fill_fail"

# Check dedup: higher value kept for id=3
check "python3 -c \"
import csv
with open('$RESULT') as f:
    rows = list(csv.DictReader(f))
val_map = {r['id']: r['value'] for r in rows}
assert val_map.get('3') == '350', f'id=3 should keep value=350 (highest), got {val_map.get(\"3\")}'
print('DEDUP_HIGHER_OK')
\"" "dedup_higher_value_fail"

# Check non-numeric value replaced with 0
check "python3 -c \"
import csv
with open('$RESULT') as f:
    rows = list(csv.DictReader(f))
val_map = {r['id']: r['value'] for r in rows}
assert val_map.get('21') == '0', f'Non-numeric value for id=21 should be 0, got {val_map.get(\"21\")}'
print('NONNUMERIC_OK')
\"" "nonnumeric_value_not_replaced"

# Check negative value replaced with 0
check "python3 -c \"
import csv
with open('$RESULT') as f:
    rows = list(csv.DictReader(f))
val_map = {r['id']: r['value'] for r in rows}
assert val_map.get('22') == '0', f'Negative value for id=22 should be 0, got {val_map.get(\"22\")}'
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

# Check extra columns dropped (no 'region' or '_timestamp' in output)
check "python3 -c \"
import csv
with open('$RESULT') as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
assert 'region' not in fieldnames, 'Extra column region not dropped'
assert '_timestamp' not in fieldnames, 'Extra column _timestamp not dropped'
assert len(fieldnames) == 4, f'Expected 4 columns, got {len(fieldnames)}'
print('EXTRA_COLUMNS_OK')
\"" "extra_columns_not_dropped"

# Specific values check for batch_004 dedup of id=3
check "python3 -c \"
import csv
with open('$RESULT') as f:
    rows = list(csv.DictReader(f))
cat_map = {r['id']: r['category'] for r in rows}
assert cat_map.get('3') == 'sales', f'id=3 category should be sales (from highest value row), got {cat_map.get(\"3\")}'
print('DEDUP_CATEGORY_OK')
\"" "dedup_category_wrong"
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
