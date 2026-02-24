"""Process and validate collected records."""
import json
import os
from datetime import datetime, timezone
from processor.schema import validate_record


def process(input_path, output_path, errors_path):
    """Validate and transform records."""
    with open(input_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    processed = []
    errors = []

    for record in records:
        issues = validate_record(record)
        if issues:
            errors.append({"record": record, "issues": issues})
            continue

        processed.append({
            "full_name": record["name"],
            "email": record["email"],
            "score": int(record["score"]),
            "processed_at": datetime.now(timezone.utc).isoformat(),
        })

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(processed, f, indent=2)

    if errors:
        with open(errors_path, "w", encoding="utf-8") as f:
            for err in errors:
                f.write(json.dumps(err) + "\n")

    return len(processed), len(errors)


if __name__ == "__main__":
    ok, err = process("data/collected.json", "data/processed.json", "data/errors.jsonl")
    print(f"Processed: {ok} valid, {err} errors")
