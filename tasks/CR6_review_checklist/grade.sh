#!/usr/bin/env bash
# Grade script for CR6: Code Review with False Positive Triage
# Arguments:
#   $1 = WORKSPACE  (directory containing pull_request.diff, review_report.json)
#   $2 = REPORTS    (grader-only directory; contains expected.json)
#   $3 = SUBMISSION (directory where the agent writes attestation.json)
#   $4 = TASK_DIR   (task definition directory)
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

EXPECTED="$REPORTS/expected.json"

# ── Check 1: review_report.json exists and is valid JSON ────────────────
check "python3 -c \"
import json
with open('review_report.json') as f:
    data = json.load(f)
assert isinstance(data, dict), 'review_report.json must be a JSON object'
print('VALID_JSON')
\"" "invalid_or_missing_report"

# ── Check 2: Report has findings array ──────────────────────────────────
check "python3 -c \"
import json
with open('review_report.json') as f:
    data = json.load(f)
assert 'findings' in data, 'Missing findings array'
assert isinstance(data['findings'], list), 'findings must be an array'
assert len(data['findings']) >= 8, f'Only {len(data[\"findings\"])} findings (need >= 8)'
print(f'FINDINGS_COUNT: {len(data[\"findings\"])}')
\"" "missing_or_insufficient_findings"

# ── Check 3: Critical issues identified ─────────────────────────────────
check "python3 -c \"
import json
with open('review_report.json') as f:
    report = json.load(f)
expected = json.load(open('$EXPECTED'))

findings = report.get('findings', [])
finding_ids = {f.get('id', '').upper() for f in findings}
finding_titles = ' '.join(f.get('title', '').lower() for f in findings)
finding_cats = ' '.join(f.get('category', '').lower() for f in findings)
all_text = ' '.join([str(f) for f in findings]).lower()

# Check critical issues are present
critical_ids = [i['id'] for i in expected['real_issues'] if i['severity'] == 'critical']
found_critical = 0
for cid in critical_ids:
    cid_lower = cid.lower().replace('_', ' ')
    cid_parts = cid.lower().split('_')
    if cid.upper() in finding_ids or any(part in all_text for part in cid_parts if len(part) > 3):
        found_critical += 1

assert found_critical >= 1, f'Only {found_critical}/{len(critical_ids)} critical issues found'
print(f'CRITICAL_FOUND: {found_critical}/{len(critical_ids)}')
\"" "critical_issues_missed"

# ── Check 4: Major issues identified ────────────────────────────────────
check "python3 -c \"
import json
with open('review_report.json') as f:
    report = json.load(f)
expected = json.load(open('$EXPECTED'))

findings = report.get('findings', [])
all_text = ' '.join([str(f) for f in findings]).lower()

major_ids = [i['id'] for i in expected['real_issues'] if i['severity'] == 'major']
found_major = 0
for mid in major_ids:
    mid_parts = mid.lower().split('_')
    if any(part in all_text for part in mid_parts if len(part) > 3):
        found_major += 1

assert found_major >= 2, f'Only {found_major}/{len(major_ids)} major issues found'
print(f'MAJOR_FOUND: {found_major}/{len(major_ids)}')
\"" "major_issues_missed"

# ── Check 5: Minor issues identified ───────────────────────────────────
check "python3 -c \"
import json
with open('review_report.json') as f:
    report = json.load(f)
expected = json.load(open('$EXPECTED'))

findings = report.get('findings', [])
all_text = ' '.join([str(f) for f in findings]).lower()

minor_ids = [i['id'] for i in expected['real_issues'] if i['severity'] == 'minor']
found_minor = 0
for mid in minor_ids:
    mid_parts = mid.lower().split('_')
    if any(part in all_text for part in mid_parts if len(part) > 3):
        found_minor += 1

assert found_minor >= 1, f'Only {found_minor}/{len(minor_ids)} minor issues found'
print(f'MINOR_FOUND: {found_minor}/{len(minor_ids)}')
\"" "minor_issues_missed"

# ── Check 6: False positives correctly handled ─────────────────────────
check "python3 -c \"
import json
with open('review_report.json') as f:
    report = json.load(f)
expected = json.load(open('$EXPECTED'))

findings = report.get('findings', [])

# Count findings marked as false_positive or similar
fp_marked = 0
for f in findings:
    sev = f.get('severity', '').lower()
    if 'false' in sev or 'fp' in sev or sev == 'none' or sev == 'informational':
        fp_marked += 1

# Also check summary if present
summary = report.get('summary', {})
fp_from_summary = summary.get('false_positives', 0)

total_fp = max(fp_marked, fp_from_summary)
assert total_fp >= 2, f'Only {total_fp} false positives identified (expected ~4)'
print(f'FALSE_POSITIVES_IDENTIFIED: {total_fp}')
\"" "false_positives_not_handled"

# ── Check 7: Severity levels are assigned ──────────────────────────────
check "python3 -c \"
import json
with open('review_report.json') as f:
    report = json.load(f)

findings = report.get('findings', [])
severities = set()
for f in findings:
    sev = f.get('severity', '')
    if sev:
        severities.add(sev.lower())

# Should have at least 2 different severity levels
assert len(severities) >= 2, f'Only {len(severities)} severity levels used: {severities}'
print(f'SEVERITY_LEVELS: {severities}')
\"" "no_severity_differentiation"

# ── Check 8: Report has summary section ────────────────────────────────
check "python3 -c \"
import json
with open('review_report.json') as f:
    report = json.load(f)

summary = report.get('summary', {})
assert summary, 'Missing summary section'
assert 'verdict' in summary or 'total_findings' in summary or 'critical' in summary, \
    f'Summary lacks required fields. Got: {list(summary.keys())}'
print(f'SUMMARY_OK: {list(summary.keys())}')
\"" "missing_summary"

# ── Check 9: Verdict is appropriate ────────────────────────────────────
check "python3 -c \"
import json
with open('review_report.json') as f:
    report = json.load(f)

summary = report.get('summary', {})
verdict = summary.get('verdict', '').lower()
# With 2 critical issues, verdict should NOT be 'approve'
assert verdict != 'approve', \
    f'Verdict is \"approve\" despite critical issues — should be reject or request_changes'
assert verdict in ['reject', 'request_changes', 'request changes', 'changes_requested'], \
    f'Verdict \"{verdict}\" unexpected with critical issues present'
print(f'VERDICT_OK: {verdict}')
\"" "wrong_verdict"

# ── Check 10: No extra false findings beyond expected ───────────────────
check "python3 -c \"
import json
with open('review_report.json') as f:
    report = json.load(f)

findings = report.get('findings', [])
# Total findings should be reasonable (not wildly over 12)
assert len(findings) <= 20, f'Too many findings: {len(findings)} (expected ~12, max 20)'
print(f'PRECISION_OK: {len(findings)} findings')
\"" "too_many_false_findings"

# ── Check 11: Attestation ──────────────────────────────────────────────
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
