#!/usr/bin/env bash
set -euo pipefail
WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
REPORTS="${2:-${REPORTS_DIR:-/reports}}"
SUBMISSION="${3:-/submission}"
TASK_DIR="${4:-/task}"
cd "$WORKSPACE"
pip install ruff pylint 2>/dev/null || true

ruff_errors=$(ruff check app/ 2>&1 | grep -c "error\|warning\|E[0-9]\|W[0-9]\|F[0-9]" || echo "0")
pylint_score=$(pylint app/ 2>&1 | grep "Your code has been rated" | grep -oE "[0-9]+\.[0-9]+" | head -1 || echo "0")

pass=false
if [ "$ruff_errors" -eq 0 ] && python3 -c "import sys; sys.exit(0 if float('${pylint_score:-0}') >= 9.0 else 1)" 2>/dev/null; then
    pass=true
fi

partial=0
[ "$ruff_errors" -eq 0 ] && partial=$((partial + 1))
python3 -c "import sys; sys.exit(0 if float('${pylint_score:-0}') >= 9.0 else 1)" 2>/dev/null && partial=$((partial + 1))
partial_score=$(echo "scale=1; $partial / 2" | bc)

cat > "${REPORTS}/score.json" <<EOF
{"pass":$( [ "$pass" = "true" ] && echo "true" || echo "false" ),"secondary":{"partial_score":$partial_score,"ruff_errors":$ruff_errors,"pylint_score":"${pylint_score:-0}"},"failure_modes":[]}
EOF
