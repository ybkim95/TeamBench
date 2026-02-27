#!/usr/bin/env bash
set -euo pipefail
WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
REPORTS="${2:-${REPORTS_DIR:-/reports}}"
SUBMISSION="${3:-/submission}"
TASK_DIR="${4:-/task}"
cd "$WORKSPACE"

pip install pip-audit pytest 2>/dev/null || true

pass=true
partial=0
total=7

check_pass() { partial=$((partial + 1)); }
check_fail() { pass=false; }

# Check requirements versions
check_dep() {
    local pkg="$1" safe_ver="$2"
    if grep -qi "^${pkg}>=" requirements.txt 2>/dev/null; then
        check_pass
    elif grep -qi "^${pkg}==" requirements.txt 2>/dev/null; then
        local ver=$(grep -i "^${pkg}==" requirements.txt | grep -oE "[0-9]+\.[0-9]+\.[0-9]+")
        if python3 -c "from packaging.version import Version; exit(0 if Version('$ver') >= Version('$safe_ver') else 1)" 2>/dev/null; then
            check_pass
        else
            check_fail
        fi
    else
        check_fail
    fi
}

check_dep "Werkzeug" "3.0.3"
check_dep "requests" "2.32.0"
check_dep "Pillow" "10.3.0"
check_dep "cryptography" "42.0.4"
check_dep "PyYAML" "6.0.1"

# Check Pillow API fix
if ! grep -q "ANTIALIAS" "${WORKSPACE}/app/image_processor.py" 2>/dev/null; then
    check_pass
else
    check_fail
fi

# Check cryptography API fix
if ! grep -q "default_backend()" "${WORKSPACE}/app/crypto_utils.py" 2>/dev/null; then
    check_pass
else
    check_fail
fi

partial_score=$(echo "scale=2; $partial / $total" | bc)
cat > "${REPORTS}/score.json" <<EOF
{"pass":$( [ "$pass" = "true" ] && echo "true" || echo "false" ),"secondary":{"partial_score":$partial_score,"checks_passed":$partial,"total_checks":$total},"failure_modes":[]}
EOF
