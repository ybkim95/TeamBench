"""Create and populate company.db for SQL1_query_repair task."""
import sqlite3
import os

DB_PATH = "company.db"


def setup():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # --- Schema ---
    cur.executescript("""
        CREATE TABLE employees (
            id          INTEGER PRIMARY KEY,
            name        TEXT NOT NULL,
            department  TEXT NOT NULL,
            salary      REAL NOT NULL,
            hire_date   TEXT NOT NULL
        );

        CREATE TABLE departments (
            id          INTEGER PRIMARY KEY,
            name        TEXT NOT NULL,
            budget      REAL NOT NULL,
            manager_id  INTEGER
        );

        CREATE TABLE projects (
            id            INTEGER PRIMARY KEY,
            name          TEXT NOT NULL,
            department_id INTEGER NOT NULL,
            deadline      TEXT NOT NULL,
            status        TEXT NOT NULL
        );
    """)

    # --- Employees (15 rows) ---
    employees = [
        (1,  "Alice",  "Engineering", 95000,  "2019-03-15"),
        (2,  "Bob",    "Engineering", 72000,  "2020-07-01"),
        (3,  "Carol",  "Marketing",   68000,  "2018-11-20"),
        (4,  "Dave",   "Engineering", 110000, "2017-05-10"),
        (5,  "Eve",    "Marketing",   75000,  "2021-02-28"),
        (6,  "Frank",  "Sales",       58000,  "2022-01-15"),
        (7,  "Grace",  "Sales",       62000,  "2021-09-03"),
        (8,  "Heidi",  "HR",          70000,  "2019-06-22"),
        (9,  "Ivan",   "HR",          66000,  "2020-04-11"),
        (10, "Judy",   "Engineering", 88000,  "2018-08-30"),
        (11, "Karl",   "Marketing",   71000,  "2023-03-01"),
        (12, "Liam",   "Sales",       54000,  "2022-11-14"),
        (13, "Mia",    "HR",          73000,  "2021-07-19"),
        (14, "Noah",   "Engineering", 91000,  "2016-12-05"),
        (15, "Olivia", "Marketing",   65000,  "2023-06-30"),
    ]
    cur.executemany(
        "INSERT INTO employees VALUES (?, ?, ?, ?, ?)", employees
    )

    # --- Departments (5 rows) ---
    # Note: Executive has no employees — tests LEFT JOIN in Q5.
    # Marketing (279000) > budget (200000), Sales (174000) > budget (150000),
    # HR (209000) > budget (180000) — tests Q2.
    # Engineering (456000) < budget (500000) — not over budget.
    departments = [
        (1, "Engineering", 500000, 4),
        (2, "Marketing",   200000, 3),
        (3, "Sales",       150000, 7),
        (4, "HR",          180000, 8),
        (5, "Executive",   300000, None),
    ]
    cur.executemany(
        "INSERT INTO departments VALUES (?, ?, ?, ?)", departments
    )

    # --- Projects (8 rows) ---
    # Active projects with deadline < 2025-01-01 (overdue as of 2025-01-01):
    #   id=3  Sales Automation   2024-03-01  Sales
    #   id=6  Brand Refresh      2024-09-01  Marketing
    #   id=7  Recruit Pipeline   2024-06-15  HR
    #   id=8  Data Warehouse     2024-11-30  Engineering
    # Active projects NOT overdue (deadline >= 2025-01-01):
    #   id=5  Mobile App         2025-01-01  Engineering  (boundary — not < so excluded)
    projects = [
        (1, "Platform Rewrite",   1, "2023-06-01", "completed"),
        (2, "Q4 Campaign",        2, "2024-01-15", "completed"),
        (3, "Sales Automation",   3, "2024-03-01", "active"),
        (4, "HR Portal",          4, "2023-12-31", "completed"),
        (5, "Mobile App",         1, "2025-01-01", "active"),
        (6, "Brand Refresh",      2, "2024-09-01", "active"),
        (7, "Recruit Pipeline",   4, "2024-06-15", "active"),
        (8, "Data Warehouse",     1, "2024-11-30", "active"),
    ]
    cur.executemany(
        "INSERT INTO projects VALUES (?, ?, ?, ?, ?)", projects
    )

    conn.commit()
    conn.close()
    print(f"Database created: {DB_PATH}")


if __name__ == "__main__":
    setup()
