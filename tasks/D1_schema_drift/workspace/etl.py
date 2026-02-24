"""ETL pipeline — read CSV batches and produce unified output."""
import csv
import os


def run():
    input_dir = "data/input"
    output_dir = "data/output"
    os.makedirs(output_dir, exist_ok=True)

    rows = []
    for fname in sorted(os.listdir(input_dir)):
        if not fname.endswith(".csv"):
            continue
        with open(os.path.join(input_dir, fname), "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(dict(row))

    # Normalize columns across batches
    normalized = []
    for row in rows:
        out = {}
        # Handle full_name -> name rename
        out["name"] = row.get("full_name", row.get("name", ""))
        out["id"] = row.get("id", "")
        out["value"] = row.get("value", "0")
        # Fill missing category
        out["category"] = row.get("category", "")
        normalized.append(out)

    # Deduplicate by id — keep first occurrence
    seen_ids = set()
    deduped = []
    for row in normalized:
        if row["id"] not in seen_ids:
            seen_ids.add(row["id"])
            deduped.append(row)

    # Sort by id ascending
    deduped.sort(key=lambda r: int(r["id"]) if r["id"].isdigit() else 0)

    with open(os.path.join(output_dir, "result.csv"), "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "name", "value", "category"])
        writer.writeheader()
        for row in deduped:
            writer.writerow(row)


if __name__ == "__main__":
    run()
