#!/usr/bin/env python3
"""LLM-as-rater inter-rater agreement on TeamBench grader decisions.

For each sampled (task, condition, run) tuple:
  - Read the post-run workspace state and the deterministic grader's
    score.json from the run directory.
  - Send the task spec, the run's verifier attestation (if any), the
    final workspace summary, and the grader's pass/fail call to three
    OpenRouter judges (Claude Haiku 4.5, Gemini-3 Flash, GPT-5.4 Mini).
  - Each judge independently decides PASS / FAIL with a one-sentence reason.
  - Compute pairwise Cohen's kappa across judges, three-way Fleiss kappa,
    Krippendorff's alpha (binary), and per-judge agreement with the
    deterministic grader as the reference.

Outputs:
  - shared/paper/teambench_quality/llm_inter_rater.json (raw judgments)
  - shared/paper/teambench_quality/llm_inter_rater_summary.md (table)

Sample design:
  - Stratify on (LB100 category, condition).
  - Default n=300, 5 conditions × ~60 per condition.
  - Skip tuples whose run_dir is missing or whose grader output is malformed.

Usage:
  python scripts/llm_inter_rater.py --n 300
  python scripts/llm_inter_rater.py --n 50 --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
import urllib.request
import urllib.error
from collections import defaultdict, Counter
from datetime import datetime, timezone

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ABL = os.path.join(REPO, "shared/ablation_results")
RUNS = os.path.join(ABL, "ablation_runs")
TASKS = os.path.join(REPO, "tasks")
OUT_DIR = os.path.join(REPO, "shared/paper/teambench_quality")
os.makedirs(OUT_DIR, exist_ok=True)

OR_KEY = os.environ.get("OPENROUTER_API") or os.environ.get("OPENROUTER_API_KEY")
OR_URL = "https://openrouter.ai/api/v1/chat/completions"

JUDGES = [
    ("haiku45",   "anthropic/claude-haiku-4.5"),
    ("g3flash",   "google/gemini-3-flash-preview"),
    ("gpt54mini", "openai/gpt-5.4-mini"),
]

JUDGE_PROMPT_WITH_VERDICT = """You are an impartial software-engineering judge. Decide whether the agent's submission satisfies the task requirements stated in the spec.

You will receive: the task specification, a summary of files the agent left in the workspace, the verifier-attestation file the agent wrote (if any), and the deterministic grader's per-check verdict.  Use only this evidence.

Reply on the FIRST line with exactly one token, PASS or FAIL.  On the second line give a one-sentence justification under 120 characters.  Do not output anything else.
"""

JUDGE_PROMPT_NO_VERDICT = """You are an impartial software-engineering judge. Decide whether the agent's submission satisfies the task requirements stated in the spec.

You will receive: the task specification, a summary of files the agent left in the workspace, and the verifier-attestation file the agent wrote (if any).  Use only this evidence.  You will not see the deterministic grader's verdict; form your own judgment.

Reply on the FIRST line with exactly one token, PASS or FAIL.  On the second line give a one-sentence justification under 120 characters.  Do not output anything else.
"""

USER_TEMPLATE_WITH_VERDICT = """## Task spec
{spec}

## Workspace summary (key files modified)
{workspace}

## Verifier attestation
{attestation}

## Deterministic grader verdict
{grader_verdict}
"""

USER_TEMPLATE_NO_VERDICT = """## Task spec
{spec}

## Workspace summary (key files modified)
{workspace}

