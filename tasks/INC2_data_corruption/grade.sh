#!/usr/bin/env bash
# Seed-aware grader for INC2: Data Corruption Recovery
# Reads expected values from expected.json for seed-specific grading.
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

# Write a reusable grading helper that all checks can import
cat > .grader_helpers.py << 'PYEOF'
import json, sys, os

def load_expected(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_records(path='data.json'):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def check_numeric(val, field, rng):
    """Return error string if val is non-numeric or out of range, else None."""
    if val is None:
        return f"field '{field}' is null"
    try:
        num = float(val)
    except (TypeError, ValueError):
        return f"field '{field}' = {val!r} is not numeric"
    lo = rng.get('min')
    hi = rng.get('max')
    if lo is not None and hi is not None:
        if not (lo <= num <= hi):
            return f"field '{field}' = {num} out of range [{lo}, {hi}]"
    return None
PYEOF

# ── Check 1: data.json exists and is valid JSON ──────────────────────────────
check "python3 -c '
import json
with open(\"data.json\", \"r\", encoding=\"utf-8\") as f:
    records = json.load(f)
assert isinstance(records, list) and len(records) > 0
print(\"DATA_JSON_VALID\")
'" "data_json_invalid"

# ── Check 2: recover.py runs without error ───────────────────────────────────
cp data.json data.json.pre_recovery 2>/dev/null || true
check "python3 recover.py" "recover_py_crashes"

# ── Check 3: All records present after recovery (no deletion) ────────────────
check "python3 -c '
import json, sys
sys.path.insert(0, \".\")
expected = json.load(open(\"$EXPECTED\"))
total = expected[\"total_records\"]
records = json.load(open(\"data.json\", encoding=\"utf-8\"))
assert len(records) == total, f\"Expected {total} records got {len(records)}\"
print(\"RECORD_COUNT_OK\")
'" "record_count_wrong"

# ── Check 4: No previously-good records corrupted ────────────────────────────
python3 - << 'PYEOF' > .check4_result.txt 2>&1
import json, sys
sys.path.insert(0, ".")
from .grader_helpers import load_expected, load_records, check_numeric

expected = load_expected("EXPECTED_PLACEHOLDER")
pk        = expected["primary_key"]
cf        = expected["corrupt_field"]
cpks      = set(str(x) for x in expected["corrupted_primary_keys"])
ranges    = expected["field_ranges"]
cf_range  = ranges.get(cf, {})

records = load_records()
errors = []
for record in records:
    pk_val = str(record.get(pk))
    if pk_val in cpks:
        continue
    val = record.get(cf)
    err = check_numeric(val, cf, cf_range)
    if err:
        errors.append(f"Good record pk={pk_val}: {err}")

if errors:
    for e in errors:
        print(f"ERROR: {e}")
    sys.exit(1)
print("GOOD_RECORDS_INTACT")
PYEOF
# Replace placeholder and re-run properly
check "python3 -c '
import json, sys
sys.path.insert(0, \".\")

expected = json.load(open(\"$EXPECTED\"))
pk        = expected[\"primary_key\"]
cf        = expected[\"corrupt_field\"]
cpks      = set(str(x) for x in expected[\"corrupted_primary_keys\"])
cf_range  = expected[\"field_ranges\"].get(cf, {})
lo        = cf_range.get(\"min\")
hi        = cf_range.get(\"max\")

records = json.load(open(\"data.json\", encoding=\"utf-8\"))
for record in records:
    pk_val = str(record.get(pk))
    if pk_val in cpks:
        continue
    val = record.get(cf)
    assert val is not None, f\"Good pk={pk_val}: {cf} is null\"
    try:
        num = float(val)
    except Exception:
        raise AssertionError(f\"Good pk={pk_val}: {cf}={val!r} not numeric\")
    if lo is not None and hi is not None:
        assert lo <= num <= hi, f\"Good pk={pk_val}: {cf}={num} out of [{lo},{hi}]\"
print(\"GOOD_RECORDS_INTACT\")
'" "good_records_modified"

# ── Check 5: Corrupted records have correct recovered values ─────────────────
check "python3 -c '
import json, sys
expected = json.load(open(\"$EXPECTED\"))
pk         = expected[\"primary_key\"]
cf         = expected[\"corrupt_field\"]
exp_vals   = expected[\"expected_recovered_values\"]

records  = json.load(open(\"data.json\", encoding=\"utf-8\"))
pk_map   = {str(r.get(pk)): r for r in records}
for pk_val, exp_val in exp_vals.items():
    record = pk_map.get(pk_val)
    assert record is not None, f\"Record pk={pk_val} missing\"
    actual = record.get(cf)
    try:
        assert abs(float(actual) - float(exp_val)) < 0.01, f\"pk={pk_val}: {cf}={actual!r} expected {exp_val!r}\"
    except (TypeError, ValueError):
        assert str(actual) == str(exp_val), f\"pk={pk_val}: {cf}={actual!r} expected {exp_val!r}\"
print(\"CORRUPTED_RECORDS_RECOVERED\")
'" "corrupted_records_not_recovered"

# ── Check 6: All numeric fields within specified ranges ──────────────────────
check "python3 -c '
import json, sys
expected     = json.load(open(\"$EXPECTED\"))
field_ranges = expected[\"field_ranges\"]

records = json.load(open(\"data.json\", encoding=\"utf-8\"))
for idx, record in enumerate(records):
    for field, rng in field_ranges.items():
        val = record.get(field)
        if val is None:
            continue
        try:
            num = float(val)
        except (TypeError, ValueError):
            raise AssertionError(f\"record[{idx}]: {field}={val!r} not numeric\")
        lo = rng[\"min\"]; hi = rng[\"max\"]
        assert lo <= num <= hi, f\"record[{idx}]: {field}={num} out of [{lo},{hi}]\"
print(\"NUMERIC_RANGES_OK\")
'" "numeric_ranges_violated"

# ── Check 7: All required fields present and non-null in every record ─────────
check "python3 -c '
import json, sys
expected = json.load(open(\"$EXPECTED\"))
required = expected[\"required_fields\"]
pk       = expected[\"primary_key\"]

records = json.load(open(\"data.json\", encoding=\"utf-8\"))
for idx, record in enumerate(records):
    pk_val = record.get(pk, f\"index_{idx}\")
    for field in required:
        val = record.get(field)
        assert val is not None, f\"pk={pk_val}: {field} is null\"
        assert str(val).strip() != \"\", f\"pk={pk_val}: {field} is empty\"
print(\"ALL_REQUIRED_FIELDS_PRESENT\")
'" "required_fields_null"

# ── Check 8: validate.py passes all records ───────────────────────────────────
check "python3 validate.py" "validate_py_fails"

# ── Check 9: recover.py is idempotent ────────────────────────────────────────
if [ -f data.json.pre_recovery ]; then
    cp data.json.pre_recovery data.json
    python3 recover.py 2>/dev/null || true
fi
check "python3 -c '
import json, sys
expected = json.load(open(\"$EXPECTED\"))
pk       = expected[\"primary_key\"]
cf       = expected[\"corrupt_field\"]
exp_vals = expected[\"expected_recovered_values\"]
total    = expected[\"total_records\"]

records = json.load(open(\"data.json\", encoding=\"utf-8\"))
assert len(records) == total, f\"Idempotency: count changed to {len(records)}\"
pk_map  = {str(r.get(pk)): r for r in records}
for pk_val, exp_val in exp_vals.items():
    actual = pk_map.get(pk_val, {}).get(cf)
    try:
        assert abs(float(actual) - float(exp_val)) < 0.01
    except (TypeError, ValueError):
        assert str(actual) == str(exp_val), f\"Idempotency failed pk={pk_val}\"
print(\"IDEMPOTENT_OK\")
'" "recover_not_idempotent"

# ── Check 10: Attestation verdict=pass ───────────────────────────────────────
check "python3 -c '
import json, sys
att = json.load(open(\"$SUBMISSION/attestation.json\"))
assert att.get(\"verdict\") == \"pass\", f\"verdict={att.get(chr(39)+'verdict'+chr(39))!r}\"
print(\"ATTESTATION_OK\")
'" "bad_attestation"

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
