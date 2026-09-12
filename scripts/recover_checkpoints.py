#!/usr/bin/env python3
"""Reconstruct checkpoint files from ablation log files.

Parses log lines like:
  [N/200] oracle x TASK_ID (seed=0)
    PASS (partial=1.00, 300.5s, 19 turns)
or
    FAIL (partial=0.90, 300.5s, 19 turns)

and writes a checkpoint.jsonl that run_full_ablation can resume from.
"""
import json
import os
import re
import sys

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "shared", "ablation_results")

MODELS = {
    "haiku45": "lb100_haiku45_oraclefull_seed0.json",
    "sonnet46": "lb100_sonnet46_oraclefull_seed0.json",
    "gpt54": "lb100_gpt54_oraclefull_seed0.json",
    "gpt5nano": "lb100_gpt5nano_oraclefull_seed0.json",
    "gemini3flash": "lb100_gemini3flash_oraclefull_seed0.json",
    "gemini31lite": "lb100_gemini31lite_oraclefull_seed0.json",
}

RUN_RE = re.compile(r'^\[(\d+)/(\d+)\]\s+(oracle|full|restricted|team_no_verify|team_no_plan)\s+x\s+(\S+)\s+\(seed=(\d+)\)')
RESULT_RE = re.compile(r'^\s+(PASS|FAIL)\s+\(partial=([0-9.]+),\s+([0-9.]+)s,\s+(\d+)\s+turns\)')
SKIP_RE = re.compile(r'SKIPPED \(checkpoint\)')
ERROR_RE = re.compile(r'^\s+ERROR:\s+(.*)')


def parse_log(log_path):
    """Parse a log file and return list of completed run entries."""
    entries = []
    current = None

    with open(log_path) as f:
        for line in f:
            line = line.rstrip()

            # Match run header
            m = RUN_RE.match(line)
            if m:
                current = {
                    "idx": int(m.group(1)),
                    "condition": m.group(3),
                    "task_id": m.group(4),
                    "seed": int(m.group(5)),
                }
                continue

            if current is None:
                continue

            # Skip checkpointed runs
            if SKIP_RE.search(line):
                current = None
                continue

            # Match result
            m = RESULT_RE.match(line)
            if m:
                status = m.group(1)
                partial = float(m.group(2))
                elapsed = float(m.group(3))
                entry = {
                    "condition": current["condition"],
                    "task_id": current["task_id"],
                    "seed": current["seed"],
                    "run_id": f"recovered_{current['idx']}",
                    "run_dir": "",
                    "pass": status == "PASS",
                    "partial_score": partial,
                    "elapsed_sec": elapsed,
                    "failure_modes": [],
                    "error": None,
                }
                entries.append(entry)
                current = None
                continue

            # Match error
            m = ERROR_RE.match(line)
            if m:
                entry = {
                    "condition": current["condition"],
                    "task_id": current["task_id"],
                    "seed": current["seed"],
                    "run_id": f"recovered_{current['idx']}",
                    "run_dir": "",
                    "pass": False,
                    "partial_score": 0.0,
                    "elapsed_sec": 0.0,
                    "failure_modes": [],
                    "error": m.group(1),
                }
                entries.append(entry)
                current = None
                continue

    return entries


def main():
    for model_key, out_json in MODELS.items():
        log_path = os.path.join(LOG_DIR, f"ablation_{model_key}_of.log")
        checkpoint_path = os.path.join(OUT_DIR, out_json + ".checkpoint.jsonl")

        if not os.path.isfile(log_path):
            print(f"SKIP {model_key}: no log file")
            continue

        if os.path.isfile(checkpoint_path):
            existing = sum(1 for _ in open(checkpoint_path))
            print(f"SKIP {model_key}: checkpoint already exists ({existing} entries)")
            continue

        entries = parse_log(log_path)
        if not entries:
            print(f"SKIP {model_key}: no completed runs found in log")
            continue

        # Deduplicate by (condition, task_id, seed)
        seen = set()
        unique = []
        for e in entries:
            key = f"{e['condition']}:{e['task_id']}:{e['seed']}"
            if key not in seen:
                seen.add(key)
                unique.append(e)

        with open(checkpoint_path, "w") as f:
            for e in unique:
                f.write(json.dumps(e) + "\n")

        oracle = sum(1 for e in unique if e["condition"] == "oracle")
        full = sum(1 for e in unique if e["condition"] == "full")
        passes = sum(1 for e in unique if e["pass"])
        print(f"RECOVERED {model_key}: {len(unique)} runs (oracle={oracle}, full={full}, pass={passes}) -> {checkpoint_path}")


if __name__ == "__main__":
    main()
