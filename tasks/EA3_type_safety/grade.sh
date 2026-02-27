#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
REPORTS="${2:-${REPORTS_DIR:-/reports}}"
SUBMISSION="${3:-/submission}"
TASK_DIR="${4:-/task}"

cd "$WORKSPACE"
pip install mypy 2>/dev/null || true

# Run mypy and count errors
mypy_output=$(python -m mypy app/ --ignore-missing-imports --strict 2>&1 || true)
error_count=$(echo "$mypy_output" | grep -c "error:" || echo "999")

pass=false
partial_score="0.0"

if [ "$error_count" -eq 0 ]; then
    pass=true
    partial_score="1.0"
elif [ "$error_count" -le 3 ]; then
    partial_score="0.7"
elif [ "$error_count" -le 7 ]; then
    partial_score="0.4"
fi

# Check type:ignore count — spec requires exactly 3 (one per dynamic pattern)
# Count type: ignore across all app/ files
ignore_count=$(grep -rh "type: ignore" "${WORKSPACE}/app/" 2>/dev/null | grep -c "type: ignore" || echo "0")

# Fail if agent cheated by adding excessive type:ignore comments
if [ "$ignore_count" -gt 3 ] && [ "$pass" = "true" ]; then
    pass=false
    partial_score="0.7"  # partial credit: mypy passes but too many suppressions
fi

cat > "${REPORTS}/score.json" <<EOF
{
  "pass": $( [ "$pass" = "true" ] && echo "true" || echo "false" ),
  "secondary": {
    "partial_score": $partial_score,
    "mypy_error_count": $error_count,
    "type_ignore_count": $ignore_count,
    "type_ignore_within_limit": $( [ "$ignore_count" -le 3 ] && echo "true" || echo "false" )
  },
  "failure_modes": []
}
EOF
