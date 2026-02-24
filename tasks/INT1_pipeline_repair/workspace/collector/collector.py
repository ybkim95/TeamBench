"""Collect data from CSV input."""
import csv
import json
import os


def collect(input_path, output_path):
    """Read CSV and output JSON records."""
    records = []
    with open(input_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            records.append({
                "name": row.get("name", "").strip(),
                "email": row.get("email", "").strip(),
                "score": row.get("score", "0").strip(),
                "raw_line": i,
            })

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    # Write as newline-delimited JSON
    with open(output_path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")

    return len(records)


if __name__ == "__main__":
    count = collect("data/input.csv", "data/collected.json")
    print(f"Collected {count} records")
