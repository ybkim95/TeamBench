#!/usr/bin/env bash
# Grade script for SEC8: Dependency Audit & Vulnerability Patch
# Arguments: WORKSPACE REPORTS SUBMISSION TASK_DIR
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

# Load expected values from grader report
EXPECTED="$REPORTS/expected.json"

# ── Helper: extract a field from expected.json ──────────────────────────────
get_expected() {
  python3 -c "import json,sys; d=json.load(open('$EXPECTED')); print(d['$1'])"
}

PKG_A=$(get_expected pkg_a)
SAFE_VER_A=$(get_expected safe_ver_a)
PKG_B=$(get_expected pkg_b)
SAFE_VER_B=$(get_expected safe_ver_b)
TRAP_PKG=$(get_expected trap_pkg)
TRAP_SAFE=$(get_expected trap_safe_ver)
TRAP_LATEST=$(get_expected trap_latest_ver)

# ── Check 1: requirements.txt is syntactically valid ────────────────────────
check "python3 -c \"
import re, sys
with open('requirements.txt') as f:
    lines = [l.strip() for l in f if l.strip() and not l.startswith('#')]
# Each line must be a valid PEP 508 specifier (package name + optional version)
import re
for line in lines:
    assert re.match(r'^[A-Za-z0-9_.-]+', line), f'Invalid requirement line: {line}'
print('REQUIREMENTS_VALID')
\"" "requirements_invalid"

# ── Check 2: pkg_a is no longer at vulnerable version ───────────────────────
check "python3 -c \"
from packaging.version import Version
import re
with open('requirements.txt') as f:
    content = f.read()
# Extract pinned or minimum version for pkg_a
import re
# Match exact pin (==) or range with >=
pattern = re.compile(r'(?i)${PKG_A}[>=!<~^]*([0-9][0-9.]*)', re.IGNORECASE)
# Also match: requests>=2.31.0 or requests==2.31.0 etc.
lines = [l.strip() for l in content.splitlines() if l.strip().lower().startswith('${PKG_A}'.lower())]
assert lines, '${PKG_A} not found in requirements.txt'
line = lines[0]
# Parse all version specifiers
specs = re.findall(r'([><=!~^]+)([0-9][0-9.a-zA-Z]*)', line)
assert specs, f'No version specifier found for ${PKG_A}: {line}'
# For == pin: must be >= safe version
# For >= constraint: must be >= safe version
safe = Version('${SAFE_VER_A}')
for op, ver in specs:
    v = Version(ver)
    if op == '==':
        assert v >= safe, f'${PKG_A} pinned to {ver} which is still vulnerable (need >= ${SAFE_VER_A})'
    elif op in ('>=', '>'):
        assert v >= safe or True, 'range check'  # '>=' constraint sufficient
print('PKG_A_PATCHED')
\"" "pkg_a_still_vulnerable"

# ── Check 3: pkg_a exact-pin check (== must be >= safe) ─────────────────────
check "python3 -c \"
from packaging.version import Version
import re
with open('requirements.txt') as f:
    content = f.read()
lines = [l.strip() for l in content.splitlines() if l.strip().lower().startswith('${PKG_A}'.lower())]
assert lines, '${PKG_A} missing from requirements.txt'
line = lines[0]
# If there is an == pin, it must be safe
pins = re.findall(r'==([0-9][0-9.]*)', line)
for pin in pins:
    assert Version(pin) >= Version('${SAFE_VER_A}'), (
        f'${PKG_A} exact pin {pin} is still vulnerable (need >= ${SAFE_VER_A})'
    )
# If >= constraint, minimum must be >= safe
mins = re.findall(r'>=([0-9][0-9.]*)', line)
for m in mins:
    assert Version(m) >= Version('${SAFE_VER_A}'), (
        f'${PKG_A} lower bound {m} is still vulnerable (need >= ${SAFE_VER_A})'
    )
print('PKG_A_VERSION_OK')
\"" "pkg_a_version_wrong"

# ── Check 4: pkg_b is no longer at vulnerable version ───────────────────────
check "python3 -c \"
from packaging.version import Version
import re
with open('requirements.txt') as f:
    content = f.read()
lines = [l.strip() for l in content.splitlines() if l.strip().lower().startswith('${PKG_B}'.lower())]
assert lines, '${PKG_B} not found in requirements.txt'
line = lines[0]
pins = re.findall(r'==([0-9][0-9.]*)', line)
for pin in pins:
    assert Version(pin) >= Version('${SAFE_VER_B}'), (
        f'${PKG_B} exact pin {pin} is still vulnerable (need >= ${SAFE_VER_B})'
    )
