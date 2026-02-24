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

check "python3 validate_all.py" "validation_fail"

REPORT="output/budget_report.json"
check "test -f '$REPORT'" "missing_report"

if [ -f "$REPORT" ]; then
check "python3 -c \"
import json
report = json.load(open('$REPORT'))
assert report['files_fixed'] == 3, f'files_fixed={report[\"files_fixed\"]}'
\"" "wrong_files_fixed"

check "python3 -c \"
import json
report = json.load(open('$REPORT'))
assert report['all_valid'] is True, f'all_valid={report[\"all_valid\"]}'
\"" "not_all_valid"

check "python3 -c \"
import json
report = json.load(open('$REPORT'))
assert report['budget_used'] <= 20, f'budget_used={report[\"budget_used\"]} (max 20)'
assert report['budget_total'] == 20, f'budget_total={report[\"budget_total\"]}'
\"" "budget_exceeded"
fi

BLOG="budget_log.jsonl"
BLOG_COUNT=0
if [ -f "$BLOG" ]; then
    BLOG_COUNT=$(wc -l < "$BLOG" | tr -d ' ')
    check "[ $BLOG_COUNT -le 20 ]" "budget_log_exceeded"
fi

# Verify each file is actually fixed
check "python3 -c \"
import json
a = json.load(open('data/file_a.json'))
assert 'version' in a, 'file_a missing version'
assert 'ver' not in a, 'file_a still has ver field'
\"" "file_a_not_fixed"

check "python3 -c \"
import json
from datetime import datetime
b = json.load(open('data/file_b.json'))
dt = datetime.fromisoformat(b['created'].replace('Z', '+00:00'))
assert dt.tzinfo is not None, 'file_b date has no timezone'
\"" "file_b_not_fixed"

check "python3 -c \"
import json
c = json.load(open('data/file_c.json'))
items = c['items']
lower = [i.lower() for i in items]
assert len(lower) == len(set(lower)), f'file_c has case-insensitive duplicates: {items}'
\"" "file_c_not_fixed"

check "python3 -c \"
import json, sys
att = json.load(open(sys.argv[1]))
assert att.get('verdict') == 'pass'
\" '$SUBMISSION/attestation.json'" "bad_attestation"

PARTIAL=$(python3 -c "print(round($PASSED/max(1,$CHECKS), 2))")
if [ "$PASSED" -eq "$CHECKS" ]; then SUCCESS=1; PASS=true; else SUCCESS=0; PASS=false; fi
FM=$(python3 -c "import json; print(json.dumps([x for x in '${FAILURES}'.split(',') if x]))")

cat > "$REPORTS/score.json" <<JSON
{
  "pass": $PASS,
  "primary": {"success": $SUCCESS},
  "secondary": {"checks_passed": $PASSED, "checks_total": $CHECKS, "partial_score": $PARTIAL, "budget_used": ${BLOG_COUNT:-0}},
  "failure_modes": $FM
}
JSON
