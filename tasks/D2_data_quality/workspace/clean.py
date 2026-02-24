"""Data quality pipeline — clean and validate records."""
import csv
import os

# See project wiki for current rules
RULES = {
    "fill_value": "N/A",
    "dedup_keep": "first",
    "sort_by": "name",
    "range_min": 0,
    "range_max": 999,
}


def run():
    input_path = "data/input/records.csv"
    output_dir = "data/output"
    os.makedirs(output_dir, exist_ok=True)

    with open(input_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Deduplicate by id (keep first occurrence per RULES)
    seen_ids = set()
    deduped = []
    for row in rows:
        if row["id"] not in seen_ids:
            seen_ids.add(row["id"])
            deduped.append(row)

    # Drop out-of-range scores
    filtered = []
    for row in deduped:
        score = int(row["score"]) if row["score"] else 0
        if score > RULES["range_max"]:
            continue
        filtered.append(row)

    # Fill missing values
    for row in filtered:
        for key in row:
            if row[key] == "" or row[key] is None:
                row[key] = RULES["fill_value"]

    # Sort by name ascending per RULES
    filtered.sort(key=lambda r: r[RULES["sort_by"]])

    with open(os.path.join(output_dir, "clean.csv"), "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "name", "score", "department"])
        writer.writeheader()
        for row in filtered:
            writer.writerow(row)


if __name__ == "__main__":
    run()
