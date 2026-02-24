#!/usr/bin/env bash
set -euo pipefail
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

# Recreate DB from setup_db.py (ensures clean state)
check "python3 setup_db.py" "setup_db_crash"

# Run main.py -- exits 0 only when all 5 queries pass
check "python3 main.py" "main_crash_or_query_fail"

# Query 1: get_high_salary_employees returns 8 rows
check "python3 -c \"
import sqlite3, sys
sys.path.insert(0, '.')
from queries import get_high_salary_employees
db = sqlite3.connect('company.db')
rows = get_high_salary_employees(db)
db.close()
assert len(rows) == 7, f'Expected 7 rows, got {len(rows)}'
print('Q1_ROW_COUNT_OK')
\"" "q1_wrong_row_count"

# Query 1: must contain above-avg earners from each dept, not global avg
check "python3 -c \"
import sqlite3, sys
sys.path.insert(0, '.')
from queries import get_high_salary_employees
db = sqlite3.connect('company.db')
rows = get_high_salary_employees(db)
db.close()
names = {r['name'] for r in rows}
# Dave (110000) above Engineering avg (91200) -- must be present
assert 'Dave' in names, 'Dave missing (Engineering above-dept-avg)'
# Frank (58000) == Sales avg (58000) -- must NOT be present (not strictly above)
assert 'Frank' not in names, 'Frank should not appear (salary equals dept avg, not above)'
print('Q1_CORRECTNESS_OK')
\"" "q1_uses_global_avg"

# Query 2: get_over_budget_departments returns 3 rows
check "python3 -c \"
import sqlite3, sys
sys.path.insert(0, '.')
from queries import get_over_budget_departments
db = sqlite3.connect('company.db')
rows = get_over_budget_departments(db)
db.close()
assert len(rows) == 3, f'Expected 3 rows, got {len(rows)}'
depts = {r['name'] for r in rows}
assert depts == {'Marketing', 'Sales', 'HR'}, f'Wrong depts: {depts}'
print('Q2_OK')
\"" "q2_wrong_departments"

# Query 3: get_overdue_projects returns 4 rows
check "python3 -c \"
import sqlite3, sys
sys.path.insert(0, '.')
from queries import get_overdue_projects
db = sqlite3.connect('company.db')
rows = get_overdue_projects(db)
db.close()
assert len(rows) == 4, f'Expected 4 rows, got {len(rows)}'
names = {r['name'] for r in rows}
assert 'Sales Automation' in names, 'Sales Automation missing'
assert 'Brand Refresh' in names, 'Brand Refresh missing'
assert 'Recruit Pipeline' in names, 'Recruit Pipeline missing'
assert 'Data Warehouse' in names, 'Data Warehouse missing'
# Mobile App deadline is exactly 2025-01-01 -- not overdue
assert 'Mobile App' not in names, 'Mobile App should not be overdue (deadline == cutoff)'
print('Q3_OK')
\"" "q3_wrong_overdue_projects"

# Query 4: get_department_managers returns correct manager names
check "python3 -c \"
import sqlite3, sys
sys.path.insert(0, '.')
from queries import get_department_managers
db = sqlite3.connect('company.db')
rows = get_department_managers(db)
db.close()
assert len(rows) == 4, f'Expected 4 rows, got {len(rows)}'
mgr_map = {r['department']: r['manager_name'] for r in rows}
assert mgr_map.get('Engineering') == 'Dave',  f'Engineering mgr: {mgr_map.get(\"Engineering\")}'
assert mgr_map.get('Marketing')   == 'Carol', f'Marketing mgr: {mgr_map.get(\"Marketing\")}'
assert mgr_map.get('Sales')       == 'Grace', f'Sales mgr: {mgr_map.get(\"Sales\")}'
assert mgr_map.get('HR')          == 'Heidi', f'HR mgr: {mgr_map.get(\"HR\")}'
print('Q4_OK')
\"" "q4_wrong_manager_names"

# Query 5: get_employee_count_by_dept returns 5 rows including Executive(0)
check "python3 -c \"
import sqlite3, sys
sys.path.insert(0, '.')
from queries import get_employee_count_by_dept
db = sqlite3.connect('company.db')
rows = get_employee_count_by_dept(db)
db.close()
assert len(rows) == 5, f'Expected 5 rows (including Executive with 0), got {len(rows)}'
count_map = {r['department']: r['emp_count'] for r in rows}
assert count_map.get('Engineering') == 5, f'Engineering count: {count_map.get(\"Engineering\")}'
assert count_map.get('Marketing')   == 4, f'Marketing count: {count_map.get(\"Marketing\")}'
assert count_map.get('Sales')       == 3, f'Sales count: {count_map.get(\"Sales\")}'
assert count_map.get('HR')          == 3, f'HR count: {count_map.get(\"HR\")}'
assert count_map.get('Executive')   == 0, f'Executive count: {count_map.get(\"Executive\")}'
# First row must be Engineering (highest count)
assert rows[0]['department'] == 'Engineering', f'First row should be Engineering, got {rows[0][\"department\"]}'
print('Q5_OK')
\"" "q5_wrong_count_or_order"

# Attestation check
check "python3 -c \"
import json, sys
att = json.load(open(sys.argv[1]))
assert att.get('verdict') == 'pass', f'verdict={att.get(\"verdict\")}'
\" '$SUBMISSION/attestation.json'" "bad_attestation"

# Write score with partial scoring
PARTIAL=$(python3 -c "print(round($PASSED/max(1,$CHECKS), 2))")
if [ "$PASSED" -eq "$CHECKS" ]; then
    SUCCESS=1; PASS=true
else
    SUCCESS=0; PASS=false
fi
FM=$(python3 -c "import json; print(json.dumps([x for x in '${FAILURES}'.split(',') if x]))")

cat > "$REPORTS/score.json" <<JSON
{
  "pass": $PASS,
  "primary": {"success": $SUCCESS},
  "secondary": {
    "checks_passed": $PASSED,
    "checks_total": $CHECKS,
    "partial_score": $PARTIAL
  },
  "failure_modes": $FM
}
JSON
