#!/usr/bin/env bash
# CRYPTO5 grader: verify 3 TLS issues fixed + 2 intentional configs preserved
set -uo pipefail

WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
REPORTS="${2:-${REPORTS_DIR:-/reports}}"
SUBMISSION="${3:-/submission}"
TASK_DIR="${4:-/task}"

source /usr/local/lib/venv/bin/activate 2>/dev/null || true

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

cd "${WORKSPACE}"

# Install dependencies if needed
# was: pip install (grade-time network fetch), replaced scripts/make_graders_hermetic.py
tb_require pytest || true

# -------------------------------------------------------------------
# C1: All Python files parse without SyntaxError
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys, glob
for f in glob.glob('**/*.py', recursive=True):
    try:
        ast.parse(open(f).read())
    except SyntaxError as e:
        print(f'SyntaxError in {f}: {e}', file=sys.stderr)
        sys.exit(1)
sys.exit(0)
PYEOF
then
    check "C1" "All Python files have valid syntax" "pass"
else
    check "C1" "Syntax error in one or more Python files" "fail"
fi

# -------------------------------------------------------------------
# C2: pytest tests/ passes overall
# -------------------------------------------------------------------
if python3 -m pytest tests/ -q --tb=short 2>&1 | tail -5 | grep -qE "passed|no tests"; then
    check "C2" "All pytest tests pass" "pass"
else
    check "C2" "Some pytest tests still failing" "fail"
fi

# -------------------------------------------------------------------
# C3-C10: Inline Python checks
# -------------------------------------------------------------------
(python3 - <<'PYEOF'
import json, sys, os, re

os.chdir(os.environ.get("WORKSPACE_DIR", os.getcwd()))
sys.path.insert(0, ".")

results = {}

try:
    # Load expected.json
    reports_dir = os.environ.get("REPORTS_DIR", "/reports")
    expected_path = os.path.join(reports_dir, "expected.json")
    if os.path.exists(expected_path):
        with open(expected_path) as f:
            expected = json.load(f)
    else:
        expected = {}

    fix_issues = expected.get("fix_issues", [])
    preserve_issues = expected.get("preserve_issues", [])

    # Read the TLS config source
    config_file = expected.get("config_file", "server/tls_config.py")
    if os.path.exists(config_file):
        config_src = open(config_file).read()
    else:
        config_src = ""
        for f in ["tls_config.py", "server/tls_config.py", "config/tls.py"]:
            if os.path.exists(f):
                config_src = open(f).read()
                break

    # C3: RC4 cipher removed (fix issue)
    has_rc4 = bool(re.search(r'RC4|rc4', config_src))
    results["C3"] = not has_rc4

    # C4: Self-signed cert replaced or proper cert loading
    # Check that cert generation uses CA-signed or proper validation
    has_self_signed_gen = bool(re.search(r'self_signed|generate_self_signed|selfsigned', config_src, re.I))
    has_proper_cert = bool(re.search(r'load_cert|cert_file|certfile|CERT_PATH|ca_cert|CA_BUNDLE', config_src, re.I))
    results["C4"] = (not has_self_signed_gen) or has_proper_cert

    # C5: OCSP stapling enabled
    has_ocsp = bool(re.search(r'ocsp|OCSP|stapling', config_src, re.I))
    results["C5"] = has_ocsp

    # C6: Preserved — check that TLS 1.0 is still enabled (intentional)
    # Look for TLSv1 or PROTOCOL_TLSv1 or minimum_version not excluding 1.0
    preserve_tls10 = "tls_1_0" in preserve_issues or "tls10" in [p.replace("_","") for p in preserve_issues]
    if preserve_tls10:
        has_tls10 = bool(re.search(r'TLSv1[^._23]|PROTOCOL_TLS|TLS_1_0|tls_1_0|minimum_version.*TLSv1[^23]', config_src, re.I))
        # Also check it wasn't explicitly disabled
        tls10_disabled = bool(re.search(r'OP_NO_TLSv1[^_23]|disable.*tls.*1\.0|minimum_version.*TLSv1_2', config_src, re.I))
        results["C6"] = has_tls10 or not tls10_disabled
    else:
        results["C6"] = True

    # C7: Preserved — check that session timeout is still short (intentional)
    preserve_timeout = "session_timeout" in preserve_issues or "short_timeout" in preserve_issues
    if preserve_timeout:
        timeout_match = re.search(r'session_timeout\s*=\s*(\d+)|timeout\s*=\s*(\d+)', config_src)
        if timeout_match:
            val = int(timeout_match.group(1) or timeout_match.group(2))
            results["C7"] = val <= 120  # Short timeout preserved
        else:
            results["C7"] = True  # If no timeout found, it wasn't changed
    else:
        results["C7"] = True

    # C8: No weak ciphers remain (other than intentional preserves)
    weak_ciphers = re.findall(r'(DES|3DES|RC4|RC2|MD5|NULL|EXPORT|aNULL|eNULL)', config_src, re.I)
    # Filter out comments
    code_lines = [l for l in config_src.splitlines() if not l.strip().startswith('#')]
    code_only = "\n".join(code_lines)
    weak_in_code = re.findall(r'(DES|3DES|RC4|RC2|NULL|EXPORT|aNULL|eNULL)', code_only, re.I)
    results["C8"] = len(weak_in_code) == 0

except Exception as e:
    for k in ["C3","C4","C5","C6","C7","C8"]:
        results[k] = False
    results["_error"] = str(e)

print(json.dumps(results))
PYEOF
) > /tmp/crypto5_results.json 2>/tmp/crypto5_err.txt || true