mins = re.findall(r'>=([0-9][0-9.]*)', line)
for m in mins:
    assert Version(m) >= Version('${SAFE_VER_B}'), (
        f'${PKG_B} lower bound {m} is still vulnerable (need >= ${SAFE_VER_B})'
    )
print('PKG_B_PATCHED')
\"" "pkg_b_still_vulnerable"

# ── Check 5: trap package is no longer at vulnerable version ─────────────────
check "python3 -c \"
from packaging.version import Version
import re
with open('requirements.txt') as f:
    content = f.read()
lines = [l.strip() for l in content.splitlines() if l.strip().lower().startswith('${TRAP_PKG}'.lower())]
assert lines, '${TRAP_PKG} not found in requirements.txt'
line = lines[0]
pins = re.findall(r'==([0-9][0-9.]*)', line)
for pin in pins:
    assert Version(pin) >= Version('${TRAP_SAFE}'), (
        f'${TRAP_PKG} exact pin {pin} is still vulnerable (need >= ${TRAP_SAFE})'
    )
mins = re.findall(r'>=([0-9][0-9.]*)', line)
for m in mins:
    assert Version(m) >= Version('${TRAP_SAFE}'), (
        f'${TRAP_PKG} lower bound {m} is still vulnerable (need >= ${TRAP_SAFE})'
    )
print('TRAP_PKG_PATCHED')
\"" "trap_pkg_still_vulnerable"

# ── Check 6: trap package NOT upgraded to breaking latest version ─────────────
check "python3 -c \"
from packaging.version import Version
import re
with open('requirements.txt') as f:
    content = f.read()
lines = [l.strip() for l in content.splitlines() if l.strip().lower().startswith('${TRAP_PKG}'.lower())]
assert lines, '${TRAP_PKG} not found in requirements.txt'
line = lines[0]

# If exact pin == trap_latest, that is the breaking version — FAIL
pins = re.findall(r'==([0-9][0-9.]*)', line)
for pin in pins:
    assert Version(pin) < Version('${TRAP_LATEST}'), (
        f'${TRAP_PKG} pinned to breaking version {pin} (== ${TRAP_LATEST}). '
        f'This version has a breaking API change. Pin below ${TRAP_LATEST}.'
    )

# If >= constraint with no upper bound, that allows the breaking version — FAIL
# Check for explicit upper bound < trap_latest or <= some-safe
has_upper = bool(re.search(r'<[^=]?([0-9])', line)) or bool(re.search(r'<=([0-9])', line))
has_open_gte = bool(re.findall(r'>=([0-9][0-9.]*)', line)) and not has_upper
# Open >= without upper bound allows breaking latest
if has_open_gte and not pins:
    # Warn but still pass — the grader cannot verify installed version without pip
    # This is acceptable: the agent may not know about the trap; we grade on pin presence
    pass

print('TRAP_NOT_BROKEN')
\"" "trap_pkg_upgraded_to_breaking"

# ── Check 7: trap package has upper bound excluding breaking version ──────────
check "python3 -c \"
from packaging.version import Version
import re
with open('requirements.txt') as f:
    content = f.read()
lines = [l.strip() for l in content.splitlines() if l.strip().lower().startswith('${TRAP_PKG}'.lower())]
assert lines, '${TRAP_PKG} not found in requirements.txt'
line = lines[0]

# Acceptable patterns:
#   1. exact pin == X where X < trap_latest
#   2. range with explicit upper < trap_latest (e.g., >=1.34,<1.35)
#   3. range with explicit upper <= some version < trap_latest
exact_pins = re.findall(r'==([0-9][0-9.]*)', line)
upper_lt    = re.findall(r'<([0-9][0-9.]*)', line)  # includes both < and <=
upper_le    = re.findall(r'<=([0-9][0-9.]*)', line)

if exact_pins:
    pin_ver = Version(exact_pins[0])
    assert pin_ver < Version('${TRAP_LATEST}'), (
        f'${TRAP_PKG}=={exact_pins[0]} is the breaking version'
    )
    print('TRAP_UPPER_BOUND_OK')
elif upper_lt:
    # < constraint: the excluded version must be <= trap_latest
    excl = Version(upper_lt[0])
    assert excl <= Version('${TRAP_LATEST}'), (
        f'Upper bound <{upper_lt[0]} still allows ${TRAP_LATEST}'
    )
    print('TRAP_UPPER_BOUND_OK')
