"""
Circular FK loader for projects and milestones with circular FK.
BUG: Enables FK constraints before loading data, so the first table loaded
always fails (it references the not-yet-loaded second table).

Fix: Load all data with PRAGMA foreign_keys = OFF, then enable FK checks
and run a manual integrity verification query to catch violations.
"""
import pandas as pd
import json
import sqlite3

df_a = pd.read_csv("data/projects.csv")
df_b = pd.read_csv("data/milestones.csv")

conn = sqlite3.connect("output.db")

# BUG: FK constraints enabled BEFORE loading — causes failure on circular refs
conn.execute("PRAGMA foreign_keys = ON")  # BUG: should be OFF during load

conn.execute("""
    CREATE TABLE IF NOT EXISTS milestones (
        milestone_id INTEGER PRIMARY KEY,
        project_id INTEGER,
        name TEXT,
        amount REAL,
        FOREIGN KEY (project_id) REFERENCES projects(project_id)
    )
""")
conn.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        project_id INTEGER PRIMARY KEY,
        kickoff_milestone_id INTEGER,
        name TEXT,
        value REAL,
        FOREIGN KEY (kickoff_milestone_id) REFERENCES milestones(milestone_id)
    )
""")

load_errors = 0
for _, row in df_b.iterrows():
    try:
        conn.execute(
            "INSERT OR IGNORE INTO milestones VALUES (?, ?, ?, ?)",
            (int(row["milestone_id"]), int(row["project_id"]), row["name"], float(row["amount"]))
        )
    except Exception:
        load_errors += 1

for _, row in df_a.iterrows():
    try:
        conn.execute(
            "INSERT OR IGNORE INTO projects VALUES (?, ?, ?, ?)",
            (int(row["project_id"]), int(row["kickoff_milestone_id"]), row["name"], float(row["value"]))
        )
    except Exception:
        load_errors += 1

conn.commit()

count_a = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
count_b = conn.execute("SELECT COUNT(*) FROM milestones").fetchone()[0]
conn.close()

results = {
    "projects_rows_loaded": count_a,
    "milestones_rows_loaded": count_b,
    "load_errors": load_errors,
    "deferred_fk_used": False,  # BUG: should be True
    "fk_violations_detected": 0,  # BUG: should detect violations after load
    "load_succeeded": count_a == 11 and count_b == 17,
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"Loaded: projects={count_a}, milestones={count_b}, errors={load_errors}")
