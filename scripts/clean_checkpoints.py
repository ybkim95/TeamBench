#!/usr/bin/env python3
"""Remove error entries from checkpoint files so failed runs can be retried."""
import json
import os
import sys

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "shared", "ablation_results")

MODELS = [
    "lb100_haiku45_oraclefull_seed0.json",
    "lb100_sonnet46_oraclefull_seed0.json",
    "lb100_gpt54_oraclefull_seed0.json",
    "lb100_gpt5nano_oraclefull_seed0.json",
    "lb100_gemini3flash_oraclefull_seed0.json",
    "lb100_gemini31lite_oraclefull_seed0.json",
    "lb100_gemini25pro_oraclefull_seed0.json",
]


def clean_checkpoint(cp_path):
    if not os.path.isfile(cp_path):
        return 0, 0, 0

    entries = []
    for line in open(cp_path):
        try:
            entries.append(json.loads(line.strip()))
        except json.JSONDecodeError:
            pass

    total = len(entries)
    good = [e for e in entries if not e.get("error")]
    removed = total - len(good)

    if removed > 0:
        # Backup original
        backup = cp_path + ".backup"
        os.rename(cp_path, backup)
        # Write cleaned
        with open(cp_path, "w") as f:
            for e in good:
                f.write(json.dumps(e) + "\n")

    return total, len(good), removed


def clean_json_output(json_path):
    """Also clean the final .json output file if it exists, removing error runs."""
    if not os.path.isfile(json_path):
        return

    with open(json_path) as f:
        data = json.load(f)

    runs = data.get("runs", [])
    good = [r for r in runs if not r.get("error")]
    removed = len(runs) - len(good)

    if removed > 0:
        # Remove the completed output so it will be regenerated on re-run
        backup = json_path + ".backup"
        os.rename(json_path, backup)
        print(f"  Removed completed output (had {removed} error runs) -> backup at {backup}")


def main():
    for out_json in MODELS:
        cp_path = os.path.join(RESULTS_DIR, out_json + ".checkpoint.jsonl")
        json_path = os.path.join(RESULTS_DIR, out_json)
        name = out_json.split("_")[1]  # e.g., haiku45

        total, good, removed = clean_checkpoint(cp_path)
        if total == 0:
            print(f"{name}: no checkpoint found")
            continue

        print(f"{name}: {total} total -> {good} valid, {removed} errors removed")
        clean_json_output(json_path)


if __name__ == "__main__":
    main()
