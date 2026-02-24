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

# ---------------------------------------------------------------------------
# Check 1: app.py imports without error
# ---------------------------------------------------------------------------
check "python3 -c 'from app import app'" "import_error"

# ---------------------------------------------------------------------------
# Check 2: test_create_note passes
# ---------------------------------------------------------------------------
check "python3 -m pytest test_app.py::NoteAppTestCase::test_create_note -x -q 2>/dev/null || \
       python3 -m unittest test_app.NoteAppTestCase.test_create_note 2>/dev/null" \
      "test_create_note_fail"

# ---------------------------------------------------------------------------
# Check 3: test_get_notes passes
# ---------------------------------------------------------------------------
check "python3 -m pytest test_app.py::NoteAppTestCase::test_get_notes -x -q 2>/dev/null || \
       python3 -m unittest test_app.NoteAppTestCase.test_get_notes 2>/dev/null" \
      "test_get_notes_fail"

# ---------------------------------------------------------------------------
# Check 4: test_notes_sorted passes (newest-first ordering)
# ---------------------------------------------------------------------------
check "python3 -m pytest test_app.py::NoteAppTestCase::test_notes_sorted -x -q 2>/dev/null || \
       python3 -m unittest test_app.NoteAppTestCase.test_notes_sorted 2>/dev/null" \
      "test_notes_sorted_fail"

# ---------------------------------------------------------------------------
# Check 5: test_delete_note passes
# ---------------------------------------------------------------------------
check "python3 -m pytest test_app.py::NoteAppTestCase::test_delete_note -x -q 2>/dev/null || \
       python3 -m unittest test_app.NoteAppTestCase.test_delete_note 2>/dev/null" \
      "test_delete_note_fail"

# ---------------------------------------------------------------------------
# Check 6: deploy.sh contains FLASK_APP=app.py
# ---------------------------------------------------------------------------
check "grep -q 'FLASK_APP=app\.py' deploy.sh" "deploy_flask_app_wrong"

# ---------------------------------------------------------------------------
# Check 7: static/app.js contains application/json (Content-Type fix)
# ---------------------------------------------------------------------------
check "grep -q 'application/json' static/app.js" "frontend_content_type_wrong"

# ---------------------------------------------------------------------------
# Check 8: attestation.json verdict=pass
# ---------------------------------------------------------------------------
check "python3 -c \"
import json, sys
att = json.load(open(sys.argv[1]))
assert att.get('verdict') == 'pass', f'verdict={att.get(\\\"verdict\\\")}'
\" '$SUBMISSION/attestation.json'" "bad_attestation"

# ---------------------------------------------------------------------------
# Write score
# ---------------------------------------------------------------------------
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
