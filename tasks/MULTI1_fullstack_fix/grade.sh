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

# ---------------------------------------------------------------------------
# Seed-aware: read expected.json if present (generated tasks)
# ---------------------------------------------------------------------------
EXPECTED_JSON="$REPORTS/expected.json"
if [ ! -f "$EXPECTED_JSON" ]; then
  # Fallback: look next to grade.sh (static task)
  EXPECTED_JSON="$(dirname "$0")/expected.json"
fi

# Extract values from expected.json, fall back to defaults matching original task
ENTITY_NAME="notes"
SINGULAR="note"
WRONG_APP="application.py"
WRONG_CT="text/plain"
if [ -f "$EXPECTED_JSON" ]; then
  ENTITY_NAME=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('entity_name','notes'))" 2>/dev/null || echo "notes")
  SINGULAR=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('singular','note'))" 2>/dev/null || echo "note")
  WRONG_APP=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('wrong_app_name','application.py'))" 2>/dev/null || echo "application.py")
  WRONG_CT=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('wrong_content_type','text/plain'))" 2>/dev/null || echo "text/plain")
fi

# Discover test class name from test_app.py (seed-aware)
TEST_CLASS=$(python3 -c "
import ast, sys
try:
    tree = ast.parse(open('test_app.py').read())
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and 'TestCase' in node.name:
            print(node.name)
            sys.exit(0)
except Exception:
    pass
print('NoteAppTestCase')
" 2>/dev/null || echo "NoteAppTestCase")

# ---------------------------------------------------------------------------
# Check 1: app.py imports without error
# ---------------------------------------------------------------------------
check "python3 -c 'from app import app'" "import_error"

# ---------------------------------------------------------------------------
# Check 2: create test passes (test_create_<singular>)
# ---------------------------------------------------------------------------
check "python3 -m unittest test_app.${TEST_CLASS}.test_create_${SINGULAR} 2>/dev/null" \
      "test_create_fail"

# ---------------------------------------------------------------------------
# Check 3: get test passes (test_get_<entity>)
# ---------------------------------------------------------------------------
check "python3 -m unittest test_app.${TEST_CLASS}.test_get_${ENTITY_NAME} 2>/dev/null" \
      "test_get_fail"

# ---------------------------------------------------------------------------
# Check 4: sorted test passes (test_<entity>_sorted)
# ---------------------------------------------------------------------------
check "python3 -m unittest test_app.${TEST_CLASS}.test_${ENTITY_NAME}_sorted 2>/dev/null" \
      "test_sorted_fail"

# ---------------------------------------------------------------------------
# Check 5: delete test passes (test_delete_<singular>)
# ---------------------------------------------------------------------------
check "python3 -m unittest test_app.${TEST_CLASS}.test_delete_${SINGULAR} 2>/dev/null" \
      "test_delete_fail"

# ---------------------------------------------------------------------------
# Check 6: deploy.sh contains FLASK_APP=app.py (not the wrong app name)
# ---------------------------------------------------------------------------
check "grep -q 'FLASK_APP=app\.py' deploy.sh" "deploy_flask_app_wrong"

# ---------------------------------------------------------------------------
# Check 7: static/app.js contains application/json and NOT the wrong Content-Type
# ---------------------------------------------------------------------------
check "grep -q 'application/json' static/app.js && ! grep -q '${WRONG_CT}' static/app.js" \
      "frontend_content_type_wrong"

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
