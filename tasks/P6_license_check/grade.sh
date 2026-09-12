#!/usr/bin/env bash
# Grader for P6: License Compatibility Check
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

# 1. requirements.txt exists
check "test -f requirements.txt" "missing_requirements"

# 2. compliance_report.txt exists
check "test -f compliance_report.txt" "missing_report"

# 3. No GPL dependencies remain
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
with open('requirements.txt') as f:
    content = f.read().lower()
for gpl_pkg in expected['gpl_packages']:
    assert gpl_pkg.lower() not in content.split('#')[0] if '#' in content else gpl_pkg.lower() not in content, f'GPL package {gpl_pkg} still in requirements.txt'
    # Check line by line for the package name before any comment
    with open('requirements.txt') as f2:
        for line in f2:
            pkg_part = line.split('#')[0].strip().lower()
            assert gpl_pkg.lower() not in pkg_part, f'GPL package {gpl_pkg} still present: {line.strip()}'
\"" "gpl_deps_remain"

# 4. Replacement packages present
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
with open('requirements.txt') as f:
    content = f.read().lower()
for replacement in expected['replacement_packages']:
    found = False
    with open('requirements.txt') as f2:
        for line in f2:
            pkg_part = line.split('#')[0].strip().lower()
            if replacement.lower() in pkg_part:
                found = True
                break
    assert found, f'Replacement package {replacement} not found in requirements.txt'
\"" "replacements_missing"

# 5. Compatible deps unchanged
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
with open('requirements.txt') as f:
    lines = [l.split('#')[0].strip().lower() for l in f if l.strip() and not l.strip().startswith('#')]
for keep_pkg in expected['keep_packages']:
    found = any(keep_pkg.lower() in l for l in lines)
    assert found, f'Compatible package {keep_pkg} was incorrectly removed'
\"" "compatible_deps_removed"

# 6. Report mentions incompatible packages
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
with open('compliance_report.txt') as f:
    content = f.read().lower()
for gpl_pkg in expected['gpl_packages']:
    assert gpl_pkg.lower() in content, f'Report does not mention {gpl_pkg}'
\"" "report_incomplete"

# Attestation
# ── Attestation recorded as METADATA, never scored ───────────────────────
# de-scored-by: scripts/repair_graders.py (R3 attestation-is-protocol)
# attestation.json is a PROTOCOL property of the run (already enforced as a
# hard gate in harness/grade_task.py), not a property of the submitted
# artifact. Scoring it let an agent buy partial credit by writing one JSON
# file, which is the confound behind the withdrawn "removing the Verifier
# improves partial score" result. Recorded here, excluded from partial_score.
echo "metadata: attestation_present=$([ -f "${SUBMISSION:-}/attestation.json" ] && echo yes || echo no)"

PARTIAL=$(python3 -c "print(round($PASSED/max(1,$CHECKS), 2))")
if [ "$PASSED" -eq "$CHECKS" ]; then
    PASS=true
else
    PASS=false
fi
FM=$(python3 -c "import json; print(json.dumps([x for x in '${FAILURES}'.split(',') if x]))")

cat > "$REPORTS/score.json" <<JSON
{
  "pass": $PASS,
  "primary": {"success": $([ "$PASS" = "true" ] && echo 1 || echo 0)},
  "secondary": {
    "checks_passed": $PASSED,
    "checks_total": $CHECKS,
    "partial_score": $PARTIAL
  },
  "failure_modes": $FM
}
JSON
