#!/usr/bin/env python3
"""
G3 reference-solution sweep
===========================

    python3 scripts/g3_reference_sweep.py --bootstrap --workers 8

Gate G3 of ``scripts/task_admission_gate.py`` asks the SWE-bench-Verified
question: **does a known-correct solution pass the task's own grader?**  This
script asks it of every task that has an authoritative upstream reference patch
at ``tasks/<id>/reference/patch.diff``, rather than only of the 150 tasks in the
admission gate's default scope.

It reports the three-way split that the question actually has:

  (a) ``a_validated``               the reference applies and the grader gives 1.0.
                                    The task is anchored to ground truth.
  (b) ``b_grader_rejects_reference``the reference applies and the grader does NOT
                                    give 1.0.  The grader disagrees with the fix
                                    the upstream maintainers merged.  This is a
                                    grader defect, and it is the scientifically
                                    interesting bucket: it is a measurement of
                                    how often a checklist grader mis-scores a
                                    correct solution.
  (c) ``c_unappliable``             the reference cannot be applied by any method
                                    in harness/reference_apply.py.  The task has
                                    lost its link to ground truth and nothing can
                                    be concluded about its grader.

Two grades are run per task: the pristine staged workspace (the G1 floor, needed
to tell a reference that changed nothing from a grader that ignores the change)
and the reference workspace.  For bucket (b) the per-check statuses of both are
recorded, so the exact checks the upstream fix fails are in the ledger.

Outputs, all under ``shared/paper/quality/``:
    g3_reference_ledger.json      per-task records + summary
    g3_reference_summary.md       the tables for the paper
    g3_reference_checkpoint.jsonl append-only, makes the run resumable

Grading environment: identical to the admission gate.  ``--bootstrap`` builds a
throwaway venv that reads the repo venv's site-packages through a .pth file, so
the many graders that run ``pip install`` at grade time cannot mutate the repo
venv from eight concurrent workers.
"""
from __future__ import annotations

import argparse
import glob
import importlib.util
import json
import os
import shutil
import sys
import threading
import time
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

OUT_DIR = os.path.join(REPO_ROOT, "shared", "paper", "quality")
LEDGER_PATH = os.path.join(OUT_DIR, "g3_reference_ledger.json")
SUMMARY_PATH = os.path.join(OUT_DIR, "g3_reference_summary.md")
CHECKPOINT_PATH = os.path.join(OUT_DIR, "g3_reference_checkpoint.jsonl")

MAX_WORKERS = 8