## Verifier attestation
{attestation}
"""

# Backward-compatible aliases for the original behaviour.
JUDGE_PROMPT = JUDGE_PROMPT_WITH_VERDICT
USER_TEMPLATE = USER_TEMPLATE_WITH_VERDICT


def list_run_pass_records():
    """Yield {task_id, condition, run_dir, model, partial_score, pass} for every run we know about."""
    if not os.path.isdir(ABL):
        return
    for fn in sorted(os.listdir(ABL)):
        if not fn.startswith("lb100_"):
            continue
        if any(s in fn for s in ("invalid", "archived", "pre_", ".bak")):
            continue
        path = os.path.join(ABL, fn)
        if not os.path.isfile(path):
            continue
        if fn.endswith(".json"):
            try:
                d = json.load(open(path))
            except Exception:
                continue
            model = d.get("model") if isinstance(d, dict) else None
            records = d.get("runs", []) if isinstance(d, dict) else []
        elif fn.endswith(".checkpoint.jsonl"):
            model = None
            records = []
            for line in open(path):
                try:
                    records.append(json.loads(line))
                except Exception:
                    continue
        else:
            continue
        for r in records:
            if not isinstance(r, dict):
                continue
            yield {
                "task_id": r.get("task_id") or r.get("task"),
                "condition": r.get("condition"),
                "run_dir": r.get("run_dir"),
                "model": r.get("model") or model or fn,
                "partial_score": r.get("partial_score"),
                "pass": bool(r.get("pass") or r.get("passed")),
            }


def load_lb100_categories():
    p = os.path.join(REPO, "leaderboard/data/leaderboard_100_tasks.json")
    if not os.path.isfile(p):
        return {}
    d = json.load(open(p))
    out = {}
    for t in d.get("tasks", []):
        if isinstance(t, dict):
            out[t["task_id"]] = t.get("category", "?")
        else:
            out[t] = "?"
    return out


def stratified_sample(records, n, seed=0):
    cat_map = load_lb100_categories()
    by_strata = defaultdict(list)
    for r in records:
        cat = cat_map.get(r["task_id"], "?")
        if cat == "?":
            continue                         # restrict to LB100 only
        if not r.get("run_dir"):
            continue
        by_strata[(cat, r["condition"])].append(r)
    rng = random.Random(seed)
    strata = sorted(by_strata)
    n_strata = len(strata)
    if n_strata == 0:
        return []
    per_stratum = max(1, n // n_strata)
    out = []
    for s in strata:
        bucket = by_strata[s][:]
        rng.shuffle(bucket)
        out.extend(bucket[:per_stratum])
    rng.shuffle(out)
    return out[:n]


def _read_text(p, max_len=8000):
    try:
        with open(p, errors="replace") as f:
            t = f.read()
        return t[:max_len]
    except Exception:
        return ""


def gather_evidence(rec):
    """Build the prompt evidence dict from a run record's run_dir on disk."""
    task_id = rec["task_id"]
    spec_path = os.path.join(TASKS, task_id, "spec.md")
    spec = _read_text(spec_path, max_len=4000)

    rd = rec.get("run_dir") or ""
    if rd and not os.path.isabs(rd):
        rd = os.path.join(REPO, rd)

    # Workspace summary: list edited file paths + first 60 lines each
    ws_path = os.path.join(rd, "workspace") if rd else ""
    workspace_summary = "(no workspace artifacts)"
    if os.path.isdir(ws_path):
        files = []
        for root, _, fs in os.walk(ws_path):
            for f in fs:
                files.append(os.path.relpath(os.path.join(root, f), ws_path))
        files = sorted(files)[:30]
        chunks = []
        for f in files:
            chunks.append(f"### {f}\n{_read_text(os.path.join(ws_path, f), max_len=1500)}\n")
        workspace_summary = "".join(chunks)[:8000]

    # Attestation
    att_path = os.path.join(rd, "reports", "attestation.json") if rd else ""
    attestation = _read_text(att_path, max_len=1500) if os.path.isfile(att_path) else "(no attestation)"

    # Grader verdict
    score_path = os.path.join(rd, "reports", "score.json") if rd else ""
    grader_verdict = _read_text(score_path, max_len=1500) if os.path.isfile(score_path) else "(no score.json)"

    return {
        "spec": spec,
        "workspace": workspace_summary,
        "attestation": attestation,
        "grader_verdict": grader_verdict,
    }


def call_judge(model_slug, messages, timeout=60):
    body = {
        "model": model_slug,
        "messages": messages,
        "max_tokens": 80,
        "temperature": 0,
    }
    req = urllib.request.Request(
        OR_URL,
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {OR_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/teambench/teambench",
            "X-Title": "TeamBench LLM inter-rater",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode())
        out = data["choices"][0]["message"]["content"].strip()
        return out, None
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:300]
        return None, f"http_{e.code}: {body}"
    except Exception as e:
        return None, f"err: {e}"


