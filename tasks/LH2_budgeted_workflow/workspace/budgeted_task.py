"""
Budgeted task: fix data files within execution budget.
Each significant operation is logged to budget_log.jsonl.
"""
import json
import os
from datetime import datetime, timezone


BUDGET_LOG = "budget_log.jsonl"
BUDGET_LIMIT = 20


def log_execution(action, detail=""):
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "detail": detail,
    }
    with open(BUDGET_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


def get_budget_used():
    if not os.path.exists(BUDGET_LOG):
        return 0
    with open(BUDGET_LOG) as f:
        return sum(1 for line in f if line.strip())


def check_budget():
    used = get_budget_used()
    if used >= BUDGET_LIMIT:
        raise RuntimeError(f"Budget exhausted: {used}/{BUDGET_LIMIT}")
    return used


def load_file(path):
    check_budget()
    log_execution("read", path)
    with open(path, "r") as f:
        return json.load(f)


def save_file(path, data):
    check_budget()
    log_execution("write", path)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def validate_file(path):
    """Validate a single data file. Returns (valid, errors)."""
    check_budget()
    log_execution("validate", path)
    data = json.load(open(path))
    errors = []

    if "version" not in data:
        errors.append("missing_version")

    created = data.get("created", "")
    try:
        datetime.fromisoformat(created.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        errors.append("invalid_date_format")

    items = data.get("items", [])
    if len(items) != len(set(items)):
        errors.append("duplicate_items")

    return len(errors) == 0, errors


def fix_file(path, errors):
    """Attempt to fix known errors in a data file."""
    check_budget()
    log_execution("fix", path)
    data = json.load(open(path))

    if "missing_version" in errors:
        data["version"] = "1.0"
    if "invalid_date_format" in errors:
        data["created"] = datetime.now(timezone.utc).isoformat()
    if "duplicate_items" in errors:
        data["items"] = list(dict.fromkeys(data["items"]))

    # Write fixed data to staging area
    staging = path + ".tmp"
    with open(staging, "w") as f:
        json.dump(data, f, indent=2)


def main():
    log_execution("start", "budgeted_task.py")
    os.makedirs("output", exist_ok=True)

    data_dir = "data"
    files = ["file_a.json", "file_b.json", "file_c.json"]

    results = {}
    for fname in files:
        path = os.path.join(data_dir, fname)
        data = load_file(path)

        valid, errors = validate_file(path)
        if not valid:
            print(f"{fname}: {errors}")
            fix_file(path, errors)
            results[fname] = "fixed"
        else:
            print(f"{fname}: OK")
            results[fname] = "ok"

    log_execution("end", "budgeted_task.py")

    budget_used = get_budget_used()
    report = {
        "files_fixed": 0,
        "budget_total": BUDGET_LIMIT,
        "budget_used": budget_used,
        "all_valid": False,
    }
    with open("output/budget_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print(f"Budget: {budget_used}/{BUDGET_LIMIT}")


if __name__ == "__main__":
    main()
