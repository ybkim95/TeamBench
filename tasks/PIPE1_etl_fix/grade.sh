#!/usr/bin/env bash
# Seed-aware grader for PIPE1: ETL Schema Mapping Fix
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

# ── Check 1: etl.py is syntactically valid Python ────────────────────────────
check "python3 -m py_compile etl.py" "etl_syntax_error"

# ── Check 2: run_etl.py completes without error ──────────────────────────────
check "python3 run_etl.py" "run_etl_crash"

# ── Check 3: output.json exists and is valid JSON ────────────────────────────
check "python3 -c \"
import json
with open('output.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
assert isinstance(data, list), 'output.json must be a JSON array'
print('OUTPUT_JSON_VALID')
\"" "output_json_invalid"

# Remaining checks only run when output.json and expected.json are present
if [ -f "output.json" ] && [ -f "$EXPECTED" ]; then

# ── Check 4: All records transformed (count matches source) ──────────────────
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
output = json.load(open('output.json'))
assert len(output) == expected['record_count'], \
    f'Expected {expected[\"record_count\"]} records, got {len(output)}'
print('RECORD_COUNT_OK')
\"" "wrong_record_count"

# ── Check 5: Field names match target schema ──────────────────────────────────
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
output = json.load(open('output.json'))
target_fields = set(expected['target_fields'])
for i, rec in enumerate(output):
    rec_fields = set(rec.keys())
    missing = target_fields - rec_fields
    extra = rec_fields - target_fields
    assert not missing, f'Record {i} missing fields: {missing}'
    assert not extra, f'Record {i} has extra fields: {extra}'
print('FIELD_NAMES_OK')
\"" "wrong_field_names"

# ── Check 6: Field renames correctly applied (spot-check first 3 records) ────
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
output = json.load(open('output.json'))
field_map = expected['field_map']
exp_records = expected['records']
# Verify first 3 records match expected values on renamed key fields
target_fields = expected['target_fields']
check_fields = target_fields[:4]  # first 4 target fields (IDs / key fields)
for i, (got, exp) in enumerate(zip(output[:3], exp_records[:3])):
    for f in check_fields:
        assert str(got.get(f)) == str(exp.get(f)), \
            f'Record {i} field {f}: got {got.get(f)!r}, expected {exp.get(f)!r}'
print('FIELD_RENAMES_OK')
\"" "field_renames_wrong"

# ── Check 7: Type conversions correct (dates, amounts) ───────────────────────
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
output = json.load(open('output.json'))
exp_records = expected['records']
domain = expected['domain']

# Domain-specific type conversion spot checks
if domain == 'ecommerce':
    for i, (got, exp) in enumerate(zip(output, exp_records)):
        # unit_price must be float
        assert isinstance(got.get('unit_price'), (int, float)), \
            f'Record {i}: unit_price must be numeric, got {type(got.get(\"unit_price\"))}'
        # order_date must be YYYY-MM-DD (10 chars)
        d = str(got.get('order_date', ''))
        assert len(d) == 10 and d[4] == '-' and d[7] == '-', \
            f'Record {i}: order_date format wrong: {d!r}'
        # discount_pct must be int 0-100
        dp = got.get('discount_pct')
        assert isinstance(dp, int) and 0 <= dp <= 100, \
            f'Record {i}: discount_pct must be int 0-100, got {dp!r}'
elif domain == 'healthcare':
    import re
    for i, (got, exp) in enumerate(zip(output, exp_records)):
        # dob must be MM/DD/YYYY
        dob = str(got.get('dob', ''))
        assert re.match(r'^\d{2}/\d{2}/\d{4}$', dob), \
            f'Record {i}: dob format wrong: {dob!r}'
        # copay_amount must be float
        assert isinstance(got.get('copay_amount'), (int, float)), \
            f'Record {i}: copay_amount must be numeric'
elif domain == 'financial':
    for i, (got, exp) in enumerate(zip(output, exp_records)):
        # amount must be float dollars
        assert isinstance(got.get('amount'), (int, float)), \
            f'Record {i}: amount must be numeric'
        # txn_date must be YYYY-MM-DD
        d = str(got.get('txn_date', ''))
        assert len(d) == 10 and d[4] == '-', \
            f'Record {i}: txn_date format wrong: {d!r}'
        # is_flagged must be bool
        assert isinstance(got.get('is_flagged'), bool), \
            f'Record {i}: is_flagged must be bool, got {type(got.get(\"is_flagged\"))}'
elif domain == 'logistics':
    for i, (got, exp) in enumerate(zip(output, exp_records)):
        # weight_kg must be float
        assert isinstance(got.get('weight_kg'), (int, float)), \
            f'Record {i}: weight_kg must be numeric'
        # shipped_date must be YYYY-MM-DD
        d = str(got.get('shipped_date', ''))
        assert len(d) == 10 and d[4] == '-', \
            f'Record {i}: shipped_date format wrong: {d!r}'
        # estimated_days must be int
        assert isinstance(got.get('estimated_days'), int), \
            f'Record {i}: estimated_days must be int'
print('TYPE_CONVERSIONS_OK')
\"" "type_conversions_wrong"

# ── Check 8: Null values handled per spec rules ───────────────────────────────
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
output = json.load(open('output.json'))
exp_records = expected['records']
null_rules = expected['null_rules']
# For each record where expected has a default value, verify output matches
for i, (got, exp) in enumerate(zip(output, exp_records)):
    for field, default_str in null_rules.items():
        exp_val = exp.get(field)
        got_val = got.get(field)
        if exp_val is None:
            # Both should be None or both should use default
            pass
        else:
            assert got_val is not None, \
                f'Record {i}: field {field} should not be null (expected {exp_val!r})'
print('NULL_HANDLING_OK')
\"" "null_handling_wrong"

# ── Check 9: Nested fields flattened correctly ────────────────────────────────
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
output = json.load(open('output.json'))
exp_records = expected['records']
# Verify no nested dicts remain in output records
for i, rec in enumerate(output):
    for k, v in rec.items():
        assert not isinstance(v, dict), \
            f'Record {i}: field {k!r} is still a nested dict (not flattened)'
# Spot-check nested field values match expected
domain = expected['domain']
if domain in ('ecommerce', 'healthcare', 'financial', 'logistics'):
    nested_target_pairs = {
        'ecommerce': ('city', 'country'),
        'healthcare': ('plan_id', 'plan_name'),
        'financial': ('card_last4', 'card_network'),
        'logistics': ('origin_country', 'destination_country'),
    }
    fields = nested_target_pairs.get(domain, ())
    for i, (got, exp) in enumerate(zip(output, exp_records)):
        for f in fields:
            assert str(got.get(f)) == str(exp.get(f)), \
                f'Record {i}: nested field {f}: got {got.get(f)!r}, expected {exp.get(f)!r}'
print('NESTED_FIELDS_OK')
\"" "nested_fields_not_flattened"

# ── Check 10: No data loss — all source records appear in output ──────────────
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
output = json.load(open('output.json'))
# Count must match exactly
assert len(output) == expected['record_count'], \
    f'Data loss: {len(output)} output records vs {expected[\"record_count\"]} source records'
# No record should be entirely empty
for i, rec in enumerate(output):
    non_null = [v for v in rec.values() if v is not None]
    assert non_null, f'Record {i} is entirely null — possible data loss'
print('NO_DATA_LOSS_OK')
\"" "data_loss_detected"

fi  # end if output.json and expected.json present

# ── Check 11: Attestation ─────────────────────────────────────────────────────
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
    "partial_score": $PARTIAL
  },
  "failure_modes": $FM
}
JSON
