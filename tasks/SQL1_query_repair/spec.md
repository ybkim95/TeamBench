# SQL1: Query Repair (Planner Specification)

## Database Schema

The app uses SQLite (`company.db`) with three tables:

```sql
CREATE TABLE employees (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    department  TEXT NOT NULL,
    salary      REAL NOT NULL,
    hire_date   TEXT NOT NULL   -- stored as ISO-8601: 'YYYY-MM-DD'
);

CREATE TABLE departments (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    budget      REAL NOT NULL,
    manager_id  INTEGER         -- FK -> employees.id
);

CREATE TABLE projects (
    id            INTEGER PRIMARY KEY,
    name          TEXT NOT NULL,
    department_id INTEGER NOT NULL,  -- FK -> departments.id
    deadline      TEXT NOT NULL,     -- stored as ISO-8601: 'YYYY-MM-DD'
    status        TEXT NOT NULL      -- 'active' | 'completed' | 'cancelled'
);
```

## Test Data Summary

**employees** (15 rows):

| id | name        | department   | salary   | hire_date  |
|----|-------------|--------------|----------|------------|
| 1  | Alice       | Engineering  | 95000    | 2019-03-15 |
| 2  | Bob         | Engineering  | 72000    | 2020-07-01 |
| 3  | Carol       | Marketing    | 68000    | 2018-11-20 |
| 4  | Dave        | Engineering  | 110000   | 2017-05-10 |
| 5  | Eve         | Marketing    | 75000    | 2021-02-28 |
| 6  | Frank       | Sales        | 58000    | 2022-01-15 |
| 7  | Grace       | Sales        | 62000    | 2021-09-03 |
| 8  | Heidi       | HR           | 70000    | 2019-06-22 |
| 9  | Ivan        | HR           | 66000    | 2020-04-11 |
| 10 | Judy        | Engineering  | 88000    | 2018-08-30 |
| 11 | Karl        | Marketing    | 71000    | 2023-03-01 |
| 12 | Liam        | Sales        | 54000    | 2022-11-14 |
| 13 | Mia         | HR           | 73000    | 2021-07-19 |
| 14 | Noah        | Engineering  | 91000    | 2016-12-05 |
| 15 | Olivia      | Marketing    | 65000    | 2023-06-30 |

**departments** (5 rows):

| id | name        | budget    | manager_id |
|----|-------------|-----------|------------|
| 1  | Engineering | 500000    | 4          |
| 2  | Marketing   | 200000    | 3          |
| 3  | Sales       | 150000    | 7          |
| 4  | HR          | 180000    | 8          |
| 5  | Executive   | 300000    | NULL       |

**projects** (8 rows):

| id | name                  | department_id | deadline   | status    |
|----|-----------------------|---------------|------------|-----------|
| 1  | Platform Rewrite      | 1             | 2023-06-01 | completed |
| 2  | Q4 Campaign           | 2             | 2024-01-15 | completed |
| 3  | Sales Automation      | 3             | 2024-03-01 | active    |
| 4  | HR Portal             | 4             | 2023-12-31 | completed |
| 5  | Mobile App            | 1             | 2025-01-01 | active    |
| 6  | Brand Refresh         | 2             | 2024-09-01 | active    |
| 7  | Recruit Pipeline      | 4             | 2024-06-15 | active    |
| 8  | Data Warehouse        | 1             | 2024-11-30 | active    |

## The 5 Broken Queries and Their Correct Forms

### Query 1: `get_high_salary_employees(db)`

**Intent:** Return each employee whose salary exceeds the average salary of their department.

**Bug:** The current query uses a subquery that computes a single global average (no correlated filter), so it compares every employee against the company-wide average instead of their department's average.

**Broken SQL:**
```sql
SELECT e.id, e.name, e.department, e.salary
FROM employees e
WHERE e.salary > (SELECT AVG(salary) FROM employees)
ORDER BY e.department, e.salary DESC
```

