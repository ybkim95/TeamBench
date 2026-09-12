#!/usr/bin/env bash
# CRYPTO3 grader: verify 3 cert chain bugs fixed and 2 false positives preserved
set -uo pipefail

WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
REPORTS="${2:-${REPORTS_DIR:-/reports}}"
SUBMISSION="${3:-/submission}"
TASK_DIR="${4:-/task}"

cd "$WORKSPACE"

pass=true
partial=0
total=10
findings=""

check() {
    local id="$1"
    local desc="$2"
    local result="$3"
    if [ "$result" = "pass" ]; then
        partial=$((partial + 1))
        findings="${findings}{\"id\":\"${id}\",\"ok\":true,\"note\":\"${desc}\"},"
    else
        pass=false
        findings="${findings}{\"id\":\"${id}\",\"ok\":false,\"note\":\"${desc}\"},"
    fi
}

# Install dependencies if needed
# was: pip install (grade-time network fetch), replaced scripts/make_graders_hermetic.py
tb_require pytest cryptography || true

# -------------------------------------------------------------------
# C1: Overall pytest suite passes
# -------------------------------------------------------------------
if python -m pytest tests/ -q --tb=no 2>/dev/null | grep -q "passed"; then
    check "C1" "pytest tests/ passes" "pass"
else
    check "C1" "pytest tests/ has failures" "fail"
fi

# -------------------------------------------------------------------
# C2: test_expired.py passes (UTC-aware expiry check)
# -------------------------------------------------------------------
if python -m pytest tests/test_expired.py -q --tb=no 2>/dev/null | grep -q "passed"; then
    check "C2" "test_expired.py passes: UTC-aware expiry check works" "pass"
else
    check "C2" "test_expired.py fails: expired cert not properly rejected" "fail"
fi

# -------------------------------------------------------------------
# C3: test_issuer_match.py passes (Subject/Issuer chain check)
# -------------------------------------------------------------------
if python -m pytest tests/test_issuer_match.py -q --tb=no 2>/dev/null | grep -q "passed"; then
    check "C3" "test_issuer_match.py passes: Subject/Issuer name chain enforced" "pass"
else
    check "C3" "test_issuer_match.py fails: issuer mismatch not detected" "fail"
fi

# -------------------------------------------------------------------
# C4: test_path_length.py passes (pathLenConstraint enforced)
# -------------------------------------------------------------------
if python -m pytest tests/test_path_length.py -q --tb=no 2>/dev/null | grep -q "passed"; then
    check "C4" "test_path_length.py passes: pathLenConstraint enforced" "pass"
else
    check "C4" "test_path_length.py fails: pathLenConstraint not enforced" "fail"
fi

# -------------------------------------------------------------------
# C5: test_self_signed.py passes (self-signed root still accepted)
# -------------------------------------------------------------------
if python -m pytest tests/test_self_signed.py -q --tb=no 2>/dev/null | grep -q "passed"; then
    check "C5" "test_self_signed.py passes: self-signed root CA still accepted" "pass"
else
    check "C5" "test_self_signed.py fails: self-signed root acceptance broken" "fail"
fi

# -------------------------------------------------------------------
# C6: test_valid_chain.py passes (valid chain still validates)
# -------------------------------------------------------------------
if python -m pytest tests/test_valid_chain.py -q --tb=no 2>/dev/null | grep -q "passed"; then
    check "C6" "test_valid_chain.py passes: valid cert chain still validates" "pass"
else
    check "C6" "test_valid_chain.py fails: valid chain broken by changes" "fail"
fi

# -------------------------------------------------------------------
# C7: time_utils.py uses UTC time (utcnow or timezone.utc), not local datetime.now()
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys
src = open('certlib/time_utils.py').read()
# Must reference utcnow() or timezone.utc
has_utc = 'utcnow' in src or 'timezone.utc' in src or 'UTC' in src
# Must NOT use bare datetime.now() with no arguments (local time)
tree = ast.parse(src)
has_bare_now = False
for node in ast.walk(tree):
    if isinstance(node, ast.Call):
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr == 'now':
            # now() with no args = local time (bug); now(timezone.utc) = OK
            if len(node.args) == 0 and len(node.keywords) == 0:
                has_bare_now = True
if has_utc and not has_bare_now:
    sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C7" "time_utils.py uses UTC time (utcnow/timezone.utc), not local datetime.now()" "pass"
else
    check "C7" "time_utils.py still uses local datetime.now() instead of UTC" "fail"
fi

# -------------------------------------------------------------------
# C8: validator.py has issuer/subject name comparison
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys
src = open('certlib/validator.py').read()
# Must compare .issuer and .subject
has_issuer_check = '.issuer' in src and '.subject' in src
# Must have a comparison or inequality check between them
has_comparison = ('issuer !=' in src or 'issuer ==' in src or
                  'subject !=' in src or '!= issuer_cert.subject' in src or
                  '!= issuer.subject' in src or 'issuer != ' in src)
if has_issuer_check and has_comparison:
    sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C8" "validator.py has issuer/subject name comparison" "pass"
else
    check "C8" "validator.py missing issuer/subject name comparison" "fail"
fi

# -------------------------------------------------------------------
# C9: validator.py has pathLenConstraint check
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys
src = open('certlib/validator.py').read()
# Must reference path_length
has_path_len = 'path_length' in src
# Must have a comparison against depth or similar
has_depth_check = ('depth' in src and ('path_length' in src)) or 'path_len' in src.lower()
if has_path_len and has_depth_check:
    sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C9" "validator.py has pathLenConstraint depth check" "pass"
else
    check "C9" "validator.py missing pathLenConstraint check" "fail"
fi

# -------------------------------------------------------------------
# C10: Syntax validity of modified files
# -------------------------------------------------------------------
if python3 -c "
import py_compile, sys
files = ['certlib/validator.py', 'certlib/time_utils.py']
for f in files:
    try:
        py_compile.compile(f, doraise=True)
    except py_compile.PyCompileError as e:
        print(f'Syntax error in {f}: {e}')
        sys.exit(1)
sys.exit(0)
" 2>/dev/null; then
    check "C10" "certlib/validator.py and certlib/time_utils.py have valid syntax" "pass"
else
    check "C10" "Syntax error in certlib/validator.py or certlib/time_utils.py" "fail"
fi

# -------------------------------------------------------------------
# Run full pytest for informational counts
# -------------------------------------------------------------------
pytest_out=$(python -m pytest tests/ -q --tb=no 2>&1 || true)
pytest_pass=$(echo "$pytest_out" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' || echo "0")
pytest_fail=$(echo "$pytest_out" | grep -oE '[0-9]+ failed' | grep -oE '[0-9]+' || echo "0")

partial_score=$(awk "BEGIN {printf \"%.4f\", $partial / $total}")
findings="${findings%,}"  # Remove trailing comma

cat > "${REPORTS}/score.json" <<EOF
{
  "pass": $( [ "$pass" = "true" ] && echo "true" || echo "false" ),
  "secondary": {
    "partial_score": $partial_score,
    "checks_passed": $partial,
    "total_checks": $total,
    "pytest_passed": ${pytest_pass:-0},
    "pytest_failed": ${pytest_fail:-0}
  },
  "failure_modes": [],
  "checklist": [$findings]
}
EOF

# hermetic-by: scripts/make_graders_hermetic.py
