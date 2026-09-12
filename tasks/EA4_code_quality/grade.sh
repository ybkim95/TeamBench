#!/usr/bin/env bash
set -uo pipefail
WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
REPORTS="${2:-${REPORTS_DIR:-/reports}}"
SUBMISSION="${3:-/submission}"
TASK_DIR="${4:-/task}"
cd "$WORKSPACE"
# was: pip install (grade-time network fetch), replaced scripts/make_graders_hermetic.py
tb_require ruff pylint || true

ruff_output=$(ruff check app/ 2>&1 || true)
ruff_errors=$(echo "$ruff_output" | grep -c "error\|warning\|E[0-9]\|W[0-9]\|F[0-9]" || true)
pylint_output=$(pylint app/ 2>&1 || true)
pylint_score=$(echo "$pylint_output" | grep "Your code has been rated" | grep -oE "[0-9]+\.[0-9]+" | head -1 || echo "0")

pass=false
if [ "$ruff_errors" -eq 0 ] && python3 -c "import sys; sys.exit(0 if float('${pylint_score:-0}') >= 9.0 else 1)" 2>/dev/null; then
    pass=true
fi

partial=0
[ "$ruff_errors" -eq 0 ] && partial=$((partial + 1))
python3 -c "import sys; sys.exit(0 if float('${pylint_score:-0}') >= 9.0 else 1)" 2>/dev/null && partial=$((partial + 1))
partial_score=$(awk "BEGIN {printf \"%.1f\", $partial / 2}")

cat > "${REPORTS}/score.json" <<EOF
{"pass":$( [ "$pass" = "true" ] && echo "true" || echo "false" ),"secondary":{"partial_score":$partial_score,"ruff_errors":$ruff_errors,"pylint_score":"${pylint_score:-0}"},"failure_modes":[]}
EOF

# hermetic-by: scripts/make_graders_hermetic.py