**Correct SQL:**
```sql
SELECT e.id, e.name, e.department, e.salary
FROM employees e
WHERE e.salary > (
    SELECT AVG(e2.salary)
    FROM employees e2
    WHERE e2.department = e.department
)
ORDER BY e.department, e.salary DESC
```

**Expected results:** 6 rows.
- Engineering: avg = (95000+72000+110000+88000+91000)/5 = 456000/5 = 91200. Strictly above avg: Dave (110000), Alice (95000) = 2 rows. (Noah=91000 equals avg, not above.)
- Marketing: avg = (68000+75000+71000+65000)/4 = 279000/4 = 69750. Above avg: Eve (75000), Karl (71000) = 2 rows.
- Sales: avg = (58000+62000+54000)/3 = 174000/3 = 58000. Above avg: Grace (62000) = 1 row. (Frank=58000 equals avg, not above.)
- HR: avg = (70000+66000+73000)/3 = 209000/3 ≈ 69667. Above avg: Mia (73000), Heidi (70000) = 2 rows.

**Expected row count: 7**

### Query 2: `get_over_budget_departments(db)`

**Intent:** Return departments where the total salary of their employees exceeds the department's budget.

**Bug:** The JOIN between `employees` and `departments` uses `employees.department = departments.name` (string match on the name column), but additionally the budget comparison compares total salary against budget. This actually works for the join, BUT the bug is that the query joins `employees.department` (a text column storing the department name as a string like "Engineering") against `departments.name`. This is the intended join since there's no `department_id` in `employees`. The real bug is the HAVING clause uses `SUM(e.salary) > d.budget` but the query accidentally does `GROUP BY d.name` when it should `GROUP BY d.id, d.name, d.budget` — causing wrong budget values when names could collide, and more critically the query has `JOIN departments d ON e.department = d.id` (joining text to integer id) instead of `ON e.department = d.name`.

**Broken SQL:**
```sql
SELECT d.name, d.budget, SUM(e.salary) AS total_salary
FROM employees e
JOIN departments d ON e.department = d.id
GROUP BY d.name
HAVING SUM(e.salary) > d.budget
ORDER BY d.name
```

**Correct SQL:**
```sql
SELECT d.name, d.budget, SUM(e.salary) AS total_salary
FROM employees e
JOIN departments d ON e.department = d.name
GROUP BY d.id, d.name, d.budget
HAVING SUM(e.salary) > d.budget
ORDER BY d.name
```

**Expected results:**
- Engineering: budget=500000, total salary = 95000+72000+110000+88000+91000 = 456000. Not over budget.
- Marketing: budget=200000, total = 68000+75000+71000+65000 = 279000. OVER.
- Sales: budget=150000, total = 58000+62000+54000 = 174000. OVER.
- HR: budget=180000, total = 70000+66000+73000 = 209000. OVER.

**Expected row count: 3** (Marketing, Sales, HR)

### Query 3: `get_overdue_projects(db)`

**Intent:** Return active projects whose deadline has passed (deadline < today). For grading, "today" is fixed to `'2025-01-01'` so results are deterministic.

**Bug:** The query compares the ISO date string using `strftime('%s', deadline) < strftime('%s', 'now')` (Unix timestamp conversion). While this would work in many SQLite builds, the bug introduced is that the query uses `deadline < date('now', 'localtime')` but with the wrong format string causing a constant wrong date, specifically the query uses a hardcoded wrong reference date in a format that SQLite cannot parse:

Actually the specific bug is simpler: the query uses `CAST(strftime('%Y%m%d', deadline) AS INTEGER) < CAST(strftime('%Y%m%d', 'now') AS INTEGER)` which strips the dashes and works, BUT in the broken version it uses `deadline < strftime('%s', 'now')` — comparing an ISO string ('2024-03-01') against a Unix timestamp integer string ('1735689600'), which in SQLite string comparison makes '2024-03-01' > '1735...' (since '2' > '1'), so NO projects appear overdue.

