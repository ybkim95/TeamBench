#!/usr/bin/env bash
# Generic grader for generator-based tasks.
# Delegates to workspace/check_solution.py which writes reports/score.json.
#
# Called as: grade.sh WORKSPACE REPORTS SUBMISSION TASK_DIR [EXPECTED_JSON]
set -uo pipefail

WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
REPORTS="${2:-${REPORTS_DIR:-/reports}}"

if [ ! -f "${WORKSPACE}/check_solution.py" ]; then
    mkdir -p "${REPORTS}"
    cat > "${REPORTS}/score.json" <<EOF
{
  "pass": false,
  "primary": {"success": 0},
  "secondary": {"partial_score": 0.0, "checks_passed": 0, "checks_total": 0},
  "failure_modes": ["check_solution_missing"]
}
EOF
    exit 0
fi

cd "${WORKSPACE}"
python3 check_solution.py || true   # non-zero return is fine; score.json reflects result
