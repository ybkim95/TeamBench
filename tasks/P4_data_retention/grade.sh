#!/usr/bin/env bash
# Seed-aware grader for P4: Data Retention Policy Implementation
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

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
if [ -f "$REPO_ROOT/venv/bin/python3" ]; then
  PYTHON="$REPO_ROOT/venv/bin/python3"
else
  PYTHON="python3"
fi

CHECKS=0; PASSED=0; FAILURES=""
check() {
  CHECKS=$((CHECKS + 1))
  if eval "$1" 2>/dev/null; then
    PASSED=$((PASSED + 1))
  else
    FAILURES="${FAILURES:+${FAILURES},}$2"
  fi
}

RETENTION_PY="$WORKSPACE/retention.py"
SEED_SQL="$WORKSPACE/seed_data.sql"
DB_PATH="$WORKSPACE/grade_test.db"

# ── Check 1: retention.py exists and has valid Python syntax ──────────────────
check "$PYTHON -m py_compile '$RETENTION_PY' && echo OK" "retention_py_syntax_error"

# ── Check 2: seed_data.sql exists and is non-empty ───────────────────────────
check "[ -s '$SEED_SQL' ] && echo OK" "seed_sql_missing_or_empty"

# ── Check 3: RETENTION_DAYS dict is populated with all required types ─────────
check "$PYTHON -c '
import sys, json; sys.path.insert(0, \"$WORKSPACE\")
from retention import RETENTION_DAYS
expected = json.load(open(\"$EXPECTED\"))
required = set(expected[\"retention_config\"].keys())
actual = set(RETENTION_DAYS.keys())
missing = required - actual
assert not missing, \"Missing data types in RETENTION_DAYS: \" + str(missing)
print(\"RETENTION_DAYS_COMPLETE\")
'" "retention_days_missing_types"

# ── Check 4: Retention periods are correct per expected.json ──────────────────
check "$PYTHON -c '
import sys, json; sys.path.insert(0, \"$WORKSPACE\")
from retention import RETENTION_DAYS
expected = json.load(open(\"$EXPECTED\"))
rc = expected[\"retention_config\"]
wrong = []
for tid, cfg in rc.items():
    if tid in RETENTION_DAYS:
        actual = RETENTION_DAYS[tid]
        exp = cfg[\"retention_days\"]
        if actual != exp:
            wrong.append(f\"{tid}: got {actual} expected {exp}\")
assert not wrong, \"Wrong retention periods: \" + \"; \".join(wrong)
print(\"RETENTION_PERIODS_CORRECT\")
'" "retention_periods_incorrect"

# ── Check 5: PII_TYPES set is correct ────────────────────────────────────────
check "$PYTHON -c '
import sys, json; sys.path.insert(0, \"$WORKSPACE\")
from retention import PII_TYPES
expected = json.load(open(\"$EXPECTED\"))
required = set(expected[\"pii_types\"])
actual = set(PII_TYPES)
missing = required - actual
extra = actual - required
assert not missing, \"Missing PII types: \" + str(missing)
assert not extra, \"Unexpected PII types: \" + str(extra)
print(\"PII_TYPES_CORRECT\")
'" "pii_types_incorrect"

if [ -f "$RETENTION_PY" ] && [ -f "$SEED_SQL" ] && [ -f "$EXPECTED" ]; then

# Initialise a fresh test DB for grading
rm -f "$DB_PATH"
sqlite3 "$DB_PATH" < "$SEED_SQL" 2>/dev/null || true

# ── Check 6: run_retention() runs without exception and returns a dict ────────
check "$PYTHON -c '
import sys, json; sys.path.insert(0, \"$WORKSPACE\")
from retention import run_retention
result = run_retention(\"$DB_PATH\")
assert isinstance(result, dict), \"run_retention must return a dict, got \" + type(result).__name__
required_keys = {\"deleted\", \"anonymized\", \"skipped_exempt\", \"audit_entries_written\"}
missing = required_keys - set(result.keys())
assert not missing, \"Summary dict missing keys: \" + str(missing)
print(\"RUN_RETENTION_RETURNS_DICT\")
'" "run_retention_bad_return"

# Re-init DB for subsequent checks
rm -f "$DB_PATH"
sqlite3 "$DB_PATH" < "$SEED_SQL" 2>/dev/null || true

# ── Check 7: Audit log entries are written before deletion ────────────────────
check "$PYTHON -c '
import sys, json, sqlite3; sys.path.insert(0, \"$WORKSPACE\")
from retention import run_retention
result = run_retention(\"$DB_PATH\")
conn = sqlite3.connect(\"$DB_PATH\")
audit_count = conn.execute(\"SELECT COUNT(*) FROM retention_audit\").fetchone()[0]
conn.close()
assert audit_count > 0, \"retention_audit table is empty — audit entries must be written\"
assert result[\"audit_entries_written\"] > 0, \"audit_entries_written counter is 0\"
assert result[\"audit_entries_written\"] == audit_count, (
    f\"audit_entries_written={result['"'"'audit_entries_written'"'"']} but table has {audit_count} rows\"
)
print(\"AUDIT_LOG_WRITTEN\")
'" "audit_log_not_written"

# Re-init DB
rm -f "$DB_PATH"
sqlite3 "$DB_PATH" < "$SEED_SQL" 2>/dev/null || true

# ── Check 8: Legal hold prevents deletion ────────────────────────────────────
check "$PYTHON -c '
import sys, json, sqlite3; sys.path.insert(0, \"$WORKSPACE\")
from retention import run_retention, TABLE_NAMES, RETENTION_DAYS
result = run_retention(\"$DB_PATH\")
conn = sqlite3.connect(\"$DB_PATH\")
# All records with legal_hold=1 that are expired must still exist
held_still_present = 0
for tid, table in TABLE_NAMES.items():
    try:
        rows = conn.execute(
            f\"SELECT COUNT(*) FROM {table} WHERE legal_hold=1 AND expires_at < datetime('"'"'now'"'"')\"
        ).fetchone()[0]
        held_still_present += rows
    except Exception:
        pass
conn.close()
assert held_still_present > 0, (
    \"All legal_hold records were deleted — legal hold must prevent deletion\"
)
print(\"LEGAL_HOLD_PREVENTS_DELETION\")
'" "legal_hold_not_respected"

# Re-init DB
rm -f "$DB_PATH"
sqlite3 "$DB_PATH" < "$SEED_SQL" 2>/dev/null || true

# ── Check 9: Exempt records have skipped_exempt audit entries ─────────────────
check "$PYTHON -c '
import sys, json, sqlite3; sys.path.insert(0, \"$WORKSPACE\")
from retention import run_retention
result = run_retention(\"$DB_PATH\")
conn = sqlite3.connect(\"$DB_PATH\")
skipped_audit = conn.execute(
    \"SELECT COUNT(*) FROM retention_audit WHERE action='"'"'skipped_exempt'"'"'\"
).fetchone()[0]
conn.close()
assert result[\"skipped_exempt\"] > 0, \"skipped_exempt count is 0 — exempt records must be skipped\"
assert skipped_audit > 0, \"No skipped_exempt audit entries found in retention_audit\"
print(\"EXEMPT_RECORDS_SKIPPED\")
'" "exempt_records_not_skipped"

# Re-init DB
rm -f "$DB_PATH"
sqlite3 "$DB_PATH" < "$SEED_SQL" 2>/dev/null || true

# ── Check 10: PII records are anonymized before deletion ──────────────────────
check "$PYTHON -c '
import sys, json, sqlite3; sys.path.insert(0, \"$WORKSPACE\")
from retention import run_retention, PII_TYPES, TABLE_NAMES
result = run_retention(\"$DB_PATH\")
assert result[\"anonymized\"] > 0, (
    \"anonymized count is 0 — PII records must be anonymized before deletion\"
)
conn = sqlite3.connect(\"$DB_PATH\")
# Check audit trail for anonymized entries
anon_audit = conn.execute(
    \"SELECT COUNT(*) FROM retention_audit WHERE action='"'"'anonymized'"'"'\"
).fetchone()[0]
conn.close()
assert anon_audit > 0, \"No anonymized audit entries found — anonymize step must write audit entry\"
print(\"PII_ANONYMIZED_BEFORE_DELETE\")
'" "pii_not_anonymized"

# Re-init DB
rm -f "$DB_PATH"
sqlite3 "$DB_PATH" < "$SEED_SQL" 2>/dev/null || true

# ── Check 11: Fresh records (not expired) are NOT deleted ─────────────────────
check "$PYTHON -c '
import sys, json, sqlite3; sys.path.insert(0, \"$WORKSPACE\")
from retention import run_retention, TABLE_NAMES
result = run_retention(\"$DB_PATH\")
conn = sqlite3.connect(\"$DB_PATH\")
# Records with expires_at far in the future must still exist
fresh_count = 0
for tid, table in TABLE_NAMES.items():
    try:
        rows = conn.execute(
            f\"SELECT COUNT(*) FROM {table} WHERE expires_at > datetime('"'"'2090-01-01'"'"')\"
        ).fetchone()[0]
        fresh_count += rows
    except Exception:
        pass
conn.close()
assert fresh_count > 0, \"Fresh (unexpired) records were deleted — only expired records must be removed\"
print(\"FRESH_RECORDS_UNTOUCHED\")
'" "fresh_records_deleted"

# Re-init DB
rm -f "$DB_PATH"
sqlite3 "$DB_PATH" < "$SEED_SQL" 2>/dev/null || true

# ── Check 12: Audit log entries have all required fields ─────────────────────
check "$PYTHON -c '
import sys, json, sqlite3; sys.path.insert(0, \"$WORKSPACE\")
from retention import run_retention
result = run_retention(\"$DB_PATH\")
conn = sqlite3.connect(\"$DB_PATH\")
conn.row_factory = sqlite3.Row
entries = conn.execute(\"SELECT * FROM retention_audit\").fetchall()
conn.close()
assert len(entries) > 0, \"retention_audit is empty\"
required_cols = {\"data_type\", \"record_id\", \"action\", \"reason\", \"processed_at\"}
for entry in entries:
    keys = set(entry.keys())
    missing = required_cols - keys
    assert not missing, \"Audit entry missing columns: \" + str(missing)
    assert entry[\"action\"] in (\"anonymized\", \"deleted\", \"skipped_exempt\"), (
        \"Invalid action value: \" + str(entry[\"action\"])
    )
    assert entry[\"processed_at\"], \"processed_at must not be empty\"
print(\"AUDIT_ENTRIES_WELL_FORMED\")
'" "audit_entries_malformed"

# Re-init DB
rm -f "$DB_PATH"
sqlite3 "$DB_PATH" < "$SEED_SQL" 2>/dev/null || true

# ── Check 13: Deleted count matches expected expired non-exempt records ────────
check "$PYTHON -c '
import sys, json, sqlite3; sys.path.insert(0, \"$WORKSPACE\")
from retention import run_retention, TABLE_NAMES
# Count expired non-exempt records BEFORE retention run
conn_before = sqlite3.connect(\"$DB_PATH\")
expected_deletable = 0
for tid, table in TABLE_NAMES.items():
    try:
        rows = conn_before.execute(
            f\"\"\"SELECT COUNT(*) FROM {table}
                WHERE expires_at < datetime('"'"'now'"'"')
                  AND legal_hold = 0
                  AND regulatory_audit = 0
                  AND active_dispute = 0
                  AND consent_pending = 0
                  AND tax_investigation = 0\"\"\"
        ).fetchone()[0]
        expected_deletable += rows
    except Exception:
        pass
conn_before.close()
result = run_retention(\"$DB_PATH\")
assert result[\"deleted\"] == expected_deletable, (
    f\"deleted={result['"'"'deleted'"'"']} but expected {expected_deletable} deletable records\"
)
print(\"DELETE_COUNT_CORRECT\")
'" "delete_count_incorrect"

fi

# ── Check 14: Attestation file produced ──────────────────────────────────────
check "$PYTHON -c '
import json, sys
att_path = \"$SUBMISSION/attestation.json\"
try:
    att = json.load(open(att_path))
    assert att.get(\"verdict\") == \"pass\", \"verdict=\" + str(att.get(\"verdict\"))
except FileNotFoundError:
    raise AssertionError(\"attestation.json not found at \" + att_path)
'" "bad_attestation"

# Cleanup temp DB
rm -f "$DB_PATH"

# ── Score ──────────────────────────────────────────────────────────────────────
PARTIAL=$($PYTHON -c "print(round($PASSED/max(1,$CHECKS), 2))")
if [ "$PASSED" -eq "$CHECKS" ]; then
    SUCCESS=1; PASS=true
else
    SUCCESS=0; PASS=false
fi
FM=$($PYTHON -c "import json; print(json.dumps([x for x in '${FAILURES}'.split(',') if x]))")

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
