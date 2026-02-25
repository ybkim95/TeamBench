#!/usr/bin/env bash
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

# Load seed-specific expected values from expected.json (written by generator)
EXPECTED_JSON="$REPORTS/expected.json"
if [ ! -f "$EXPECTED_JSON" ]; then
  EXPECTED_JSON="$TASK_DIR/expected.json"
fi

# Extract seed-specific counts and values from expected.json
# Fall back to original fixed-task values if no expected.json present
Q1_COUNT=$(python3 -c "import json; e=json.load(open('$EXPECTED_JSON')); print(e.get('q1_row_count',7))" 2>/dev/null || echo "7")
Q2_COUNT=$(python3 -c "import json; e=json.load(open('$EXPECTED_JSON')); print(e.get('q2_row_count',3))" 2>/dev/null || echo "3")
Q2_DEPTS=$(python3 -c "import json; e=json.load(open('$EXPECTED_JSON')); print(json.dumps(e.get('q2_over_budget_depts',['HR','Marketing','Sales'])))" 2>/dev/null || echo '["HR","Marketing","Sales"]')
Q3_COUNT=$(python3 -c "import json; e=json.load(open('$EXPECTED_JSON')); print(e.get('q3_row_count',4))" 2>/dev/null || echo "4")
Q3_PROJECTS=$(python3 -c "import json; e=json.load(open('$EXPECTED_JSON')); print(json.dumps(e.get('q3_overdue_project_names',[])))" 2>/dev/null || echo '[]')
Q4_COUNT=$(python3 -c "import json; e=json.load(open('$EXPECTED_JSON')); print(e.get('q4_row_count',4))" 2>/dev/null || echo "4")
Q4_MANAGERS=$(python3 -c "import json; e=json.load(open('$EXPECTED_JSON')); print(json.dumps(e.get('q4_manager_map',{})))" 2>/dev/null || echo '{}')
Q5_COUNT=$(python3 -c "import json; e=json.load(open('$EXPECTED_JSON')); print(e.get('q5_row_count',5))" 2>/dev/null || echo "5")
Q5_FIRST=$(python3 -c "import json; e=json.load(open('$EXPECTED_JSON')); print(e.get('q5_first_dept','Engineering'))" 2>/dev/null || echo "Engineering")
Q5_COUNTS=$(python3 -c "import json; e=json.load(open('$EXPECTED_JSON')); print(json.dumps(e.get('q5_dept_counts',{})))" 2>/dev/null || echo '{}')

# Recreate DB from setup_db.py (ensures clean state)
check "python3 setup_db.py" "setup_db_crash"

# Run main.py -- exits 0 only when all 5 queries pass
check "python3 main.py" "main_crash_or_query_fail"

# Query 1: get_high_salary_employees returns correct row count
check "python3 -c \"
import sqlite3, sys
sys.path.insert(0, '.')
from queries import get_high_salary_employees
db = sqlite3.connect('company.db')
rows = get_high_salary_employees(db)
db.close()
expected = int(sys.argv[1])
assert len(rows) == expected, f'Expected {expected} rows, got {len(rows)}'
print('Q1_ROW_COUNT_OK')
\" '$Q1_COUNT'" "q1_wrong_row_count"

# Query 1: must use per-department avg (not global avg)
check "python3 -c \"
import sqlite3, sys
sys.path.insert(0, '.')
from queries import get_high_salary_employees
db = sqlite3.connect('company.db')
rows = get_high_salary_employees(db)
db.close()
# Verify by recomputing per-dept avg from DB
conn2 = sqlite3.connect('company.db')
cur = conn2.cursor()
cur.execute('SELECT department, AVG(salary) FROM employees GROUP BY department')
dept_avg = dict(cur.fetchall())
conn2.close()
# Every returned employee must be strictly above their dept avg
for r in rows:
    avg = dept_avg.get(r['department'], 0)
    assert r['salary'] > avg, f'{r[\"name\"]} salary {r[\"salary\"]} not above dept avg {avg}'
