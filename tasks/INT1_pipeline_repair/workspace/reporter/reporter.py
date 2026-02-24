"""Generate summary report from processed records."""
import json
import os


def generate_report(input_path, output_path, template_path=None):
    """Generate a text report from processed records."""
    with open(input_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    # Sort by score descending
    records.sort(key=lambda r: r.get("score", 0), reverse=True)

    lines = ["=" * 50, "DATA PROCESSING REPORT", "=" * 50, ""]
    lines.append(f"Total records processed: {len(records)}")
    lines.append("")
    lines.append("RECORDS (sorted by score, descending):")
    lines.append("-" * 50)

    for i, record in enumerate(records, 1):
        lines.append(f"{i}. {record['full_name']} ({record['email']}) - Score: {record['score']}")

    lines.append("")
    lines.append("=" * 50)
    lines.append("END OF REPORT")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return len(records)


if __name__ == "__main__":
    count = generate_report("data/processed.json", "data/report.txt")
    print(f"Report generated with {count} records")