def parse_verdict(text):
    if not text:
        return None, ""
    first = text.strip().splitlines()[0].strip().upper().rstrip(".:")
    reason = text.strip().splitlines()[1].strip()[:200] if "\n" in text else ""
    if first.startswith("PASS"):
        return "PASS", reason
    if first.startswith("FAIL"):
        return "FAIL", reason
    return None, reason


# ---------------------------------------------------------------------------
# Agreement statistics
# ---------------------------------------------------------------------------

def cohen_kappa(a, b):
    n = len(a)
    if n == 0:
        return float("nan")
    cats = sorted(set(a) | set(b))
    obs = sum(1 for x, y in zip(a, b) if x == y) / n
    pe = 0.0
    for c in cats:
        pa = sum(1 for x in a if x == c) / n
        pb = sum(1 for x in b if x == c) / n
        pe += pa * pb
    if pe == 1:
        return 1.0
    return round((obs - pe) / (1 - pe), 4)


def fleiss_kappa(matrix):
    """matrix: list of [n_pass, n_fail] per item across raters."""
    if not matrix:
        return float("nan")
    n = len(matrix)
    n_raters = sum(matrix[0])
    if n_raters < 2:
        return float("nan")
    p_j = [sum(row[j] for row in matrix) / (n * n_raters) for j in range(2)]
    Pe = sum(p ** 2 for p in p_j)
    Pi = [(sum(c ** 2 for c in row) - n_raters) / (n_raters * (n_raters - 1)) for row in matrix]
    P = sum(Pi) / n
    if Pe == 1:
        return 1.0
    return round((P - Pe) / (1 - Pe), 4)