# Parse inline test results
if [ -f /tmp/crypto5_results.json ]; then
    for cid in C3 C4 C5 C6 C7 C8; do
        val=$(python3 -c "import json; d=json.load(open('/tmp/crypto5_results.json')); print('pass' if d.get('${cid}',False) else 'fail')" 2>/dev/null || echo "fail")
        case "$cid" in
            C3) check "C3" "RC4 weak cipher removed from config" "$val" ;;
            C4) check "C4" "Self-signed cert replaced with proper cert loading" "$val" ;;
            C5) check "C5" "OCSP stapling enabled" "$val" ;;
            C6) check "C6" "TLS 1.0 preserved for legacy clients (intentional)" "$val" ;;
            C7) check "C7" "Short session timeout preserved (intentional)" "$val" ;;
            C8) check "C8" "No weak ciphers remain in active config" "$val" ;;
        esac
    done
else
    for cid in C3 C4 C5 C6 C7 C8; do
        check "$cid" "Inline test harness failed to run" "fail"
    done
fi

# -------------------------------------------------------------------
# C9: Legacy client tests pass
# -------------------------------------------------------------------
if python3 -m pytest tests/test_legacy_compat.py -q --tb=short 2>&1 | tail -5 | grep -qE "passed|no tests"; then
    check "C9" "Legacy client compatibility tests pass" "pass"
else
    check "C9" "Legacy client compatibility tests failed" "fail"
fi

# -------------------------------------------------------------------
# C10: Security hardening tests pass
# -------------------------------------------------------------------
if python3 -m pytest tests/test_security.py -q --tb=short 2>&1 | tail -5 | grep -qE "passed|no tests"; then
    check "C10" "Security hardening tests pass" "pass"
else
    check "C10" "Security hardening tests failed" "fail"
fi

partial_score=$(python3 -c "print(round($partial / $total, 2))")
findings="${findings%,}"

mkdir -p "${REPORTS}"
cat > "${REPORTS}/score.json" <<EOF
{
  "pass": $( [ "$pass" = "true" ] && echo "true" || echo "false" ),
  "secondary": {
    "partial_score": $partial_score,
    "checks_passed": $partial,
    "checks_total": $total
  },
  "failure_modes": [],
  "checklist": [$findings]
}
EOF

# hermetic-by: scripts/make_graders_hermetic.py
