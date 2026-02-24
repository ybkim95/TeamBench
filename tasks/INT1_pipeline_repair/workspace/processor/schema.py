"""Validation schema for records."""
import re

# Email pattern - standard validation
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


def validate_record(record):
    """Validate a single record. Returns list of issues (empty = valid)."""
    issues = []

    name = record.get("name", "")
    if not name or not name.strip():
        issues.append("empty_name")

    email = record.get("email", "")
    if not EMAIL_PATTERN.match(email):
        issues.append("invalid_email")

    try:
        score = int(record.get("score", ""))
        if score < 0 or score > 100:
            issues.append("score_out_of_range")
    except (ValueError, TypeError):
        issues.append("invalid_score")

    return issues
