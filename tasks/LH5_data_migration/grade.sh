#!/usr/bin/env bash
set -o pipefail
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

# ── Check 1: validate.py passes all checks ───────────────────────────────────
check "python3 validate.py" "validate_fail"

# ── Check 2: migration_report.json exists ────────────────────────────────────
REPORT="migration_report.json"
check "test -f '$REPORT'" "missing_migration_report"

if [ -f "$REPORT" ]; then

# ── Check 3: migration status = success ──────────────────────────────────────
check "python3 -c \"
import json
r = json.load(open('$REPORT'))
assert r.get('status') == 'success', f'status={r.get(\"status\")}'
\"" "migration_not_success"

# ── Check 4: all steps completed and logged ───────────────────────────────────
check "python3 -c \"
import json
r = json.load(open('$REPORT'))
steps = r.get('steps_completed', [])
assert len(steps) >= 5, f'only {len(steps)} steps completed'
assert r.get('total_steps', 0) >= 5, 'total_steps < 5'
\"" "insufficient_steps"

fi

# ── Check 5: migration_log.jsonl exists and is non-empty ─────────────────────
LOG="migration_log.jsonl"
check "test -f '$LOG' && [ \$(wc -l < '$LOG') -gt 0 ]" "missing_migration_log"

# ── Check 6: steps executed in correct order ──────────────────────────────────
check "python3 -c \"
import json, os
if not os.path.exists('$LOG') or not os.path.exists('$REPORT'):
    raise AssertionError('missing files')
step_order = []
with open('$LOG') as f:
    for line in f:
        if not line.strip(): continue
        e = json.loads(line)
        if e.get('status') == 'start' and e.get('step') not in ('migration',):
            step_order.append(e['step'])
r = json.load(open('$REPORT'))
expected = r.get('steps_completed', [])
assert step_order == expected, f'order mismatch: got {step_order} expected {expected}'
\"" "steps_out_of_order"

# ── Check 7: backup directory exists with files ───────────────────────────────
check "python3 -c \"
import os
bd = 'data/backup'
assert os.path.isdir(bd), f'backup dir missing: {bd}'
files = [f for f in os.listdir(bd) if not f.startswith('.')]
assert len(files) > 0, 'backup directory is empty'
\"" "backup_missing"

# ── Check 8: row counts match source ─────────────────────────────────────────
check "python3 -c \"
import json, os
# Read expected from grader expected.json
exp_path = '$REPORTS/expected.json'
if os.path.exists(exp_path):
    exp = json.load(open(exp_path))
    expected_rows = exp.get('primary_row_count', 0)
    primary_table = exp.get('primary_table', 'records')
else:
    expected_rows = None
    primary_table = 'records'

# Count dest rows
dest_path = f'data/new_format/{primary_table}.jsonl'
assert os.path.exists(dest_path), f'dest file missing: {dest_path}'
count = sum(1 for l in open(dest_path) if l.strip())
if expected_rows is not None:
    assert count == expected_rows, f'row count mismatch: dest={count} expected={expected_rows}'
else:
    assert count > 0, 'destination file is empty'
\"" "row_count_mismatch"

# ── Check 9: checksums.json valid ────────────────────────────────────────────
check "python3 -c \"
import json
assert __import__('os').path.exists('checksums.json'), 'checksums.json missing'
cs = json.load(open('checksums.json'))
assert 'source' in cs, 'missing source key'
assert 'transformed' in cs, 'missing transformed key'
assert len(cs['source']) > 0, 'source checksums empty'
assert len(cs['transformed']) > 0, 'transformed checksums empty'
for section, entries in cs.items():
    for fname, chk in entries.items():
        assert isinstance(chk, str) and len(chk) == 64, f'invalid checksum {fname}: {chk!r}'
\"" "checksums_invalid"

# ── Check 10: verification_report.json counts_match=true ─────────────────────
check "python3 -c \"
import json
vr_path = 'verification_report.json'
assert __import__('os').path.exists(vr_path), 'verification_report.json missing'
vr = json.load(open(vr_path))
assert vr.get('counts_match') is True, f'counts_match={vr.get(\"counts_match\")}'
assert vr.get('source_count') == vr.get('dest_count'), \
    f'source_count={vr.get(\"source_count\")} != dest_count={vr.get(\"dest_count\")}'
