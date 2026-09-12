"""
Circular FK loader for employees and departments with circular FK.
BUG: Enables FK constraints before loading data, so the first table loaded
always fails (it references the not-yet-loaded second table).

Fix: Load all data with PRAGMA foreign_keys = OFF, then enable FK checks
and run a manual integrity verification query to catch violations.
"""
import pandas as pd
import json
import sqlite3

df_a = pd.read_csv("data/employees.csv")
df_b = pd.read_csv("data/departments.csv")

conn = sqlite3.connect("output.db")

# BUG: FK constraints enabled BEFORE loading — causes failure on circular refs
conn.execute("PRAGMA foreign_keys = ON")  # BUG: should be OFF during load

conn.execute("""
    CREATE TABLE IF NOT EXISTS departments (
        dept_id INTEGER PRIMARY KEY,
        manager_id INTEGER,
        name TEXT,
        amount REAL,
        FOREIGN KEY (manager_id) REFERENCES employees(employee_id)
    )
""")
conn.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        employee_id INTEGER PRIMARY KEY,
        dept_id INTEGER,
        name TEXT,
        value REAL,
        FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
    )
""")

load_errors = 0
for _, row in df_b.iterrows():
    try:
        conn.execute(
            "INSERT OR IGNORE INTO departments VALUES (?, ?, ?, ?)",
            (int(row["dept_id"]), int(row["manager_id"]), row["name"], float(row["amount"]))
        )
    except Exception:
        load_errors += 1

for _, row in df_a.iterrows():
    try:
        conn.execute(
            "INSERT OR IGNORE INTO employees VALUES (?, ?, ?, ?)",
            (int(row["employee_id"]), int(row["dept_id"]), row["name"], float(row["value"]))
        )
    except Exception:
        load_errors += 1

conn.commit()

count_a = conn.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
count_b = conn.execute("SELECT COUNT(*) FROM departments").fetchone()[0]
conn.close()

results = {
    "employees_rows_loaded": count_a,
    "departments_rows_loaded": count_b,
    "load_errors": load_errors,
    "deferred_fk_used": False,  # BUG: should be True
    "fk_violations_detected": 0,  # BUG: should detect violations after load
    "load_succeeded": count_a == 14 and count_b == 33,
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"Loaded: employees={count_a}, departments={count_b}, errors={load_errors}")
