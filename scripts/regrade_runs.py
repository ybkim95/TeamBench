#!/usr/bin/env python3
"""Re-grade existing ablation runs with fixed graders.

Walks runs in checkpoint.jsonl, re-runs grade.sh on each run_dir,
and updates pass/partial_score. Checkpoint is rewritten in place.

Per-grader timeout is 90s (enforced in harness/run_all.py:grade_run).
"""
import argparse, json, os, sys, time
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))
os.chdir(Path(__file__).parent.parent.resolve())

from harness.run_all import grade_run

RESULTS_DIR = Path("shared/ablation_results")


def regrade_model(model_short: str, dry_run: bool = False, verbose: bool = True):
    # Accept both 5-condition (lb100_<m>_seed0.json) and 2-condition (lb100_<m>_oraclefull_seed0.json) files
    for suffix in (f"lb100_{model_short}_seed0.json", f"lb100_{model_short}_oraclefull_seed0.json"):
        ckpt = RESULTS_DIR / f"{suffix}.checkpoint.jsonl"
        final = RESULTS_DIR / suffix
        if ckpt.exists() or final.exists():
            break

    runs = []
    if ckpt.exists():
        for line in ckpt.read_text().splitlines():
            if line.strip():
                runs.append(json.loads(line))
    elif final.exists():
        d = json.loads(final.read_text())
        runs = d.get("runs", d.get("all_runs", []))

    if not runs:
        print(f"  [skip] {model_short}: no runs")
        return

    from concurrent.futures import ThreadPoolExecutor, as_completed
    print(f"  [{model_short}] {len(runs)} runs (parallel=16)", flush=True)
    t0 = time.time()
    changed = 0
    missing = 0
    done = 0

    def _grade_one(r):
        rd = r.get("run_dir")
        tid = r.get("task_id")
        if not rd or not os.path.isdir(rd):
            return ("missing", r, None)
        seed = r.get("seed", 0)
        candidates = [f"tasks/{tid}_seed{seed}", f"tasks/{tid}"]
        task_dir = next((c for c in candidates if os.path.isdir(c)), f"tasks/{tid}")
        try:
            return ("ok", r, grade_run(tid, task_dir, rd))
        except Exception as e:
            return ("err", r, str(e))

    with ThreadPoolExecutor(max_workers=16) as ex:
        futures = [ex.submit(_grade_one, r) for r in runs]
        for fut in as_completed(futures):
            kind, r, payload = fut.result()
            done += 1
            if kind == "missing":
                missing += 1
            elif kind == "ok":
                old_pass = r.get("pass", False)
                old_partial = r.get("partial_score", 0.0)
                new_pass = bool(payload.get("pass", False))
                new_partial = float(payload.get("secondary", {}).get("partial_score",
                                                                      1.0 if new_pass else 0.0))
                if new_pass != old_pass or abs(new_partial - old_partial) > 0.01:
                    changed += 1
                    r["pass"] = new_pass
                    r["partial_score"] = new_partial
                    r["failure_modes"] = payload.get("failure_modes", [])
            if verbose and done % 25 == 0:
                elapsed = time.time() - t0
                rate = done / elapsed
                eta = (len(runs) - done) / rate if rate else 0
                print(f"    {done}/{len(runs)}  changed={changed}  ETA {eta:.0f}s", flush=True)

    print(f"  [{model_short}] done: changed={changed}, missing_rundir={missing}, {time.time()-t0:.0f}s", flush=True)

    if dry_run:
        return

    # Rewrite checkpoint
    if ckpt.exists():
        with open(ckpt, "w") as f:
            for r in runs:
                f.write(json.dumps(r) + "\n")

    # Rebuild per_condition summary in final
    if final.exists():
        d = json.loads(final.read_text())
        pc = defaultdict(lambda: {"passes": 0, "total": 0, "partial_sum": 0.0})
        for r in runs:
            c = r.get("condition")
            if not c: continue
            pc[c]["total"] += 1
            if r["pass"]: pc[c]["passes"] += 1
            pc[c]["partial_sum"] += r.get("partial_score", 0.0)
        d["per_condition"] = {
            c: {
                "passes": v["passes"],
                "total": v["total"],
                "success_rate": v["passes"] / v["total"] if v["total"] else 0.0,
                "mean_partial": v["partial_sum"] / v["total"] if v["total"] else 0.0,
            }
            for c, v in pc.items()
        }
        if "runs" in d: d["runs"] = runs
        if "all_runs" in d: d["all_runs"] = runs
        final.write_text(json.dumps(d, indent=2))


def list_models():
    models = set()
    for p in RESULTS_DIR.glob("lb100_*_seed0.json"):
        n = p.name
        if n == "lb100_v1_seed0.json": continue
        # Strip both _oraclefull and plain suffix
        m = n.replace("lb100_", "").replace("_oraclefull_seed0.json", "").replace("_seed0.json", "")
        models.add(m)
    for p in RESULTS_DIR.glob("lb100_*_seed0.json.checkpoint.jsonl"):
        n = p.name
        m = n.replace("lb100_", "").replace("_oraclefull_seed0.json.checkpoint.jsonl", "").replace("_seed0.json.checkpoint.jsonl", "")
        models.add(m)
    return sorted(models)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", help="Model short name")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    targets = list_models() if args.all else ([args.model] if args.model else [])
    if not targets:
        print("Models with data:")
        for m in list_models():
            print(f"  {m}")
        return
    for m in targets:
        regrade_model(m, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
