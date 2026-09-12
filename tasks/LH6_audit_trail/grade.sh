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

# Load expected for seed-specific file paths
DB_FILE=$(python3 -c "import json; print(json.load(open('$REPORTS/expected.json')).get('db_file', 'app/db.py'))" 2>/dev/null || echo "app/db.py")
VIEWS_FILE=$(python3 -c "import json; print(json.load(open('$REPORTS/expected.json')).get('views_file', 'app/views.py'))" 2>/dev/null || echo "app/views.py")
SEARCH_FIELD=$(python3 -c "import json; print(json.load(open('$REPORTS/expected.json')).get('search_field', 'query'))" 2>/dev/null || echo "query")

# ── Bug 1: SQL Injection fixed (parameterized query) ────────────────────────
check "python3 -c \"
with open('$DB_FILE') as f:
    content = f.read()
# Should NOT have f-string or format or % in SQL query
has_injection = ('f\"SELECT' in content or 'f\\\"SELECT' in content or
                 '\".format(' in content or \"% (\" in content.split('SELECT')[1] if 'SELECT' in content else False)
# Should have parameterized query (? or %s placeholder)
has_param = ('?' in content and 'execute' in content) or ('%s' in content and 'execute' in content)
assert has_param or not has_injection, 'SQL injection not fixed: still uses string formatting in query'
print('BUG1_FIXED')
\"" "bug1_sql_injection_not_fixed"

# ── Bug 2: XSS fixed (HTML escaping) ────────────────────────────────────────
check "python3 -c \"
with open('$VIEWS_FILE') as f:
    content = f.read()
# Should have html escaping (html.escape, markupsafe.escape, or manual &amp; etc)
has_escape = ('html.escape' in content or 'escape(' in content or
              'markupsafe' in content or '&amp;' in content or
              'cgi.escape' in content or 'bleach' in content)
assert has_escape, 'XSS not fixed: no HTML escaping found'
print('BUG2_FIXED')
\"" "bug2_xss_not_fixed"

# ── Bug 3: Auth check added ─────────────────────────────────────────────────
check "python3 -c \"
with open('$VIEWS_FILE') as f:
    content = f.read()
# Find the admin endpoint function and check for auth
import re
# Look for admin function with auth check
admin_section = content[content.find('admin'):]  if 'admin' in content else ''
has_auth = ('is_admin' in admin_section or 'role' in admin_section or
            'authorized' in admin_section or 'permission' in admin_section or
            'authenticate' in admin_section or '403' in admin_section or
            'Forbidden' in admin_section or 'Unauthorized' in admin_section)
assert has_auth, 'Auth check not added to admin endpoint'
print('BUG3_FIXED')
\"" "bug3_auth_not_fixed"

# ── Bug 4: Pagination offset fixed ──────────────────────────────────────────
check "python3 -c \"
with open('$VIEWS_FILE') as f:
    content = f.read()
# The buggy offset was: (page) * per_page or (page - 1) * per_page + 1
# Correct is: (page - 1) * per_page
import re
# Find offset calculation
offset_matches = re.findall(r'offset\s*=\s*(.+)', content)
if offset_matches:
    expr = offset_matches[0].strip()
    # Should have (page - 1) pattern
    ok = '- 1' in expr or 'page-1' in expr or 'page -1' in expr
    assert ok, f'Pagination offset looks wrong: {expr}'
else:
    # Check for slice or skip patterns
    ok = '(page - 1)' in content or '(page-1)' in content
    assert ok, 'No offset calculation found with correct (page-1) pattern'
print('BUG4_FIXED')
\"" "bug4_pagination_not_fixed"

# ── Bug 5: CSV export fixed ──────────────────────────────────────────────────
check "python3 -c \"
import importlib.util, sys, os
# Check that CSV export properly handles commas and quotes
with open('$VIEWS_FILE') as f:
    content = f.read()
# Should use csv module, or manual quoting with double-quote escaping
has_csv_fix = ('import csv' in content or 'csv.writer' in content or
               '\"\"' in content or 'replace(\\'\"\\'' in content or
               '.writerow' in content)
assert has_csv_fix, 'CSV export not fixed: no proper quoting found'
print('BUG5_FIXED')
\"" "bug5_csv_not_fixed"

# ── Bug fix count >= 4 ──────────────────────────────────────────────────────
BUG_FIXES=$PASSED
check "[ $BUG_FIXES -ge 4 ]" "fewer_than_4_bugs_fixed"

# ── Audit log exists and has entries ─────────────────────────────────────────
check "python3 -c \"
with open('AUDIT_LOG.md') as f:
    content = f.read()
import re
entries = re.findall(r'^## Fix \d+:', content, re.MULTILINE)
assert len(entries) >= 4, f'Only {len(entries)} audit entries (need >= 4)'
print(f'AUDIT_ENTRIES: {len(entries)}')
\"" "audit_log_too_few_entries"

# ── Audit entries have required fields ───────────────────────────────────────
check "python3 -c \"
with open('AUDIT_LOG.md') as f:
    content = f.read()
import re
entries = re.split(r'^## Fix \d+:', content, flags=re.MULTILINE)[1:]
valid = 0
for entry in entries:
    has_file = '**File**:' in entry
    has_bug = '**Bug**:' in entry
    has_fix = '**Fix**:' in entry
    has_risk = '**Risk**:' in entry
    if has_file and has_bug and has_fix and has_risk:
        valid += 1
assert valid >= 4, f'Only {valid} valid audit entries with all fields (need >= 4)'
print(f'VALID_ENTRIES: {valid}')
\"" "audit_entries_incomplete"

# ── Audit entries reference real files ───────────────────────────────────────
check "python3 -c \"
import os, re
with open('AUDIT_LOG.md') as f:
    content = f.read()
file_refs = re.findall(r'\*\*File\*\*:\s*(.+)', content)
valid = 0
for ref in file_refs:
    path = ref.strip().strip('\`')
    if os.path.exists(path):
        valid += 1
assert valid >= 3, f'Only {valid} audit entries reference real files (need >= 3)'
print(f'REAL_FILE_REFS: {valid}')
\"" "audit_file_refs_invalid"

# ── Audit risk levels are valid ──────────────────────────────────────────────
check "python3 -c \"
import re
with open('AUDIT_LOG.md') as f:
    content = f.read()
risks = re.findall(r'\*\*Risk\*\*:\s*(\w+)', content)
valid_risks = {'low', 'medium', 'high'}
for r in risks:
    assert r.lower() in valid_risks, f'Invalid risk level: {r}'
print(f'RISK_LEVELS_VALID: {len(risks)}')
\"" "audit_risk_levels_invalid"

# ── Attestation ──────────────────────────────────────────────────────────────
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