def krippendorff_alpha_binary(judgments):
    """Binary Krippendorff alpha: judgments is list of [list of judge labels per item]."""
    if not judgments:
        return float("nan")
    pairs = []
    for js in judgments:
        present = [x for x in js if x in ("PASS", "FAIL")]
        for i in range(len(present)):
            for j in range(i + 1, len(present)):
                pairs.append((present[i], present[j]))
    if not pairs:
        return float("nan")
    Do = sum(1 for x, y in pairs if x != y) / len(pairs)
    flat = [x for js in judgments for x in js if x in ("PASS", "FAIL")]
    n_pass = flat.count("PASS")
    n_fail = flat.count("FAIL")
    if n_pass + n_fail < 2:
        return float("nan")
    De_n = 2 * n_pass * n_fail
    De_d = (n_pass + n_fail) * (n_pass + n_fail - 1)
    De = De_n / De_d
    if De == 0:
        return 1.0
    return round(1.0 - (Do / De), 4)


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-verdict", action="store_true",
                    help="Hide the deterministic grader verdict from the judge prompt. "
                         "Run this to produce a leakage-free version of the audit.")
    ap.add_argument("--out", default=None,
                    help="Default depends on --no-verdict.")
    ap.add_argument("--summary-out", default=None,
                    help="Default depends on --no-verdict.")
    ap.add_argument("--throttle-sec", type=float, default=0.2)
    ap.add_argument("--budget-usd", type=float, default=80.0,
                    help="Soft cap; estimated cost at 1500 tokens-in/100 tokens-out per judge.")
    args = ap.parse_args()

    if args.out is None:
        args.out = os.path.join(
            OUT_DIR,
            "llm_inter_rater_no_verdict.json" if args.no_verdict
            else "llm_inter_rater.json",
        )
    if args.summary_out is None:
        args.summary_out = os.path.join(
            OUT_DIR,
            "llm_inter_rater_no_verdict_summary.md" if args.no_verdict
            else "llm_inter_rater_summary.md",
        )

    judge_prompt = JUDGE_PROMPT_NO_VERDICT if args.no_verdict else JUDGE_PROMPT_WITH_VERDICT
    user_template = USER_TEMPLATE_NO_VERDICT if args.no_verdict else USER_TEMPLATE_WITH_VERDICT
    print(f"[llm-rater] mode = {'NO-VERDICT (leakage-free)' if args.no_verdict else 'with-verdict'}")

    if not OR_KEY and not args.dry_run:
        print("ERROR: OPENROUTER_API not set in environment.", file=sys.stderr)
        sys.exit(1)

    print(f"[llm-rater] sampling {args.n} (task, condition, run) tuples (seed={args.seed})")
    records = list(list_run_pass_records())
    print(f"[llm-rater] total run records available: {len(records):,}")

    sample = stratified_sample(records, args.n, seed=args.seed)
    print(f"[llm-rater] sampled {len(sample)} tuples after stratification + run_dir filter")

    if args.dry_run:
        for r in sample[:10]:
            print("  ", r["task_id"], r["condition"], r["run_dir"], "pass=", r["pass"])
        print("[llm-rater] dry run; exiting")
        return

    # Resume
    judgments = []
    seen_run_ids = set()
    if os.path.isfile(args.out):
        try:
            old = json.load(open(args.out))["judgments"]
            judgments = old
            seen_run_ids = {(j["task_id"], j["condition"], j["run_dir"]) for j in old}
            print(f"[llm-rater] resuming; {len(judgments)} prior judgments")
        except Exception:
            pass

    cost_used = 0.0
    t0 = time.time()
    for i, rec in enumerate(sample, 1):
        key = (rec["task_id"], rec["condition"], rec["run_dir"])
        if key in seen_run_ids:
            continue
        ev = gather_evidence(rec)
        user_msg = user_template.format(**ev)[:14000]
        messages = [
            {"role": "system", "content": judge_prompt},
            {"role": "user", "content": user_msg},
        ]
        per_judge = {}
        for jname, jslug in JUDGES:
            text, err = call_judge(jslug, messages)
            verdict, reason = parse_verdict(text) if text else (None, err or "")
            per_judge[jname] = {
                "raw": text, "verdict": verdict, "reason": reason, "error": err,
                "model_slug": jslug,
            }
            time.sleep(args.throttle_sec)

        # Cost guess: assume ~5000 tokens in, ~50 out per judge; rough $0.04 per call avg
        cost_used += 0.04 * len(JUDGES)
        judgments.append({
            "task_id": rec["task_id"],
            "condition": rec["condition"],
            "run_dir": rec["run_dir"],
            "model": rec["model"],
            "grader_pass": bool(rec["pass"]),
            "grader_partial": rec.get("partial_score"),
            "judges": per_judge,
        })

        if i % 5 == 0 or i == len(sample):
            elapsed = time.time() - t0
            rate = i / elapsed if elapsed > 0 else 0
            print(f"[{i:>4}/{len(sample)}] {rec['task_id']:<35} {rec['condition']:<20} "
                  f"verdicts={[per_judge[j]['verdict'] for j,_ in JUDGES]} "
                  f"cost~${cost_used:.2f} ({rate:.1f}/s)")
            json.dump({"computed_at": datetime.now(timezone.utc).isoformat(),
                       "n": len(judgments), "judges": [j for j, _ in JUDGES],
                       "judgments": judgments,
                       "estimated_cost_usd": round(cost_used, 2)},
                      open(args.out, "w"), indent=2)

        if cost_used > args.budget_usd:
            print(f"[llm-rater] budget cap ${args.budget_usd} hit; stopping early")
            break

    # ---------- Compute agreement statistics ----------
    valid = [j for j in judgments if all(
        j["judges"][n]["verdict"] in ("PASS", "FAIL") for n, _ in JUDGES)]
    print(f"[llm-rater] valid judgments (all 3 judges produced verdict): {len(valid)} of {len(judgments)}")

    summary = {"n_judged": len(judgments), "n_valid": len(valid)}
    judge_names = [n for n, _ in JUDGES]

    # Pairwise Cohen kappa
    pair_kappas = {}
    for i in range(len(judge_names)):
        for j in range(i + 1, len(judge_names)):
            a = [v["judges"][judge_names[i]]["verdict"] for v in valid]
            b = [v["judges"][judge_names[j]]["verdict"] for v in valid]
            pair_kappas[f"{judge_names[i]}__vs__{judge_names[j]}"] = cohen_kappa(a, b)

    # Fleiss kappa
    matrix = []
    for v in valid:
        labels = [v["judges"][n]["verdict"] for n in judge_names]
        matrix.append([labels.count("PASS"), labels.count("FAIL")])
    fk = fleiss_kappa(matrix)

    # Krippendorff alpha (binary)
    judg_lists = [[v["judges"][n]["verdict"] for n in judge_names] for v in valid]
    kalpha = krippendorff_alpha_binary(judg_lists)

    # Each judge vs deterministic grader
    judge_vs_grader = {}
    for n in judge_names:
        judge_pass_when_grader_pass = sum(1 for v in valid if v["grader_pass"] and v["judges"][n]["verdict"] == "PASS")
        judge_pass_when_grader_fail = sum(1 for v in valid if not v["grader_pass"] and v["judges"][n]["verdict"] == "PASS")
        judge_fail_when_grader_pass = sum(1 for v in valid if v["grader_pass"] and v["judges"][n]["verdict"] == "FAIL")
        judge_fail_when_grader_fail = sum(1 for v in valid if not v["grader_pass"] and v["judges"][n]["verdict"] == "FAIL")
        n_total = max(1, len(valid))
        judge_vs_grader[n] = {
            "agreement": round((judge_pass_when_grader_pass + judge_fail_when_grader_fail) / n_total, 4),
            "false_accept": round(judge_pass_when_grader_fail / max(1, judge_pass_when_grader_fail + judge_fail_when_grader_fail), 4),
            "false_reject": round(judge_fail_when_grader_pass / max(1, judge_pass_when_grader_pass + judge_fail_when_grader_pass), 4),
            "kappa_vs_grader": cohen_kappa(
                [v["grader_pass"] for v in valid],
                [v["judges"][n]["verdict"] == "PASS" for v in valid],
            ),
        }

    summary.update({
        "pair_kappas": pair_kappas,
        "fleiss_kappa_3way": fk,
        "krippendorff_alpha_binary": kalpha,
        "judge_vs_deterministic_grader": judge_vs_grader,
    })

    payload = {
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "n": len(judgments),
        "judges": judge_names,
        "summary": summary,
        "estimated_cost_usd": round(cost_used, 2),
        "judgments": judgments,
    }
    json.dump(payload, open(args.out, "w"), indent=2)
    print(f"[llm-rater] wrote {args.out}")

    # Markdown summary
    md = ["# LLM Inter-Rater Agreement on TeamBench Graders", ""]
    md.append(f"_Computed {datetime.now(timezone.utc).isoformat()}, n_judgments={len(judgments)}, n_valid={len(valid)}._")
    md.append(f"_Estimated OpenRouter spend ≈ ${round(cost_used, 2)}._")
    md.append("")
    md.append("## Pairwise Cohen's κ between judges")
    md.append("| Pair | κ |")
    md.append("|---|---|")
    for k, v in pair_kappas.items():
        md.append(f"| {k.replace('__vs__', ' vs ')} | {v} |")
    md.append("")
    md.append(f"**Three-way Fleiss's κ**: {fk}")
    md.append(f"**Binary Krippendorff's α**: {kalpha}")
    md.append("")
    md.append("## Each LLM judge vs deterministic grader (reference)")
    md.append("| Judge | agreement | κ vs grader | LLM-pass when grader=fail | LLM-fail when grader=pass |")
    md.append("|---|---|---|---|---|")
    for n, st in judge_vs_grader.items():
        md.append(f"| {n} | {st['agreement']} | {st['kappa_vs_grader']} | {st['false_accept']} | {st['false_reject']} |")
    open(args.summary_out, "w").write("\n".join(md) + "\n")
    print(f"[llm-rater] wrote {args.summary_out}")


if __name__ == "__main__":
    main()
