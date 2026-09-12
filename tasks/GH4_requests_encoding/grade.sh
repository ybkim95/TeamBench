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

# 1. Python syntax valid
check "python3 -c \"import ast; ast.parse(open('http_response.py').read())\"" "syntax_error"

# 2. _parse_content_type still present
check "grep -q '_parse_content_type' http_response.py" "content_type_parser_removed"

# 3. apparent_encoding still present (must not remove detection)
check "grep -q 'apparent_encoding' http_response.py" "apparent_encoding_removed"

# 4. No eval/exec introduced
check "! grep -qE '\beval\s*\(|\bexec\s*\(' http_response.py" "eval_exec_introduced"

# 5. test_json_utf8_default (core fix)
check "python3 -c \"
import sys; sys.path.insert(0, '.')
from test_encoding import TestJsonUtf8Default
TestJsonUtf8Default().test_json_utf8_default()
\"" "json_utf8_default_fails"

# 6. test_json_with_charset (must not break — explicit charset)
check "python3 -c \"
import sys; sys.path.insert(0, '.')
from test_encoding import TestExplicitCharset
TestExplicitCharset().test_json_with_charset()
\"" "explicit_charset_broken"

# 7. test_json_chinese (core fix)
check "python3 -c \"
import sys; sys.path.insert(0, '.')
from test_encoding import TestJsonUtf8Default
TestJsonUtf8Default().test_json_chinese()
\"" "json_chinese_fails"

# 8. test_html_uses_detection (must not break)
check "python3 -c \"
import sys; sys.path.insert(0, '.')
from test_encoding import TestNonJsonDetection
TestNonJsonDetection().test_html_uses_detection()
\"" "html_detection_broken"

# 9. test_json_method_works (core fix)
check "python3 -c \"
import sys; sys.path.insert(0, '.')
from test_encoding import TestJsonUtf8Default
TestJsonUtf8Default().test_json_method_works()
\"" "json_method_broken"

# 10. test_content_type_parsing (must not break)
check "python3 -c \"
import sys; sys.path.insert(0, '.')
from test_encoding import TestContentTypeParsing
TestContentTypeParsing().test_content_type_parsing()
\"" "content_type_parsing_broken"

# 11. Attestation
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