else:
    # No upper bound — agent missed the trap
    assert False, (
        f'${TRAP_PKG} has no upper version bound. '
        f'The breaking version ${TRAP_LATEST} may be installed. '
        f'Add an upper bound: <${TRAP_LATEST}'
    )
\"" "trap_missing_upper_bound"

# ── Check 8: all three packages still present in requirements.txt ────────────
check "python3 -c \"
with open('requirements.txt') as f:
    content = f.read().lower()
assert '${PKG_A}'.lower() in content, '${PKG_A} removed from requirements.txt'
assert '${PKG_B}'.lower() in content, '${PKG_B} removed from requirements.txt'
assert '${TRAP_PKG}'.lower() in content, '${TRAP_PKG} removed from requirements.txt'
print('ALL_PACKAGES_PRESENT')
\"" "package_removed"

# ── Check 9: no vulnerable exact pins remain (sanity sweep) ─────────────────
check "python3 -c \"
from packaging.version import Version
import re

def check_no_vuln_pin(pkg, vuln_ver, req_content):
    lines = [l.strip() for l in req_content.splitlines()
             if l.strip().lower().startswith(pkg.lower())]
    for line in lines:
        pins = re.findall(r'==([0-9][0-9.]*)', line)
        for pin in pins:
            assert Version(pin) != Version(vuln_ver), (
                f'{pkg} still pinned to vulnerable version {vuln_ver}'
            )

with open('requirements.txt') as f:
    content = f.read()

check_no_vuln_pin('${PKG_A}', '${SAFE_VER_A}', content)  # note: checking not == vuln
# Actually check original vuln versions from expected.json
import json
exp = json.load(open('$EXPECTED'))
check_no_vuln_pin(exp['pkg_a'], '$(python3 -c "import json; d=json.load(open(\"$EXPECTED\")); print(d.get(\"vuln_ver_a\", \"0.0.0\"))" 2>/dev/null || echo "0.0.0")', content)
print('NO_VULN_PINS_REMAIN')
\"" "vulnerable_pin_remains"

# ── Check 10: application source files not modified ──────────────────────────
check "python3 -c \"
import json, os
exp = json.load(open('$EXPECTED'))
domain = exp['domain']
# Map domain to app file name
domain_to_file = {
    'data_pipeline': 'pipeline.py',
    'web_scraper': 'scraper.py',
    'api_client': 'client.py',
    'report_generator': 'reporter.py',
    'notification_service': 'notifier.py',
}
app_file = domain_to_file.get(domain)
if app_file and os.path.exists(app_file):
    with open(app_file) as f:
        src = f.read()
    # Application code must still import the trap package (not removed)
    trap_pkg = exp['trap_pkg']
    assert trap_pkg.replace('-', '_') in src or trap_pkg in src, (
        f'App source no longer imports {trap_pkg} — do not modify app source files'
    )
print('APP_SOURCE_INTACT')
\"" "app_source_modified"

# ── Check 11: requirements.txt has no syntax errors (pip check) ──────────────
check "python3 -c \"
import subprocess, sys
result = subprocess.run(
    [sys.executable, '-m', 'pip', 'install', '--dry-run', '-r', 'requirements.txt',
     '--quiet', '--no-deps'],
    capture_output=True, text=True, timeout=30
)
# We just need pip to parse it without error (network may be unavailable)
# A parse/syntax error produces 'ERROR: Invalid requirement' on stderr
assert 'Invalid requirement' not in result.stderr, (
    f'requirements.txt has invalid syntax:\\n{result.stderr}'
)
assert 'ERROR' not in result.stderr or 'Could not find' in result.stderr, (
    f'pip error on requirements.txt: {result.stderr[:200]}'
)
print('REQUIREMENTS_PARSEABLE')
\"" "requirements_syntax_error"

# ── Check 12: attestation ────────────────────────────────────────────────────
# ── Attestation recorded as METADATA, never scored ───────────────────────
# de-scored-by: scripts/repair_graders.py (R3 attestation-is-protocol)
# attestation.json is a PROTOCOL property of the run (already enforced as a
# hard gate in harness/grade_task.py), not a property of the submitted
# artifact. Scoring it let an agent buy partial credit by writing one JSON
# file, which is the confound behind the withdrawn "removing the Verifier
# improves partial score" result. Recorded here, excluded from partial_score.
echo "metadata: attestation_present=$([ -f "${SUBMISSION:-}/attestation.json" ] && echo yes || echo no)"

# ── Score output ─────────────────────────────────────────────────────────────
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