**Broken SQL:**
```sql
SELECT p.id, p.name, p.deadline, d.name AS department
FROM projects p
JOIN departments d ON p.department_id = d.id
WHERE p.status = 'active'
  AND p.deadline < strftime('%s', 'now')
ORDER BY p.deadline
```

**Correct SQL:**
```sql
SELECT p.id, p.name, p.deadline, d.name AS department
FROM projects p
JOIN departments d ON p.department_id = d.id
WHERE p.status = 'active'
  AND p.deadline < '2025-01-01'
ORDER BY p.deadline
```

**Expected results** (active projects with deadline < 2025-01-01):
- Project 3: Sales Automation, deadline 2024-03-01, Sales — OVERDUE
- Project 6: Brand Refresh, deadline 2024-09-01, Marketing — OVERDUE
- Project 7: Recruit Pipeline, deadline 2024-06-15, HR — OVERDUE
- Project 8: Data Warehouse, deadline 2024-11-30, Engineering — OVERDUE

**Expected row count: 4**

### Query 4: `get_department_managers(db)`

**Intent:** Return each department's name and its manager's name (looked up from the `employees` table via `departments.manager_id`).

**Bug:** The self-join is missing the `employees` table for manager lookup. The query attempts to join `departments` directly to itself (or uses the wrong alias), failing to resolve `manager_id` to a name.

**Broken SQL:**
```sql
SELECT d.name AS department, m.name AS manager_name
FROM departments d
JOIN employees m ON d.manager_id = d.id
WHERE d.manager_id IS NOT NULL
ORDER BY d.name
```

**Correct SQL:**
```sql
SELECT d.name AS department, m.name AS manager_name
FROM departments d
JOIN employees m ON d.manager_id = m.id
WHERE d.manager_id IS NOT NULL
ORDER BY d.name
```

**Expected results:**
- Engineering → Dave (manager_id=4)
- HR → Heidi (manager_id=8)
- Marketing → Carol (manager_id=3)
- Sales → Grace (manager_id=7)

**Expected row count: 4** (Executive has NULL manager_id, excluded)

### Query 5: `get_employee_count_by_dept(db)`

**Intent:** Return each department and its employee count, ordered by count descending, then department name ascending.

**Bug:** The ORDER BY clause references `count` (the alias) directly, which some SQLite versions handle, but the broken query uses `ORDER BY COUNT(e.id) DESC` (repeating the aggregate expression) and also includes a typo — it says `ORDER BY COUNT(e.id) DESC, d.name ASC` but the SELECT uses `COUNT(*)` not `COUNT(e.id)`, causing SQLite to treat them as different expressions in strict mode, returning rows in an undefined order. Additionally the broken query does a RIGHT JOIN (not supported in older SQLite) instead of LEFT JOIN, dropping departments with no employees.

**Broken SQL:**
```sql
SELECT d.name AS department, COUNT(*) AS emp_count
FROM departments d
RIGHT JOIN employees e ON e.department = d.name
GROUP BY d.name
ORDER BY COUNT(e.id) DESC, d.name ASC
```

**Correct SQL:**
```sql
SELECT d.name AS department, COUNT(e.id) AS emp_count
FROM departments d
LEFT JOIN employees e ON e.department = d.name
GROUP BY d.id, d.name
ORDER BY emp_count DESC, d.name ASC
```

**Expected results:**
- Engineering: 5
- Marketing: 4
- HR: 3
- Sales: 3
- Executive: 0

**Expected row count: 5**

## Deliverables

The executor must edit `queries.py` so that all 5 functions return correct results. The fix for each query is a targeted SQL correction — no schema changes, no data changes.

- `get_high_salary_employees`: fix the correlated subquery
- `get_over_budget_departments`: fix the JOIN condition (`d.id` -> `d.name`)
- `get_overdue_projects`: fix the date comparison (use ISO string `'2025-01-01'`)
- `get_department_managers`: fix the JOIN condition (`d.id` -> `m.id`)
- `get_employee_count_by_dept`: fix RIGHT JOIN -> LEFT JOIN and ORDER BY alias
