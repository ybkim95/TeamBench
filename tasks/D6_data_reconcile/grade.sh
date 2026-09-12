#!/usr/bin/env bash
# Seed-aware grader for D6: Data Reconciliation
# Reads expected values from expected.json (generated, never shown to agents).
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

# ── Check 1: reconcile.py runs without crashing ──────────────────────────────
check "python3 reconcile.py" "reconcile_crash"

OUTPUT="reconciled.json"

# ── Check 2: Output file exists ──────────────────────────────────────────────
check "test -f '$OUTPUT'" "missing_output_file"

if [ -f "$OUTPUT" ] && [ -f "$EXPECTED" ]; then

# ── Check 3: Output is valid JSON array ──────────────────────────────────────
check "python3 -c \"
import json
data = json.load(open('$OUTPUT'))
assert isinstance(data, list), 'Output must be a JSON array'
assert len(data) > 0, 'Output array must not be empty'
print('VALID_JSON_ARRAY_OK')
\"" "invalid_json_or_not_array"

# ── Check 4: Correct total record count ──────────────────────────────────────
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
actual = json.load(open('$OUTPUT'))
assert len(actual) == expected['total_records'], \
    f'Expected {expected[\"total_records\"]} records, got {len(actual)}'
print('RECORD_COUNT_OK')
\"" "wrong_record_count"

# ── Check 5: All IDs present (no data loss) ───────────────────────────────────
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
actual = json.load(open('$OUTPUT'))
id_field = expected['id_field']
expected_ids = set(expected['per_record'].keys())
actual_ids = {r[id_field] for r in actual}
missing = expected_ids - actual_ids
extra = actual_ids - expected_ids
assert not missing, f'Missing records: {missing}'
assert not extra, f'Unexpected records: {extra}'
print('NO_DATA_LOSS_OK')
\"" "data_loss_or_extra_records"

# ── Check 6: Output sorted ascending by id_field ─────────────────────────────
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
actual = json.load(open('$OUTPUT'))
id_field = expected['id_field']
ids = [r[id_field] for r in actual]
assert ids == sorted(ids), f'Output not sorted by {id_field}'
print('SORT_ORDER_OK')
\"" "wrong_sort_order"

# ── Check 7: Required output fields present on every record ──────────────────
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
actual = json.load(open('$OUTPUT'))
required = set(expected['all_output_fields'])
for rec in actual:
    missing = required - set(rec.keys())
    assert not missing, f'Record {list(rec.values())[0]} missing fields: {missing}'
print('ALL_FIELDS_PRESENT_OK')
\"" "missing_output_fields"

# ── Check 8: reconcile_source values are valid ───────────────────────────────
check "python3 -c \"
import json
actual = json.load(open('$OUTPUT'))
valid = {'merged', 'manual_override', 'system_a_only', 'system_b_only'}
for rec in actual:
    src = rec.get('reconcile_source')
    assert src in valid, f'Invalid reconcile_source={src!r} on {list(rec.values())[0]}'
print('RECONCILE_SOURCE_VALID_OK')
\"" "invalid_reconcile_source"

# ── Check 9: Manual-override records — System B wins all fields ───────────────
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
actual = json.load(open('$OUTPUT'))
id_field = expected['id_field']
override_ids = set(expected.get('manual_override_ids', []))
actual_map = {r[id_field]: r for r in actual}
errors = []
for rid in override_ids:
    rec = actual_map.get(rid, {})
    src = rec.get('reconcile_source')
    if src != 'manual_override':
        errors.append(f'{rid}: reconcile_source={src!r}, expected manual_override')
    exp_vals = expected['per_record'][rid]['expected_values']
    for f, v in exp_vals.items():
        if f in (id_field, 'reconcile_source'):
            continue
        got = rec.get(f)
        if got != v:
            errors.append(f'{rid}.{f}: got {got!r}, expected {v!r}')
assert not errors, str(errors[:5])
print('MANUAL_OVERRIDE_OK')
\"" "manual_override_wrong"

# ── Check 10: Ownership-conflict records — field ownership respected ───────────
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
actual = json.load(open('$OUTPUT'))
id_field = expected['id_field']
conflict_ids = set(expected.get('ownership_conflict_ids', []))
a_owned = expected['a_owned_fields']
b_owned = expected['b_owned_fields']
actual_map = {r[id_field]: r for r in actual}
errors = []
for rid in conflict_ids:
    rec = actual_map.get(rid, {})
    exp_vals = expected['per_record'][rid]['expected_values']
    for f in a_owned + b_owned:
        got = rec.get(f)
        want = exp_vals.get(f)
        if got != want:
            errors.append(f'{rid}.{f}: got {got!r}, expected {want!r}')
assert not errors, str(errors[:5])
print('FIELD_OWNERSHIP_OK')
\"" "field_ownership_wrong"

