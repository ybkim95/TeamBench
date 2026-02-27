#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
REPORTS="${2:-${REPORTS_DIR:-/reports}}"
SUBMISSION="${3:-/submission}"
TASK_DIR="${4:-/task}"

cd "$WORKSPACE"

# Run coverage measurement
pip install pytest pytest-cov coverage 2>/dev/null || true
coverage_output=$(python -m pytest --cov=validator --cov-branch --cov-report=term 2>&1 || true)

# Extract branch coverage percentage
branch_pct=$(echo "$coverage_output" | grep -oE 'TOTAL.*[0-9]+%' | grep -oE '[0-9]+%' | tail -1 | tr -d '%' || echo "0")

pass=false
partial_score="0.0"

if [ -n "$branch_pct" ] && [ "$branch_pct" -ge 90 ] 2>/dev/null; then
    pass=true
    partial_score="1.0"
elif [ -n "$branch_pct" ] && [ "$branch_pct" -ge 70 ] 2>/dev/null; then
    partial_score="0.5"
fi

cat > "${REPORTS}/score.json" <<EOF
{
  "pass": $( [ "$pass" = "true" ] && echo "true" || echo "false" ),
  "secondary": {
    "partial_score": $partial_score,
    "branch_coverage_pct": ${branch_pct:-0}
  },
  "failure_modes": []
}
EOF