\"" "verification_report_invalid"

# ── Check 11: no orphaned foreign key references ──────────────────────────────
cat > /tmp/_lh5_check_orphans.py << 'PYEOF'
import json, os, sys
exp_path = sys.argv[1]
workspace = sys.argv[2]
if not os.path.exists(exp_path):
    print("SKIP: expected.json not found")
    sys.exit(0)
exp = json.load(open(exp_path))
ref_table = exp.get("ref_table", "")
ref_key = exp.get("ref_key", "")
primary_table = exp.get("primary_table", "")
if not ref_table or not ref_key or not primary_table:
    print("SKIP: missing ref_table/ref_key/primary_table in expected.json")
    sys.exit(0)
ref_path = os.path.join(workspace, "data", "new_format", ref_table + ".jsonl")
primary_path = os.path.join(workspace, "data", "new_format", primary_table + ".jsonl")
if not os.path.exists(ref_path) or not os.path.exists(primary_path):
    print(f"FAIL: missing {ref_path} or {primary_path}")
    sys.exit(1)
valid_ids = set()
with open(ref_path) as f:
    for line in f:
        if line.strip():
            rec = json.loads(line)
            if ref_key in rec:
                valid_ids.add(str(rec[ref_key]))
orphans = []
with open(primary_path) as f:
    for line in f:
        if line.strip():
            rec = json.loads(line)
            val = str(rec.get(ref_key, ""))
            if val and val not in valid_ids:
                orphans.append(val)
if orphans:
    print(f"FAIL: {len(orphans)} orphaned {ref_key} values: {orphans[:3]}")
    sys.exit(1)
print(f"PASS: no orphaned {ref_key} references")
sys.exit(0)
PYEOF
check "python3 /tmp/_lh5_check_orphans.py '$REPORTS/expected.json' '$WORKSPACE'" "orphaned_references"

# ── Check 12: new format files are valid JSONL ────────────────────────────────
check "python3 -c \"
import json, os
dest_dir = 'data/new_format'
jsonl_files = [f for f in os.listdir(dest_dir) if f.endswith('.jsonl')]
assert len(jsonl_files) >= 2, f'expected >= 2 jsonl files, got {len(jsonl_files)}'
for fname in jsonl_files:
    path = os.path.join(dest_dir, fname)
    count = 0
    with open(path) as f:
        for line in f:
            if line.strip():
                rec = json.loads(line)  # must be valid JSON
                assert isinstance(rec, dict), f'{fname}: line is not a JSON object'
                count += 1
    assert count > 0, f'{fname} is empty'
\"" "invalid_jsonl_output"

# ── Check 13: attestation ────────────────────────────────────────────────────
# ── Attestation recorded as METADATA, never scored ───────────────────────
# de-scored-by: scripts/repair_graders.py (R3 attestation-is-protocol)
# attestation.json is a PROTOCOL property of the run (already enforced as a
# hard gate in harness/grade_task.py), not a property of the submitted
# artifact. Scoring it let an agent buy partial credit by writing one JSON
# file, which is the confound behind the withdrawn "removing the Verifier
# improves partial score" result. Recorded here, excluded from partial_score.
echo "metadata: attestation_present=$([ -f "${SUBMISSION:-}/attestation.json" ] && echo yes || echo no)"

PARTIAL=$(python3 -c "print(round($PASSED/max(1,$CHECKS), 2))")
if [ "$PASSED" -eq "$CHECKS" ]; then SUCCESS=1; PASS=true; else SUCCESS=0; PASS=false; fi
FM=$(python3 -c "import json; print(json.dumps([x for x in '${FAILURES}'.split(',') if x]))")

cat > "$REPORTS/score.json" <<JSON
{
  "pass": $PASS,
  "primary": {"success": $SUCCESS},
  "secondary": {"checks_passed": $PASSED, "checks_total": $CHECKS, "partial_score": $PARTIAL},
  "failure_modes": $FM
}
JSON
