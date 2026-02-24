"""SQL query functions for company reporting.

Each function accepts a sqlite3.Connection and returns a list of dicts.
All 5 queries below contain a subtle bug -- fix them so main.py passes.
"""
import sqlite3


def get_high_salary_employees(db: sqlite3.Connection) -> list[dict]:
    """Return employees whose salary exceeds their department's average salary.

    Bug: uses a global AVG instead of a correlated per-department AVG.
    """
    cur = db.cursor()
    cur.execute("""
        SELECT e.id, e.name, e.department, e.salary
        FROM employees e
        WHERE e.salary > (SELECT AVG(salary) FROM employees)
        ORDER BY e.department, e.salary DESC
    """)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def get_over_budget_departments(db: sqlite3.Connection) -> list[dict]:
    """Return departments where total employee salary exceeds the department budget.

    Bug: JOIN condition uses d.id (integer PK) instead of d.name (text),
    so the text-to-integer comparison matches nothing in SQLite.
    """
    cur = db.cursor()
    cur.execute("""
        SELECT d.name, d.budget, SUM(e.salary) AS total_salary
        FROM employees e
        JOIN departments d ON e.department = d.id
        GROUP BY d.name
        HAVING SUM(e.salary) > d.budget
        ORDER BY d.name
    """)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def get_overdue_projects(db: sqlite3.Connection) -> list[dict]:
    """Return active projects whose deadline has already passed.

    Uses a fixed reference date of 2025-01-01 for deterministic grading.

    Bug: compares ISO date strings against a Unix timestamp integer string
    produced by strftime('%s', 'now'), so the string comparison is wrong
    and no projects appear overdue.
    """
    cur = db.cursor()
    cur.execute("""
        SELECT p.id, p.name, p.deadline, d.name AS department
        FROM projects p
        JOIN departments d ON p.department_id = d.id
        WHERE p.status = 'active'
          AND p.deadline < strftime('%s', 'now')
        ORDER BY p.deadline
    """)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def get_department_managers(db: sqlite3.Connection) -> list[dict]:
    """Return each department and its manager's name.

    Bug: JOIN condition uses d.id instead of m.id, so the join is always
    a self-match on the department's own PK rather than looking up the
    manager employee row.
    """
    cur = db.cursor()
    cur.execute("""
        SELECT d.name AS department, m.name AS manager_name
        FROM departments d
        JOIN employees m ON d.manager_id = d.id
        WHERE d.manager_id IS NOT NULL
        ORDER BY d.name
    """)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def get_employee_count_by_dept(db: sqlite3.Connection) -> list[dict]:
    """Return each department and its employee count, ordered by count desc.

    Bug 1: RIGHT JOIN is not supported in SQLite < 3.39, dropping the
    Executive department (which has 0 employees).
    Bug 2: ORDER BY references COUNT(e.id) as a new aggregate expression
    rather than the aliased column emp_count, producing undefined ordering.
    """
    cur = db.cursor()
    cur.execute("""
        SELECT d.name AS department, COUNT(*) AS emp_count
        FROM departments d
        RIGHT JOIN employees e ON e.department = d.name
        GROUP BY d.name
        ORDER BY COUNT(e.id) DESC, d.name ASC
    """)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]
