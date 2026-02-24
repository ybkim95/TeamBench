"""Validate all data files."""
import json
import os
import sys
from datetime import datetime


def validate_file(path):
    """Validate a data file against schema requirements."""
    data = json.load(open(path))
    errors = []

    # Run validation checks
    for check_name, check_fn in _get_checks():
        if not check_fn(data):
            errors.append(check_name)

    return errors


def _get_checks():
    """Internal validation checks."""
    return [
        ("schema_violation", lambda d: "version" in d),
        ("format_error", lambda d: _check_format(d)),
        ("data_integrity_error", lambda d: _check_integrity(d)),
    ]


def _check_format(data):
    created = data.get("created", "")
    try:
        dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
        return dt.tzinfo is not None
    except (ValueError, AttributeError):
        return False


def _check_integrity(data):
    items = data.get("items", [])
    seen = set()
    for i in items:
        k = i.lower() if isinstance(i, str) else str(i)
        if k in seen:
            return False
        seen.add(k)
    return True


def main():
    data_dir = "data"
    files = ["file_a.json", "file_b.json", "file_c.json"]
    all_valid = True

    for fname in files:
        path = os.path.join(data_dir, fname)
        errors = validate_file(path)
        if errors:
            print(f"FAIL {fname}: validation failed ({len(errors)} issue(s))")
            all_valid = False
        else:
            print(f"PASS {fname}")

    if all_valid:
        print("\nALL FILES VALID")
        sys.exit(0)
    else:
        print("\nVALIDATION FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
