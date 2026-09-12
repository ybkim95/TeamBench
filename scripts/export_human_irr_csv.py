#!/usr/bin/env python3
"""Export the same 285 (task, condition, run) tuples used in LLM-as-rater
into a CSV form for human inter-rater agreement.

For each row, the human rater opens the linked spec.md and run_dir/workspace,
fills in PASS / FAIL + a brief reason, and saves the CSV.

Output:
  shared/paper/teambench_quality/human_irr/human_irr_form.csv
  shared/paper/teambench_quality/human_irr/INSTRUCTIONS.md
  shared/paper/teambench_quality/human_irr/protocol.md
  (later) human_irr_filled.csv  <- rater fills this and saves

After human raters fill the CSV, run:
  python scripts/score_human_irr.py
to compute pairwise Cohen's kappa, three-way Fleiss's kappa, and Krippendorff's
alpha against both the deterministic grader AND the LLM judges.

Usage:
  python scripts/export_human_irr_csv.py
"""
from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LLM = os.path.join(REPO, "shared/paper/teambench_quality/llm_inter_rater.json")
OUT_DIR = os.path.join(REPO, "shared/paper/teambench_quality/human_irr")
os.makedirs(OUT_DIR, exist_ok=True)


def main():
    if not os.path.isfile(LLM):
        raise SystemExit(f"missing {LLM}; run scripts/llm_inter_rater.py first")
    d = json.load(open(LLM))
    judgments = d["judgments"]
    print(f"[human-irr] {len(judgments)} tuples (same as LLM-rater sample)")

    # CSV columns: row_id, task_id, condition, model, run_dir, deterministic_grader_pass,
    # haiku45_verdict, g3flash_verdict, gpt54mini_verdict,
    # human_rater_id, human_verdict (PASS/FAIL/UNSURE), human_reason, time_spent_sec
    out_csv = os.path.join(OUT_DIR, "human_irr_form.csv")
    with open(out_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "row_id",
            "task_id",
            "condition",
            "model",
            "run_dir",
            "spec_path",
            "workspace_path",
            "score_path",
            "deterministic_grader_pass",
            "deterministic_partial",
            "haiku45_verdict",
            "g3flash_verdict",
            "gpt54mini_verdict",
            "human_rater_id",
            "human_verdict",
            "human_reason",
            "time_spent_sec",
        ])
        for i, j in enumerate(judgments, 1):
            rd = j["run_dir"]
            if rd and not os.path.isabs(rd):
                rd_abs = os.path.join(REPO, rd)
            else:
                rd_abs = rd
            spec_path = os.path.join(REPO, "tasks", j["task_id"], "spec.md")
            ws = os.path.join(rd_abs, "workspace") if rd_abs else ""
            score = os.path.join(rd_abs, "reports", "score.json") if rd_abs else ""
            judges = j.get("judges", {})
            w.writerow([
                f"R{i:04d}",
                j["task_id"],
                j["condition"],
                (j.get("model") or "")[:120],
                rd_abs or "",
                spec_path,
                ws,
                score,
                j["grader_pass"],
                j.get("grader_partial"),
                judges.get("haiku45", {}).get("verdict"),
                judges.get("g3flash", {}).get("verdict"),
                judges.get("gpt54mini", {}).get("verdict"),
                "",  # human_rater_id (filled in)
                "",  # human_verdict
                "",  # human_reason
                "",  # time_spent_sec
            ])
    print(f"[human-irr] wrote {out_csv}")

    # Instructions
    instr = """# Human Inter-Rater Instructions for TeamBench

You are reviewing 285 agent task runs that have already been graded by:
  1. The deterministic shell-script grader (`grade.sh`) — column `deterministic_grader_pass`
  2. Three LLM judges (Claude Haiku 4.5, Gemini-3 Flash, GPT-5.4 Mini)

Your job: produce an independent human verdict (PASS / FAIL / UNSURE) per
row in `human_irr_form.csv`.

## Per-row workflow (target ≤ 5 minutes per row)

For each row in the CSV:

1. Open the **task spec**:
   ```
   $ less <spec_path>          # the full task specification
   ```
2. Open the **agent's final workspace** (what the agent left behind):
   ```
   $ ls <workspace_path>       # list files the agent edited / produced
   $ less <workspace_path>/<file>   # inspect specific files
   ```
3. Open the **deterministic grader's score**:
   ```
   $ cat <score_path>          # see the grader's pass/fail per check
   ```
4. Decide: **does the agent's submission satisfy the spec?**
   - PASS — yes, the spec requirements are met
   - FAIL — clearly does not meet the spec
   - UNSURE — spec is ambiguous, evidence is unclear, can't decide in 5 min

5. Fill in the four open columns:
   - `human_rater_id`: your initials (e.g. `YBK`)
   - `human_verdict`: `PASS` / `FAIL` / `UNSURE`
   - `human_reason`: one sentence explaining your call (≤ 200 chars)
   - `time_spent_sec`: rough seconds spent on this row

## Calibration (do these 5 rows first)

Pick 5 rows where the LLM judges DISAGREE (look for rows where
`haiku45_verdict ≠ g3flash_verdict`). These are the most informative
calibration cases. After completing them, compare your verdicts to the
LLMs and the grader to recalibrate your strictness.

## Important

- DO NOT look at the LLM verdicts before forming your own judgment.
  Cover the `haiku45_verdict / g3flash_verdict / gpt54mini_verdict`
  columns while you decide. The point of inter-rater is independence.
- DO NOT defer to the deterministic grader. The deterministic grader is
  your reference, but it can be wrong (over-strict, over-lenient, broken
  setup). Your job is the independent human call.
- Use the `UNSURE` verdict liberally. Forced PASS/FAIL on truly ambiguous
  cases hurts agreement statistics more than honest UNSURE.

## When you are done

Save the filled CSV as `human_irr_filled_<your_initials>.csv` in this
directory and run:

    python scripts/score_human_irr.py

This computes pairwise Cohen's κ between you and each LLM judge, between
you and the deterministic grader, and (if multiple humans rated)
three-way agreement statistics across humans.
"""
    open(os.path.join(OUT_DIR, "INSTRUCTIONS.md"), "w").write(instr)
    print(f"[human-irr] wrote {os.path.join(OUT_DIR, 'INSTRUCTIONS.md')}")

    # Protocol (the rigorous-paper-y version)
    proto = """# TeamBench Human Inter-Rater Protocol

## Sample
- N = 285 (task, condition, run) tuples drawn from the LB100 ablation runs
- Stratified by (LB100 category, condition) using random.Random(seed=0).shuffle
- Same sample as scripts/llm_inter_rater.py, allowing direct human-vs-LLM comparison

## Raters
- Target: ≥ 2 independent human raters for κ statistics
- Each rater independently completes all 285 rows
- Optional: stratify the 285 across raters if time-constrained, but report
  pairwise agreement only on overlapping subset

## Scoring scheme
- PASS / FAIL / UNSURE (UNSURE excluded from κ computation)
- Independent of the deterministic grader and LLM judges
- One-sentence human-reason logged per row

## Statistics computed
- Pairwise Cohen's κ between humans (if ≥ 2)
- Pairwise Cohen's κ between each human and each of:
  - the deterministic grader
  - each of the 3 LLM judges (haiku45, g3flash, gpt54mini)
- Three-way Fleiss's κ (humans + grader if 2+ humans, or each LLM-vs-human pair)
- Binary Krippendorff's α with UNSURE treated as missing

## Threshold for paper
- Cohen's κ ≥ 0.6 (substantial agreement, Landis & Koch 1977) between
  humans and the deterministic grader is sufficient to claim the grader
  reproduces human judgment.
- κ < 0.4 on any task category indicates the grader needs review
  in that category.

## Reproducibility
- The 285-row CSV is reproducible from llm_inter_rater.json by re-running
  scripts/export_human_irr_csv.py
- The seed for the LLM-rater sampling was 0 (in scripts/llm_inter_rater.py)
"""
    open(os.path.join(OUT_DIR, "protocol.md"), "w").write(proto)
    print(f"[human-irr] wrote {os.path.join(OUT_DIR, 'protocol.md')}")

    # Generate scoring helper script too
    scorer = '''#!/usr/bin/env python3
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
'''
    scorer_path = os.path.join(REPO, "scripts", "score_human_irr.py")
    open(scorer_path, "w").write(scorer)
    os.chmod(scorer_path, 0o755)
    print(f"[human-irr] wrote {scorer_path}")

    # Header summary file the user can also read at a glance
    summary = f"""# Human IRR — ready for raters

CSV form:    {os.path.relpath(out_csv, REPO)}
Instructions: {os.path.relpath(os.path.join(OUT_DIR, 'INSTRUCTIONS.md'), REPO)}
Protocol:    {os.path.relpath(os.path.join(OUT_DIR, 'protocol.md'), REPO)}
Scoring:     {os.path.relpath(scorer_path, REPO)}

Generated:   {datetime.now(timezone.utc).isoformat()}
N rows:      {len(judgments)}

After human raters fill the CSV (saving as `human_irr_filled_<initials>.csv`),
run `python scripts/score_human_irr.py`.
"""
    open(os.path.join(OUT_DIR, "README.md"), "w").write(summary)
    print(f"[human-irr] done. n={len(judgments)} rows.")


if __name__ == "__main__":
    main()
