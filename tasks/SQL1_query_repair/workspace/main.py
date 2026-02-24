"""Test runner for SQL1_query_repair.

Runs all 5 query functions, prints results, validates expected row counts,
and exits 0 if all pass or 1 if any fail.
"""
import json
import os
import sqlite3
import sys

from queries import (
    get_department_managers,
    get_employee_count_by_dept,
    get_high_salary_employees,
    get_over_budget_departments,
    get_overdue_projects,
)

DB_PATH = "company.db"

# Expected results for each query
EXPECTED = {
    "get_high_salary_employees": {
        "row_count": 7,
        "description": "employees earning above their department average",
    },
    "get_over_budget_departments": {
        "row_count": 3,
        "description": "departments whose total salary exceeds budget",
        "names": ["HR", "Marketing", "Sales"],
    },
    "get_overdue_projects": {
        "row_count": 4,
        "description": "active projects with deadline before 2025-01-01",
    },
    "get_department_managers": {
        "row_count": 4,
        "description": "departments with their manager names",
        "managers": {
            "Engineering": "Dave",
            "HR": "Heidi",
            "Marketing": "Carol",
            "Sales": "Grace",
        },
    },
    "get_employee_count_by_dept": {
        "row_count": 5,
        "description": "employee count per department including zero-count depts",
        "first_dept": "Engineering",  # highest count = 5
    },
}


def run_check(name, rows, spec):
    failures = []

    actual_count = len(rows)
    expected_count = spec["row_count"]
    if actual_count != expected_count:
        failures.append(
            f"row count: expected {expected_count}, got {actual_count}"
        )

    if "names" in spec:
        actual_names = sorted(r.get("name", r.get("department", "")) for r in rows)
        expected_names = sorted(spec["names"])
        if actual_names != expected_names:
            failures.append(
                f"department names: expected {expected_names}, got {actual_names}"
            )

    if "managers" in spec:
        actual_mgrs = {r["department"]: r["manager_name"] for r in rows}
        for dept, mgr in spec["managers"].items():
            if actual_mgrs.get(dept) != mgr:
                failures.append(
                    f"manager for {dept}: expected {mgr!r}, got {actual_mgrs.get(dept)!r}"
                )

    if "first_dept" in spec and rows:
        if rows[0]["department"] != spec["first_dept"]:
            failures.append(
                f"first dept: expected {spec['first_dept']!r}, got {rows[0]['department']!r}"
            )

    return failures


def main():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: {DB_PATH} not found. Run `python3 setup_db.py` first.")
        sys.exit(1)

    db = sqlite3.connect(DB_PATH)

    checks = [
        ("get_high_salary_employees",  get_high_salary_employees),
        ("get_over_budget_departments", get_over_budget_departments),
        ("get_overdue_projects",        get_overdue_projects),
        ("get_department_managers",     get_department_managers),
        ("get_employee_count_by_dept",  get_employee_count_by_dept),
    ]

    all_passed = True

    for name, fn in checks:
        spec = EXPECTED[name]
        print(f"\n=== {name} ===")
        print(f"    ({spec['description']})")
        try:
            rows = fn(db)
        except Exception as exc:
            print(f"  ERROR: {exc}")
            all_passed = False
            continue

        for row in rows:
            print(f"  {row}")

        failures = run_check(name, rows, spec)
        if failures:
            all_passed = False
            for f in failures:
                print(f"  FAIL: {f}")
        else:
            print(f"  PASS ({len(rows)} rows)")

    db.close()

    print("\n" + ("=" * 40))
    if all_passed:
        print("ALL CHECKS PASSED")
        # Write attestation
        att = {"verdict": "pass", "checks": 5, "passed": 5}
        with open("attestation.json", "w") as fh:
            json.dump(att, fh)
        sys.exit(0)
    else:
        print("SOME CHECKS FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