# No employee below dept avg should appear
cur3 = sqlite3.connect('company.db').cursor()
cur3.execute('SELECT name, department, salary FROM employees')
all_emps = cur3.fetchall()
result_names = {r['name'] for r in rows}
for name, dept, sal in all_emps:
    avg = dept_avg.get(dept, 0)
    if sal <= avg:
        assert name not in result_names, f'{name} (sal={sal}, avg={avg}) should not appear'
print('Q1_CORRECTNESS_OK')
\"" "q1_uses_global_avg"

# Query 2: get_over_budget_departments returns correct depts
check "python3 -c \"
import sqlite3, sys, json
sys.path.insert(0, '.')
from queries import get_over_budget_departments
db = sqlite3.connect('company.db')
rows = get_over_budget_departments(db)
db.close()
expected_count = int(sys.argv[1])
expected_depts = set(json.loads(sys.argv[2]))
assert len(rows) == expected_count, f'Expected {expected_count} rows, got {len(rows)}'
actual_depts = {r['name'] for r in rows}
assert actual_depts == expected_depts, f'Wrong depts: {actual_depts} vs {expected_depts}'
print('Q2_OK')
\" '$Q2_COUNT' '$Q2_DEPTS'" "q2_wrong_departments"

# Query 3: get_overdue_projects returns correct count
check "python3 -c \"
import sqlite3, sys, json
sys.path.insert(0, '.')
from queries import get_overdue_projects
db = sqlite3.connect('company.db')
rows = get_overdue_projects(db)
db.close()
expected_count = int(sys.argv[1])
expected_names = set(json.loads(sys.argv[2]))
assert len(rows) == expected_count, f'Expected {expected_count} rows, got {len(rows)}'
actual_names = {r['name'] for r in rows}
if expected_names:
    assert actual_names == expected_names, f'Wrong projects: {actual_names} vs {expected_names}'
print('Q3_OK')
\" '$Q3_COUNT' '$Q3_PROJECTS'" "q3_wrong_overdue_projects"

# Query 4: get_department_managers returns correct manager names
check "python3 -c \"
import sqlite3, sys, json
sys.path.insert(0, '.')
from queries import get_department_managers
db = sqlite3.connect('company.db')
rows = get_department_managers(db)
db.close()
expected_count = int(sys.argv[1])
expected_mgrs = json.loads(sys.argv[2])
assert len(rows) == expected_count, f'Expected {expected_count} rows, got {len(rows)}'
actual_mgrs = {r['department']: r['manager_name'] for r in rows}
for dept, mgr in expected_mgrs.items():
    assert actual_mgrs.get(dept) == mgr, f'{dept} mgr: expected {mgr!r}, got {actual_mgrs.get(dept)!r}'
print('Q4_OK')
\" '$Q4_COUNT' '$Q4_MANAGERS'" "q4_wrong_manager_names"

# Query 5: get_employee_count_by_dept returns all depts including zero-count
check "python3 -c \"
import sqlite3, sys, json
sys.path.insert(0, '.')
from queries import get_employee_count_by_dept
db = sqlite3.connect('company.db')
rows = get_employee_count_by_dept(db)
db.close()
expected_count = int(sys.argv[1])
first_dept = sys.argv[2]
dept_counts = json.loads(sys.argv[3])
assert len(rows) == expected_count, f'Expected {expected_count} rows (including zero-count dept), got {len(rows)}'
count_map = {r['department']: r['emp_count'] for r in rows}
for dept, cnt in dept_counts.items():
    assert count_map.get(dept) == cnt, f'{dept} count: expected {cnt}, got {count_map.get(dept)}'
assert rows[0]['department'] == first_dept, f'First row should be {first_dept!r}, got {rows[0][\"department\"]!r}'
print('Q5_OK')
\" '$Q5_COUNT' '$Q5_FIRST' '$Q5_COUNTS'" "q5_wrong_count_or_order"

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