def _load_gate():
    """Import scripts/task_admission_gate.py as a module (scripts/ is not a package)."""
    path = os.path.join(REPO_ROOT, "scripts", "task_admission_gate.py")
    spec = importlib.util.spec_from_file_location("teambench_admission_gate", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["teambench_admission_gate"] = mod
    spec.loader.exec_module(mod)
    return mod


GATE = _load_gate()


def _pip_shim_info(bindir: str) -> dict | None:
    """Describe the pip on the grader's PATH when it is the sweep's shim.

    Graders begin with `pip install pytest -q`. On an NFS user site-packages
    tree real pip spends ~96 s of IO wait to conclude "Requirement already
    satisfied". The shim short-circuits exactly that case and delegates every
    other invocation to real pip. Recorded here, with its call log, so a reader
    can check how often it fired and what it delegated.
    """
    pip = os.path.join(bindir, "pip")
    try:
        with open(pip, encoding="utf-8", errors="replace") as f:
            head = f.read(400)
    except OSError:
        return None
    if "pip shim used only by the G3 reference sweep" not in head:
        return None
    log = os.environ.get("TB_PIP_SHIM_LOG", os.path.join(
        os.path.dirname(bindir), "pip_shim.log"))
    kinds: dict[str, int] = {}
    try:
        with open(log, encoding="utf-8") as f:
            for line in f:
                try:
                    kinds[json.loads(line)["kind"]] = kinds.get(
                        json.loads(line)["kind"], 0) + 1
                except Exception:
                    continue
    except OSError:
        pass
    return {"path": pip, "log": log, "calls": kinds}


def tasks_with_reference() -> list[str]:
    out = []
    for p in glob.glob(os.path.join(REPO_ROOT, "tasks", "*", "reference", "patch.diff")):
        tid = os.path.basename(os.path.dirname(os.path.dirname(p)))
        if os.path.isfile(os.path.join(REPO_ROOT, "tasks", tid, "grade.sh")):
            out.append(tid)
    return sorted(out)


# Workers are PROCESSES, not threads.
#
# Per task this sweep runs the task generator three times (twice to stage, once
# more inside the applier's control run) plus a replay, and generation is
# CPU-bound pure Python: tokenising and rewriting every source file in the
# workspace. Under a thread pool the GIL serialised all of that, and
# harness.run_all's staging lock serialised staging on top of it, so eight
# "workers" delivered about one task per minute regardless of how many cores
# were free. Processes give the generators real parallelism.
#
# The one piece of shared state that must survive the switch is the lock that
# serialises graders which write to a FIXED /tmp path (see
# task_admission_gate.fixed_tmp_paths). A threading.Lock in each child would
# protect nothing, so a multiprocessing lock is handed to every worker by the
# pool initialiser.
_TMP_LOCK = None


def _init_worker(lock) -> None:
    global _TMP_LOCK
    _TMP_LOCK = lock


def evaluate(task_id: str, cfg: dict) -> dict:
    from harness.reference_apply import build_reference_workspace

    task_dir = os.path.join(REPO_ROOT, "tasks", task_id)
    run_root = os.path.join(cfg["workdir"], "runs")
    timeout_s = cfg["grade_timeout"]
    tmp_paths = GATE.fixed_tmp_paths(os.path.join(task_dir, "grade.sh"))

    rec: dict = {
        "task_id": task_id,
        "family": GATE.task_family(task_id),
        "seed": cfg["seed"],
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "grade_sh_sha256": GATE.file_sha256(os.path.join(task_dir, "grade.sh")),
        "concurrency_unsafe": bool(tmp_paths),
        "errors": [],
    }

    # ---- pristine floor -------------------------------------------------
    run_a = None
    try:
        run_a, task_dir_a = GATE.stage(task_id, run_root, cfg["seed"])
        with GATE._MaybeLock(_TMP_LOCK or GATE._FIXED_TMP_LOCK, bool(tmp_paths)):
            score_a, el_a, to_a = GATE.invoke_grader(task_id, task_dir_a, run_a, timeout_s)
        rec["pristine"] = {
            "partial_score": GATE.partial_of(score_a),
            "pass": bool(score_a.get("pass")),
            "grade_seconds": round(el_a, 2),
            "timed_out": to_a,
        }
        st_a = GATE.checklist_statuses(GATE.checklist_of(score_a))
    except Exception as exc:
        rec["errors"].append(f"pristine: {type(exc).__name__}: {exc}")
        rec["pristine"] = None
        st_a = None
    finally:
        if run_a and not cfg["keep_runs"]:
            shutil.rmtree(run_a, ignore_errors=True)

    # ---- reference ------------------------------------------------------
    run_c = None
    try:
        run_c, task_dir_c = GATE.stage(task_id, run_root, cfg["seed"])
        ws = os.path.join(run_c, "workspace")
        t0 = time.monotonic()
        appl = build_reference_workspace(task_id, task_dir_c, ws, seed=cfg["seed"])
        rec["apply_seconds"] = round(time.monotonic() - t0, 2)
        rec["application"] = {k: appl.get(k) for k in (
            "applied", "method", "base_source", "hunks_total", "hunks_applied",
            "hunks_already", "hunks_failed", "files_total", "files_applied",
            "files_already", "files_failed", "files_out_of_scope",
            "files_unsupported", "no_effective_change", "notes", "written_paths")}
        rec["file_outcomes"] = appl.get("file_outcomes", [])[:24]

        if not appl["applied"]:
            rec["outcome"] = "c_unappliable"
            rec["reference"] = None
        else:
            with GATE._MaybeLock(_TMP_LOCK or GATE._FIXED_TMP_LOCK, bool(tmp_paths)):
                score_c, el_c, to_c = GATE.invoke_grader(task_id, task_dir_c, run_c, timeout_s)
            ref_partial = GATE.partial_of(score_c)
            ref_pass = bool(score_c.get("pass"))
            rec["reference"] = {
                "partial_score": ref_partial,
                "pass": ref_pass,
                "grade_seconds": round(el_c, 2),
                "timed_out": to_c,
            }
            ok = (ref_partial == 1.0) and ref_pass
            rec["outcome"] = "a_validated" if ok else "b_grader_rejects_reference"
            st_c = GATE.checklist_statuses(GATE.checklist_of(score_c))
            if st_c is not None:
                rec["reference"]["checks_failed_ids"] = sorted(k for k, v in st_c.items() if not v)
                rec["reference"]["checks_total"] = len(st_c)
                rec["reference"]["checks_passed"] = sum(1 for v in st_c.values() if v)
                if st_a is not None:
                    rec["checks_flipped_to_pass"] = sorted(
                        k for k, v in st_a.items() if not v and st_c.get(k))
                    rec["checks_flipped_to_fail"] = sorted(
                        k for k, v in st_a.items() if v and st_c.get(k) is False)
                    rec["checks_free"] = sorted(k for k, v in st_a.items() if v)
            cl = GATE.checklist_of(score_c)
            rec["reference"]["failed_checks"] = [
                {k: e.get(k) for k in ("id", "name", "desc", "description", "detail", "message")
                 if e.get(k) is not None}
                for e in cl if isinstance(e, dict) and GATE.check_status(e) is False][:12]
    except Exception as exc:
        rec["errors"].append(f"reference: {type(exc).__name__}: {exc}")
        rec.setdefault("outcome", "error")
    finally:
        if run_c and not cfg["keep_runs"]:
            shutil.rmtree(run_c, ignore_errors=True)

    p = (rec.get("pristine") or {}).get("partial_score")
    r = (rec.get("reference") or {}).get("partial_score")
    rec["reference_minus_floor"] = (None if (p is None or r is None) else round(r - p, 4))
    return rec


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def normalize_outcome(rec: dict) -> str:
    """Final outcome for one record, including the bucket the first pass missed.

    A grade that hit the 300 s harness cap tells us nothing about whether the
    grader accepts the upstream fix, so it must not be counted as "the grader
    rejects the reference". Those become `d_inconclusive_grader_timeout`.
    Applied here rather than at collection time so that re-summarising an
    existing checkpoint (--summarize-only) reclassifies old records too.
    """
    oc = rec.get("outcome", "error")
    if oc in ("a_validated", "b_grader_rejects_reference"):
        ref = rec.get("reference") or {}
        pri = rec.get("pristine") or {}
        if ref.get("timed_out") or pri.get("timed_out") \
                or ref.get("partial_score") is None:
            return "d_inconclusive_grader_timeout"
    return oc


def summarize(records: list[dict], meta: dict) -> dict:
    for r in records:
        r["outcome"] = normalize_outcome(r)
    from collections import Counter, defaultdict
    n = len(records)
    oc = Counter(r.get("outcome", "error") for r in records)
    meth = Counter((r.get("application") or {}).get("method") for r in records
                   if (r.get("application") or {}).get("applied"))
    base = Counter((r.get("application") or {}).get("base_source") for r in records)
    fam = defaultdict(lambda: Counter())
    for r in records:
        fam[r["family"]][r.get("outcome", "error")] += 1

    ht = sum((r.get("application") or {}).get("hunks_total") or 0 for r in records)
    ha = sum((r.get("application") or {}).get("hunks_applied") or 0 for r in records)
    hl = sum((r.get("application") or {}).get("hunks_already") or 0 for r in records)
    hf = sum((r.get("application") or {}).get("hunks_failed") or 0 for r in records)

    b = [r for r in records if r.get("outcome") == "b_grader_rejects_reference"]
    b_scores = [r["reference"]["partial_score"] for r in b
                if (r.get("reference") or {}).get("partial_score") is not None]
    b_noeffect = sum(1 for r in b if (r.get("application") or {}).get("no_effective_change"))
    b_zero_gain = sum(1 for r in b if r.get("reference_minus_floor") == 0.0)
    b_negative = sum(1 for r in b if (r.get("reference_minus_floor") or 0) < 0)
    failed_ids = Counter()
    for r in b:
        for cid in (r.get("reference") or {}).get("checks_failed_ids", []):
            failed_ids[cid] += 1

    floors = [(r.get("pristine") or {}).get("partial_score") for r in records]
    floors = [f for f in floors if f is not None]

    return {
        "n": n,
        "outcomes": dict(oc),
        "outcome_frac": {k: round(v / n, 4) for k, v in oc.items()} if n else {},
        "apply_methods": dict(meth),
        "base_sources": dict(base),
        "hunks": {"total": ht, "applied": ha, "already_at_post_state": hl, "failed": hf,
                  "reached_post_state_frac": round((ha + hl) / ht, 4) if ht else None},
        "bucket_b": {
            "n": len(b),
            "mean_reference_partial": round(sum(b_scores) / len(b_scores), 4) if b_scores else None,
            "min_reference_partial": min(b_scores) if b_scores else None,
            "max_reference_partial": max(b_scores) if b_scores else None,
            "no_effective_change": b_noeffect,
            "reference_scores_exactly_the_pristine_floor": b_zero_gain,
            "reference_scores_below_the_pristine_floor": b_negative,
            "most_common_failing_check_ids": failed_ids.most_common(15),
        },
        "pristine_floor": {
            "n": len(floors),
            "mean": round(sum(floors) / len(floors), 4) if floors else None,
            "exactly_zero": sum(1 for f in floors if f == 0.0),
        },
        "by_family": {k: dict(v) for k, v in sorted(fam.items())},
        "meta": meta,
    }


def render_markdown(summary: dict, records: list[dict]) -> str:
    L: list[str] = []
    A = L.append
    m = summary["meta"]
    n = summary["n"]
    oc = summary["outcomes"]
    A("# G3: does the upstream reference solution pass the task's own grader?")
    A("")
    wall = (f"{m['wall_seconds']} s wall" if m.get("wall_seconds") is not None
            else "rebuilt from the checkpoint, no grading in this invocation")
    A(f"Generated {m['generated_at']} · commit `{m.get('git_commit')}` · "
      f"branch `{m.get('git_branch')}` · seed {m['seed']} · {m['workers']} workers · "
      f"{wall}.")
    A("")
    A(f"Scope: every task with an authoritative upstream patch at "
      f"`tasks/<id>/reference/patch.diff` and a `grade.sh`. {n} tasks"
      + (f" of {m['scope_size']} scoped." if n != m.get("scope_size") else "."))
    A("")
    A("Applier: `harness/reference_apply.py`. The reference is applied to the "
      "generator's own unparameterised base and the generator's parameterisation "
      "is then replayed on the patched base with the symbol rename map frozen to "
      "the staged instance's map, so what lands in the workspace is the upstream "
      "fix expressed in the seed's identifier space.")
    A("")
    A("## The three-way split")
    A("")
    A("| Outcome | Meaning | Tasks | Share |")
    A("|---|---|---:|---:|")
    rows = [("a_validated", "reference applies and the grader gives 1.0"),
            ("b_grader_rejects_reference", "reference applies, grader does **not** give 1.0"),
            ("c_unappliable", "reference cannot be applied by any method"),
            ("d_inconclusive_grader_timeout",
             "a grade hit the 300 s harness cap: inconclusive, not a rejection"),
            ("error", "probe crashed")]
    for k, desc in rows:
        v = oc.get(k, 0)
        if v or k != "error":
            A(f"| `{k}` | {desc} | {v} | {v/n:.1%} |")
    A("")
    h = summary["hunks"]
    A(f"Hunk-level accounting over the whole corpus: {h['total']} hunks, "
      f"{h['applied']} applied, {h['already_at_post_state']} already at their post state "
      f"(the workspace ships the PR's test files), {h['failed']} unappliable "
      f"({(h['reached_post_state_frac'] or 0):.1%} reached the post state).")
    A("")
    A("## How the reference was applied")
    A("")
    A("| Method | Tasks |")
    A("|---|---:|")
    for k, v in sorted(summary["apply_methods"].items(), key=lambda x: -x[1]):
        A(f"| `{k}` | {v} |")
    A("")
    bb = summary["bucket_b"]
    A("## Bucket (b): the grader disagrees with the upstream fix")
    A("")
    if bb["n"]:
        A(f"{bb['n']} tasks. Mean reference partial score {bb['mean_reference_partial']}, "
          f"range [{bb['min_reference_partial']}, {bb['max_reference_partial']}].")
        A("")
        A(f"- {bb['reference_scores_exactly_the_pristine_floor']} score *exactly* the "
          "pristine do-nothing floor: the grader is blind to the upstream fix.")
        A(f"- {bb['reference_scores_below_the_pristine_floor']} score *below* the pristine "
          "floor: applying the upstream fix loses points.")
        A(f"- {bb['no_effective_change']} produced no effective change in the workspace "
          "(every file the fix touches is out of the workspace's scope).")
        A("")
        A("Most frequently failed check ids among bucket (b):")
        A("")
        A("| Check id | Tasks failing it |")
        A("|---|---:|")
        for cid, cnt in bb["most_common_failing_check_ids"]:
            A(f"| `{cid}` | {cnt} |")
    else:
        A("Empty.")
    A("")
    A("## By family")
    A("")
    keys = ["a_validated", "b_grader_rejects_reference", "c_unappliable",
            "d_inconclusive_grader_timeout", "error"]
    A("| Family | " + " | ".join(f"`{k}`" for k in keys) + " | n |")
    A("|---" * (len(keys) + 2) + "|")
    for famname, d in summary["by_family"].items():
        tot = sum(d.values())
        A(f"| {famname} | " + " | ".join(str(d.get(k, 0)) for k in keys) + f" | {tot} |")
    A("")
    pf = summary["pristine_floor"]
    A(f"Pristine floor over the same {pf['n']} tasks: mean {pf['mean']}, "
      f"exactly zero on {pf['exactly_zero']}.")
    A("")
    A("## Worked examples from bucket (b)")
    A("")
    b = [r for r in records if r.get("outcome") == "b_grader_rejects_reference"]
    b.sort(key=lambda r: ((r.get("reference") or {}).get("partial_score") or 0))
    for r in b[:8]:
        ref = r.get("reference") or {}
        ap = r.get("application") or {}
        A(f"### {r['task_id']}")
        A("")
        A(f"- reference partial **{ref.get('partial_score')}**, "
          f"pristine floor {(r.get('pristine') or {}).get('partial_score')}, "
          f"delta {r.get('reference_minus_floor')}")
        A(f"- applied by `{ap.get('method')}`, "
          f"{ap.get('hunks_applied')} hunks applied / {ap.get('hunks_already')} already / "
          f"{ap.get('hunks_total')} total; files written: "
          f"{', '.join((ap.get('written_paths') or [])[:6]) or 'none'}")
        A(f"- checks the upstream fix fails: "
          f"{', '.join('`%s`' % c for c in ref.get('checks_failed_ids', [])) or 'n/a'}")
        if r.get("checks_flipped_to_fail"):
            A(f"- checks the upstream fix BROKE (passed pristine, fail with the fix): "
              f"{', '.join('`%s`' % c for c in r['checks_flipped_to_fail'])}")
        A("")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workdir", default=None)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--workers", type=int, default=MAX_WORKERS,
                    help=f"Concurrent tasks (default and hard cap {MAX_WORKERS}).")
    ap.add_argument("--grade-timeout", type=int, default=GATE.HARNESS_GRADE_CAP_S)
    ap.add_argument("--tasks", nargs="*", default=None)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--shuffle-seed", type=int, default=None,
                    help="Evaluate the scope in a deterministic random order. A run that "
                         "is cut short is then an unbiased random sample of the corpus "
                         "instead of an alphabetical prefix, which for this corpus means "
                         "a prefix of the GH1xxx block.")
    ap.add_argument("--keep-runs", action="store_true")
    ap.add_argument("--no-resume", action="store_true")
    ap.add_argument("--summarize-only", action="store_true")
    ap.add_argument("--bootstrap", action="store_true")
    ap.add_argument("--allow-shared-venv", action="store_true")
    args = ap.parse_args()

    workdir = os.path.abspath(args.workdir or os.path.join(
        os.environ.get("TMPDIR", "/tmp"), "teambench_g3_sweep"))
    os.makedirs(workdir, exist_ok=True)

    if args.bootstrap:
        gate_venv = os.path.join(workdir, "gate_venv")
        py = GATE.build_gate_venv(gate_venv)
        # Compare venv PREFIXES, not resolved binaries: a venv's bin/python is a
        # symlink to the base interpreter, so os.path.realpath() collapses the
        # throwaway venv and the repo venv onto the same /usr/bin/python3.x and
        # the re-exec never fires. That silently ran the sweep under whatever
        # interpreter invoked it, which is the exact thing --bootstrap exists to
        # prevent.
        if os.path.realpath(os.path.dirname(os.path.dirname(py))) != os.path.realpath(sys.prefix):
            rest = [a for a in sys.argv[1:] if a != "--bootstrap"]
            if "--workdir" not in rest:
                rest += ["--workdir", workdir]
            print(f"[bootstrap] re-executing under {py}", flush=True)
            os.execv(py, [py, os.path.abspath(__file__)] + rest)

    if not args.allow_shared_venv:
        prefix = os.path.realpath(sys.prefix)
        for v in GATE.repo_venv_paths():
            if os.path.isdir(v) and prefix == os.path.realpath(v):
                print(f"REFUSING to run under the repository venv {v}. "
                      "Use --bootstrap.", file=sys.stderr)
                return 2

    os.makedirs(OUT_DIR, exist_ok=True)
    scope = args.tasks or tasks_with_reference()
    if args.shuffle_seed is not None:
        import random as _random
        _random.Random(args.shuffle_seed).shuffle(scope)
    if args.limit:
        scope = scope[:args.limit]

    workers = max(1, min(args.workers, MAX_WORKERS))
    cfg = {"workdir": workdir, "seed": args.seed, "grade_timeout": args.grade_timeout,
           "keep_runs": args.keep_runs}

    done: dict[str, dict] = {}
    if not args.no_resume and os.path.isfile(CHECKPOINT_PATH):
        with open(CHECKPOINT_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                    done[r["task_id"]] = r
                except (json.JSONDecodeError, KeyError):
                    continue
        print(f"[resume] {len(done)} tasks already in checkpoint", flush=True)
    elif args.no_resume and os.path.isfile(CHECKPOINT_PATH):
        os.remove(CHECKPOINT_PATH)

    todo = [] if args.summarize_only else [t for t in scope if t not in done]
    print(f"[scope] {len(scope)} tasks with a reference patch, {len(todo)} to evaluate, "
          f"{workers} workers, workdir={workdir}", flush=True)

    ck_lock = threading.Lock()
    t0 = time.monotonic()
    completed = 0
    mp_ctx = multiprocessing.get_context("fork")
    tmp_lock = mp_ctx.Lock()
    with open(CHECKPOINT_PATH, "a", encoding="utf-8") as ck:
        with ProcessPoolExecutor(max_workers=workers, mp_context=mp_ctx,
                                 initializer=_init_worker,
                                 initargs=(tmp_lock,)) as pool:
            futs = {pool.submit(evaluate, t, cfg): t for t in todo}
            for fut in as_completed(futs):
                tid = futs[fut]
                try:
                    rec = fut.result()
                except Exception as exc:
                    rec = {"task_id": tid, "family": GATE.task_family(tid),
                           "outcome": "error",
                           "errors": [f"worker crashed: {type(exc).__name__}: {exc}"]}
                done[tid] = rec
                completed += 1
                with ck_lock:
                    ck.write(json.dumps(rec) + "\n")
                    ck.flush()
                    os.fsync(ck.fileno())
                ap_ = rec.get("application") or {}
                print(f"[{completed}/{len(todo)}] {tid} {rec.get('outcome')} "
                      f"method={ap_.get('method')} "
                      f"ref={(rec.get('reference') or {}).get('partial_score')} "
                      f"floor={(rec.get('pristine') or {}).get('partial_score')}", flush=True)

    records = [done[t] for t in scope if t in done]
    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "seed": args.seed, "workers": workers,
        "shuffle_seed": args.shuffle_seed,
        "grade_timeout": args.grade_timeout,
        "python_executable": sys.executable,
        "python_version": sys.version.split()[0],
        "workdir": workdir,
        # None, not 0.0, when nothing was evaluated: a --summarize-only rebuild
        # measures no grading and must not look like a run that took no time.
        "wall_seconds": (round(time.monotonic() - t0, 1) if todo else None),
        "summarize_only": not todo,
        "executor": "ProcessPoolExecutor(fork)",
        "scope_size": len(scope),
        "evaluated": len(records),
        "complete": len(records) == len(scope),
        "applier": "harness/reference_apply.py:build_reference_workspace",
        "sys_prefix": sys.prefix,
        "grading_path_prefix": os.path.dirname(os.path.abspath(sys.executable)),
        "pip_shim": _pip_shim_info(os.path.dirname(os.path.abspath(sys.executable))),
        "staging_fn": "harness.run_all.setup_run",
        "grading_fn": "scripts/task_admission_gate.py:invoke_grader",
        **GATE.git_info(),
    }
    summary = summarize(records, meta)
    with open(LEDGER_PATH, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "tasks": records}, f, indent=2)
    with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
        f.write(render_markdown(summary, records))

    print("\n" + "=" * 68)
    for k, v in sorted(summary["outcomes"].items()):
        print(f"  {k:32s} {v:5d}  {v/max(1,summary['n']):.1%}")
    print(f"  wrote {LEDGER_PATH}")
    print(f"  wrote {SUMMARY_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
