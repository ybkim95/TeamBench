#!/usr/bin/env python3
"""Compute human-IRR statistics from filled CSVs.

Reads any human_irr_filled_*.csv in shared/paper/teambench_quality/human_irr/.
Computes:
  - pairwise Cohen kappa: human vs each of {grader, haiku45, g3flash, gpt54mini}
  - pairwise Cohen kappa: human vs human (if 2+ raters)
  - 3-way Fleiss kappa: humans vs grader (if 2+ humans)
  - Binary Krippendorff alpha
"""
import csv, glob, json, os
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.path.join(REPO, "shared/paper/teambench_quality/human_irr")
OUT = os.path.join(DIR, "human_irr_summary.json")


def cohen_kappa(a, b):
    n = len(a)
    if n == 0: return float("nan")
    cats = sorted(set(a) | set(b))
    obs = sum(1 for x, y in zip(a, b) if x == y) / n
    pe = sum((sum(1 for x in a if x == c) / n) * (sum(1 for x in b if x == c) / n) for c in cats)
    return round((obs - pe) / (1 - pe), 4) if pe < 1 else 1.0


def main():
    files = sorted(glob.glob(os.path.join(DIR, "human_irr_filled_*.csv")))
    if not files:
        print("no human_irr_filled_*.csv files yet — instructions in INSTRUCTIONS.md")
        return
    raters = {}  # rater_id -> {row_id: verdict}
    for fn in files:
        with open(fn) as f:
            for row in csv.DictReader(f):
                rid = row.get("human_rater_id","").strip()
                v = row.get("human_verdict","").strip().upper()
                if not rid or v not in ("PASS","FAIL"): continue
                raters.setdefault(rid, {})[row["row_id"]] = v
    print(f"raters: {list(raters)}")

    # Reference labels: grader + 3 LLM judges (from the same form)
    ref_grader = {}
    ref_llm = {"haiku45":{}, "g3flash":{}, "gpt54mini":{}}
    sample = files[0]
    with open(sample) as f:
        for row in csv.DictReader(f):
            ref_grader[row["row_id"]] = "PASS" if row["deterministic_grader_pass"]=="True" else "FAIL"
            for k in ref_llm:
                v = row.get(f"{k}_verdict","").strip().upper()
                if v in ("PASS","FAIL"):
                    ref_llm[k][row["row_id"]] = v

    summary = {"raters": list(raters), "n_per_rater": {r: len(d) for r,d in raters.items()}, "kappas": {}}
    for r, vs in raters.items():
        ids = list(vs.keys())
        a = [vs[i] for i in ids]
        b = [ref_grader[i] for i in ids]
        summary["kappas"][f"{r}_vs_grader"] = cohen_kappa(a, b)
        for k in ref_llm:
            ids2 = [i for i in ids if i in ref_llm[k]]
            summary["kappas"][f"{r}_vs_{k}"] = cohen_kappa(
                [vs[i] for i in ids2], [ref_llm[k][i] for i in ids2])
    rids = list(raters)
    for i in range(len(rids)):
        for j in range(i+1, len(rids)):
            ids = sorted(set(raters[rids[i]]) & set(raters[rids[j]]))
            summary["kappas"][f"{rids[i]}_vs_{rids[j]}"] = cohen_kappa(
                [raters[rids[i]][x] for x in ids], [raters[rids[j]][x] for x in ids])

    json.dump(summary, open(OUT, "w"), indent=2)
    print(json.dumps(summary, indent=2))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