# ── Check 11: Timestamp-conflict records — newer timestamp wins shared fields ──
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
actual = json.load(open('$OUTPUT'))
id_field = expected['id_field']
ts_conflict_ids = set(expected.get('timestamp_conflict_ids', []))
shared = expected['shared_fields']
actual_map = {r[id_field]: r for r in actual}
errors = []
for rid in ts_conflict_ids:
    rec = actual_map.get(rid, {})
    exp_vals = expected['per_record'][rid]['expected_values']
    for f in shared:
        got = rec.get(f)
        want = exp_vals.get(f)
        if got != want:
            errors.append(f'{rid}.{f}: got {got!r}, expected {want!r} (timestamp conflict)')
assert not errors, str(errors[:5])
print('TIMESTAMP_CONFLICT_OK')
\"" "timestamp_conflict_wrong"

# ── Check 12: System-A-only records correct (B fields are null) ───────────────
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
actual = json.load(open('$OUTPUT'))
id_field = expected['id_field']
only_a_ids = set(expected.get('only_a_ids', []))
b_owned = expected['b_owned_fields']
actual_map = {r[id_field]: r for r in actual}
errors = []
for rid in only_a_ids:
    rec = actual_map.get(rid, {})
    src = rec.get('reconcile_source')
    if src != 'system_a_only':
        errors.append(f'{rid}: reconcile_source={src!r}, expected system_a_only')
    for f in b_owned:
        val = rec.get(f)
        if val is not None:
            errors.append(f'{rid}.{f}: expected null, got {val!r}')
assert not errors, str(errors[:5])
print('ONLY_A_RECORDS_OK')
\"" "only_a_records_wrong"

# ── Check 13: System-B-only records correct (A fields are null) ───────────────
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
actual = json.load(open('$OUTPUT'))
id_field = expected['id_field']
only_b_ids = set(expected.get('only_b_ids', []))
a_owned = expected['a_owned_fields']
actual_map = {r[id_field]: r for r in actual}
errors = []
for rid in only_b_ids:
    rec = actual_map.get(rid, {})
    src = rec.get('reconcile_source')
    if src != 'system_b_only':
        errors.append(f'{rid}: reconcile_source={src!r}, expected system_b_only')
    for f in a_owned:
        val = rec.get(f)
        if val is not None:
            errors.append(f'{rid}.{f}: expected null, got {val!r}')
assert not errors, str(errors[:5])
print('ONLY_B_RECORDS_OK')
\"" "only_b_records_wrong"

# ── Check 14: Agreement records are correct ───────────────────────────────────
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
actual = json.load(open('$OUTPUT'))
id_field = expected['id_field']
agree_ids = set(expected.get('agree_ids', []))
actual_map = {r[id_field]: r for r in actual}
errors = []
for rid in agree_ids:
    rec = actual_map.get(rid, {})
    exp_vals = expected['per_record'][rid]['expected_values']
    for f, want in exp_vals.items():
        if f in (id_field, 'reconcile_source'):
            continue
        got = rec.get(f)
        if got != want:
            errors.append(f'{rid}.{f}: got {got!r}, expected {want!r}')
assert not errors, str(errors[:5])
print('AGREE_RECORDS_OK')
\"" "agree_records_wrong"

# ── Check 15: No extra fields in output records ───────────────────────────────
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
actual = json.load(open('$OUTPUT'))
allowed = set(expected['all_output_fields'])
errors = []
for rec in actual:
    extra = set(rec.keys()) - allowed
    if extra:
        id_field = expected['id_field']
        errors.append(f'{rec.get(id_field)}: extra fields {extra}')
assert not errors, str(errors[:5])
print('NO_EXTRA_FIELDS_OK')
\"" "extra_fields_in_output"

# ── Check 16: Null-filled fields are JSON null, not string 'null' ─────────────
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
actual = json.load(open('$OUTPUT'))
id_field = expected['id_field']
errors = []
for rec in actual:
    for k, v in rec.items():
        if v == 'null':
            errors.append(f'{rec.get(id_field)}.{k}: string null instead of JSON null')
assert not errors, str(errors[:5])
print('NULL_TYPE_OK')
\"" "string_null_instead_of_json_null"

# ── Check 17: All per-record expected values match ────────────────────────────
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
actual = json.load(open('$OUTPUT'))
id_field = expected['id_field']
actual_map = {r[id_field]: r for r in actual}
errors = []
for rid, info in expected['per_record'].items():
    exp_vals = info['expected_values']
    rec = actual_map.get(rid, {})
    for f, want in exp_vals.items():
        got = rec.get(f)
        if got != want:
            errors.append(f'{rid}.{f}: got {got!r}, want {want!r}')
if errors:
    # Report first 5 mismatches
    raise AssertionError(str(errors[:5]))
print('ALL_RECORDS_CORRECT_OK')
\"" "per_record_values_wrong"

fi

# ── Check 18: Attestation ─────────────────────────────────────────────────────
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
