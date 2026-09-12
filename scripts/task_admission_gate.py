#!/usr/bin/env python3
"""
TeamBench Task Admission Gate
=============================

A task is *admissible* to TeamBench only if it can be shown, mechanically, to
measure agent work. This script is the mechanism. It stages every candidate
task exactly the way the evaluation harness does, runs the task's real
``grade.sh``, and evaluates seven gates. It writes one JSON record per task
plus a corpus-level summary.

    shared/paper/quality/admission_ledger.json   per-task records + summary
    shared/paper/quality/admission_summary.md    the summary as a table
    shared/paper/quality/admission_checkpoint.jsonl   incremental checkpoint

Re-run with one command
-----------------------
    python3 scripts/task_admission_gate.py --bootstrap

``--bootstrap`` builds a throwaway grading virtualenv (see "Grading
environment" below) and re-executes this script inside it. Everything else is
defaulted. The run is resumable: it appends to the checkpoint after every task
and skips tasks already present unless ``--no-resume`` is given.

Two self-verification modes exist, because a gate whose own correctness is
unaudited is worth nothing:

    python3 scripts/task_admission_gate.py --selftest

builds two synthetic tasks in a temporary tasks tree -- one constructed to
satisfy all seven gates including a reference solution, one constructed to
violate G1, G5 and G6 -- runs them through the same ``evaluate_task()`` the
sweep uses, and exits non-zero if the gate does not classify both correctly.

    python3 scripts/task_admission_gate.py --parity-check N

grades N real tasks twice, once through this script's ``invoke_grader()`` and
once through the unmodified ``harness.run_all.grade_run()``, and reports whether
the two agree. The result is stored in the ledger's ``meta.parity_check``.


THE SEVEN GATES
---------------

G1  pristine floor (discriminative scale; see the note at its evaluation)
    Stage the pristine seed-0 workspace exactly as ``harness.run_all.setup_run``
    does, make NO edits of any kind, and run the real ``grade.sh``.
    Recorded: ``floor`` = ``score.json -> secondary.partial_score``.
    PASS iff the task has at least one discriminative check, so that an
    empty submission scores 0 on the checks that are actually scored. The
    raw floor, guards included, is recorded alongside it.
    Any credit awarded for doing nothing is a defect: it is score an agent
    receives without acting, so it inflates every condition equally and
    compresses the dynamic range of the benchmark.

G2  no free pass
    The same pristine, unedited workspace must not reach ``pass == true``.
    PASS iff pristine ``pass`` is false.

G3  reference solution passes
    If ``tasks/<id>/reference/patch.diff`` exists, turn a freshly staged
    pristine workspace into the upstream reference solution with
    ``harness.reference_apply.build_reference_workspace`` and grade it.
    PASS iff the reference was applied AND ``partial_score == 1.0`` AND
    ``pass == true``.
    UNKNOWN if no reference patch exists. UNKNOWN is not a pass. A task with no
    demonstrated solution has not been shown to be solvable at all.

    FAIL is now split, because the two halves are completely different findings
    and the old implementation conflated them. ``rec["gates"]["G3"]["outcome"]``
    records which:

      ``b_grader_rejects_reference``  the reference was applied and the grader
          did not give it 1.0. The grader disagrees with the fix the upstream
          maintainers merged. This is a defect in the task, and it is the
          finding worth reporting.
      ``c_unappliable``  the reference could not be applied by any method in
          the ladder. The task has lost its link to ground truth and nothing can
          be concluded about its grader.

    The applier matters more than it sounds. GH workspaces are parameterised by
    their generator (identifiers renamed, comment noise injected), they contain
    only the PR-touched files rather than the repo, and many already ship the
    PR's test files in their post-PR state. A plain ``git apply`` therefore
    measures the applier, not the benchmark: under the previous implementation
    57 of 63 G3 failures were "patch did not apply", of which 56 apply cleanly
    once the diff is applied to the generator's own unparameterised base and the
    parameterisation is replayed on the result. That previous ladder also
    contained ``patch -p0``, which "succeeds" on a ``diff --git`` patch by
    creating literal ``a/`` and ``b/`` directories, recording applications that
    never touched the workspace at all.

    The corpus-wide measurement lives in ``scripts/g3_reference_sweep.py``,
    which runs this same definition over every task that has a reference patch
    rather than only the 150 in this gate's scope.

G4  determinism
    Run the grader a second time on the *same* staged directory and compare the
    two ``score.json`` documents after normalisation (see NORMALISATION below).
    PASS iff the normalised documents are identical.
    Note that the second run observes any side effects the first run left
    behind (installed packages, ``__pycache__``, files the grader wrote into the
    workspace). That is deliberate: a grader whose verdict depends on whether it
    has been run before is not deterministic in the sense the benchmark needs.

G5  hermeticity (static)
    Read ``grade.sh`` and look for two classes of defect:
      (a) network / package installation at grade time -- pip, npm, yarn, pnpm,
          curl, wget, apt, apk, yum, dnf, git clone/fetch/pull, go get,
          cargo fetch, gem install;
      (b) references to a virtualenv path that is gitignored or absent from a
          clean checkout -- ``venv/``, ``.venv/``, ``/usr/local/lib/venv``.
    Full-line comments are ignored; trailing comments are not.
    PASS iff neither class matches.
    This gate is static only. It is a lower bound on non-hermeticity: it cannot
    see network access performed by a test suite the grader invokes.

G6  discriminative checks
    From the pristine run, split the grader's checklist into checks that pass
    with zero work ("free") and checks that do not ("discriminative").
    PASS iff ``discriminative / total >= 0.5``.
    When a reference solution exists, the stricter definition is also computed
    and recorded as ``g6.strict_discriminative``: a check is strictly
    discriminative iff it FAILS on the pristine workspace and PASSES on the
    reference solution. G6's verdict uses the pristine-only definition, because
    it is available for every task; the strict count is reported alongside.

G7  terminates
    The grader must finish inside the harness's own cap
    (``harness.run_all.grade_run`` kills the grader's process group at 300 s).
    PASS iff the pristine grade returned without being killed.
    Caveat: this is wall-clock on the machine that ran the sweep. A G7 failure
    means "did not finish in 300 s under the load this machine was actually
    carrying", not "cannot finish". Every invocation's ``grade_seconds`` is
    recorded so a reviewer can see how close a task ran to the cap, and the
    gate should be re-run on an idle machine before a G7 failure is reported as
    a property of the task.

ADMISSION
    ``admitted_strict``  -- all seven gates pass. This is the honest size of the
                            benchmark and the number the paper should report.
    ``admitted_pending_reference``
                         -- G1, G2, G4, G5, G6, G7 pass and G3 is pass OR
                            unknown. This is the ceiling that becomes reachable
                            once reference solutions exist for every task. It is
                            reported separately and is NOT the headline.


ADVISORY MEASUREMENTS (recorded, never gated)
---------------------------------------------
These are measurements the paper needs. They are deliberately kept out of the
gate verdicts so that no hidden heuristic can move the admitted count.

attestation credit
    ``submission/attestation.json`` is a scored check in a large minority of
    graders. A second pristine workspace is staged, the harness's own
    ``_write_passing_attestation`` stub is written into ``submission/``, and the
    grader is run again. ``floor_attested`` and
    ``attestation_credit = floor_attested - floor`` are recorded. This is the
    score a do-nothing agent collects merely by filing a passing report, which
    is exactly what the ``team_no_verify`` ablation condition does
    automatically.

spec availability
    Whether ``tasks/<id>/spec.md`` and ``brief.md`` exist on disk. Generator
    backed tasks produce a spec in memory, but no harness caller writes it to
    ``task_dir``, so a task with no on-disk spec.md hands the agent an empty
    specification at run time.

grade-time installs
    ``pip freeze`` is captured before and after the whole sweep. Any delta is a
    package that grading downloaded from the network, which makes grading
    order-dependent: a task graded later benefits from a dependency a task
    graded earlier installed.


GRADING ENVIRONMENT
-------------------
``harness.run_all.grade_run`` prepends ``os.path.dirname(sys.executable)`` to
the grader's PATH, so whichever interpreter runs this script is the interpreter
and the ``pip`` that graders get. Because many graders run ``pip install`` at
grade time, running this script under the repository's own ``venv/`` would
mutate that venv, concurrently, from four workers.

The gate therefore refuses to run under ``<repo>/venv`` or ``<repo>/.venv``
unless ``--allow-shared-venv`` is passed. ``--bootstrap`` instead builds a
throwaway venv under the work directory containing a single ``.pth`` file that
adds the repository venv's ``site-packages`` to ``sys.path``. Reads of the
canonical dependency set are therefore unchanged, while any grade-time install
lands in the throwaway and is discarded.


NORMALISATION (used by G4)
--------------------------
Before comparing two ``score.json`` documents, the following are removed or
rewritten, recursively, over the whole document. Nothing else is touched.

  dropped keys      timestamp, timestamps, generated_at, graded_at, started_at,
                    finished_at, duration, duration_s, duration_sec, elapsed,
                    elapsed_s, runtime, runtime_s, run_id, run_dir, workspace,
                    workspace_dir, reports, reports_dir, submission,
                    submission_dir, task_dir, hostname, host, pid, tmpdir
  rewritten in all  ISO-8601 datetimes            -> <TS>
  string values     harness run ids (8_6_hex8)    -> <RUNID>
                    the gate's own work directory -> <WORKDIR>
                    any /tmp/... path             -> <TMP>
                    hex runs of 8 or more digits  -> <HEX>
                    0x... addresses               -> <ADDR>

SCOPE
-----
Default scope is the 90 leaderboard tasks from
``leaderboard/data/leaderboard_90_tasks.json`` plus a deterministic random
sample of 60 further tasks drawn with ``random.Random(--sample-seed)`` from the
sorted list of every other directory under ``tasks/`` that contains a
``grade.sh``. The sample is an unbiased draw from the remaining corpus, so it is
dominated by the GH family in the same proportion the corpus is; a per-family
breakdown is reported so the reader can see this.

All task instances are staged at seed 0.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

TASKS_DIR = os.path.join(REPO_ROOT, "tasks")
LB90_PATH = os.path.join(REPO_ROOT, "leaderboard", "data", "leaderboard_90_tasks.json")
OUT_DIR = os.path.join(REPO_ROOT, "shared", "paper", "quality")
LEDGER_PATH = os.path.join(OUT_DIR, "admission_ledger.json")
SUMMARY_PATH = os.path.join(OUT_DIR, "admission_summary.md")
CHECKPOINT_PATH = os.path.join(OUT_DIR, "admission_checkpoint.jsonl")
CORPUS_STATIC_PATH = os.path.join(OUT_DIR, "admission_corpus_static.json")
PARITY_PATH = os.path.join(OUT_DIR, "admission_parity.json")

# harness/run_all.py grade_run() kills the grader's process group at this many
# seconds. G7 is defined against this number, not against --grade-timeout.
HARNESS_GRADE_CAP_S = 300

GATE_IDS = ["G1", "G2", "G3", "G4", "G5", "G6", "G7"]
GATE_TITLES = {
    "G1": "an empty submission scores 0 on the discriminative checks",
    "G2": "pristine does not pass",
    "G3": "reference solution scores 1.0",
    "G4": "grader is deterministic",
    "G5": "grader is hermetic (static)",
    "G6": ">=50% of checks are discriminative",
    "G7": "grader terminates within 300 s",
}


# ---------------------------------------------------------------------------
# Grader invocation
# ---------------------------------------------------------------------------
# invoke_grader() below is a copy of harness.run_all.grade_run() with two
# changes: the 300 s literal passed to communicate() is replaced by the
# `timeout_s` argument with wall-clock time measured, and the staged-core hook
# below. The duplication is the reason the second change was needed at all, so
# --parity-check matters: run it after touching either copy. Run this script
# with --parity-check to have it assert, on live tasks, that invoke_grader() and
# the unmodified harness grade_run() return identical scores.

def invoke_grader(task_name: str, task_dir: str, run_dir: str, timeout_s: int) -> tuple[dict, float, bool]:
    """Run a task's grade.sh. Returns (score_dict, elapsed_seconds, timed_out)."""
    import pathlib

    workspace = os.path.abspath(os.path.join(run_dir, "workspace"))
    reports = os.path.abspath(os.path.join(run_dir, "reports"))
    submission = os.path.abspath(os.path.join(run_dir, "submission"))
    score_path = os.path.join(reports, "score.json")

    # A stale score.json from a previous invocation must not be mistaken for
    # this invocation's output. harness.grade_run() does not need this because
    # it grades each run directory once; the gate grades one directory twice.
    if os.path.isfile(score_path):
        os.remove(score_path)

    grade_script = os.path.abspath(os.path.join(task_dir, "grade.sh"))
    task_dir_abs = os.path.abspath(task_dir)
    expected_path = os.path.join(reports, "expected.json")
    grade_args = ["bash", grade_script, workspace, reports, submission, task_dir_abs]
    if os.path.isfile(expected_path):
        grade_args.append(expected_path)

    grade_env = os.environ.copy()
    venv_bin = os.path.dirname(os.path.abspath(sys.executable))
    grade_env["PATH"] = venv_bin + os.pathsep + grade_env.get("PATH", "")

    # The one behaviour this copy had drifted from. harness.run_all.grade_run
    # now restores a staged task's held-out tests before grading and points the
    # grader at that task's pinned dependency environment. Without it the gate
    # grades a workspace whose discriminating test is absent, so the pristine
    # floor looks high and applying the reference changes nothing: G1, G3 and G6
    # all fail for a reason that has nothing to do with the task.
    try:
        from harness.core_staging import grade_prepare
        core_env = grade_prepare(run_dir)
        if core_env.get("PATH"):
            grade_env["PATH"] = core_env["PATH"] + os.pathsep + grade_env["PATH"]
        if core_env.get("PYTHONPATH"):
            grade_env["PYTHONPATH"] = core_env["PYTHONPATH"] + os.pathsep + \
                grade_env.get("PYTHONPATH", "")
    except ImportError:
        pass

    timed_out = False
    t0 = time.monotonic()
    proc = subprocess.Popen(
        grade_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, env=grade_env, start_new_session=True,
    )
    try:
        proc.communicate(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        timed_out = True
        from harness.agent_interface import _kill_process_group
        _kill_process_group(proc)
    elapsed = time.monotonic() - t0

    if os.path.isfile(score_path):
        try:
            return json.loads(pathlib.Path(score_path).read_text()), elapsed, timed_out
        except json.JSONDecodeError:
            pass

    return (
        {
            "pass": False,
            "primary": {"success": 0},
            "secondary": {},
            "failure_modes": ["grader_timeout" if timed_out else "grader_no_score"],
        },
        elapsed,
        timed_out,
    )


# ---------------------------------------------------------------------------
# Score helpers
# ---------------------------------------------------------------------------

VOLATILE_KEYS = {
    "timestamp", "timestamps", "generated_at", "graded_at", "started_at",
    "finished_at", "duration", "duration_s", "duration_sec", "elapsed",
    "elapsed_s", "runtime", "runtime_s", "run_id", "run_dir", "workspace",
    "workspace_dir", "reports", "reports_dir", "submission", "submission_dir",
    "task_dir", "hostname", "host", "pid", "tmpdir",
}

_ISO_RE = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?")
_RUNID_RE = re.compile(r"\d{8}_\d{6}_[0-9a-f]{8}")
_TMP_RE = re.compile(r"/tmp/[^\s\"']+")
_HEX_RE = re.compile(r"\b[0-9a-f]{8,}\b")
_ADDR_RE = re.compile(r"0x[0-9a-fA-F]+")


def scrub(value, workdir: str):
    """Recursively drop volatile keys and rewrite volatile substrings."""
    if isinstance(value, dict):
        return {k: scrub(v, workdir) for k, v in sorted(value.items()) if k not in VOLATILE_KEYS}
    if isinstance(value, list):
        return [scrub(v, workdir) for v in value]
    if isinstance(value, str):
        s = value
        if workdir:
            s = s.replace(workdir, "<WORKDIR>")
        s = _ISO_RE.sub("<TS>", s)
        s = _RUNID_RE.sub("<RUNID>", s)
        s = _TMP_RE.sub("<TMP>", s)
        s = _ADDR_RE.sub("<ADDR>", s)
        s = _HEX_RE.sub("<HEX>", s)
        return s
    return value


def normalized_score_text(score: dict, workdir: str) -> str:
    return json.dumps(scrub(score, workdir), sort_keys=True, separators=(",", ":"))


def partial_of(score: dict):
    """Extract partial_score. Falls back to checks_passed/checks_total."""
    sec = score.get("secondary") or {}
    if isinstance(sec.get("partial_score"), (int, float)):
        return float(sec["partial_score"])
    p, t = sec.get("checks_passed"), sec.get("checks_total")
    if isinstance(p, int) and isinstance(t, int) and t > 0:
        return round(p / t, 4)
    return None


def checklist_of(score: dict) -> list:
    cl = score.get("checklist")
    return cl if isinstance(cl, list) else []


# Graders in this repo emit per-check status under different key names:
# harness/grader_helpers.sh and the hand-written graders use "ok";
# generators/real_data_base.py (the RDS family) uses "passed".
_STATUS_KEYS = ("ok", "passed", "pass", "success", "result")
_TRUE_WORDS = {"pass", "passed", "ok", "true", "yes", "1"}
_FALSE_WORDS = {"fail", "failed", "false", "no", "0"}


def check_status(entry) -> bool | None:
    """Resolve one checklist entry to True/False, or None if unrecognisable."""
    if not isinstance(entry, dict):
        return None
    for k in _STATUS_KEYS:
        if k not in entry:
            continue
        v = entry[k]
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            lv = v.strip().lower()
            if lv in _TRUE_WORDS:
                return True
            if lv in _FALSE_WORDS:
                return False
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return bool(v)
    return None


def checklist_statuses(cl: list) -> dict[str, bool] | None:
    """id -> bool for a checklist, or None unless EVERY entry resolves.

    An all-or-nothing rule: a partially readable checklist would silently
    undercount free checks, which would flatter G6.
    """
    if not cl:
        return None
    out = {}
    for i, entry in enumerate(cl):
        st = check_status(entry)
        if st is None:
            return None
        cid = str(entry.get("id", entry.get("name", i))) if isinstance(entry, dict) else str(i)
        out[cid] = st
    return out


# ---------------------------------------------------------------------------
# G5: static hermeticity
# ---------------------------------------------------------------------------

# The three static detectors below each want the text of the same grade.sh, and
# the corpus scan runs all three over 800+ files on a network filesystem. One
# read per file, memoised on (path, mtime, size), instead of three.
_TEXT_CACHE: dict[str, tuple[tuple, str | None]] = {}
_TEXT_CACHE_LOCK = threading.Lock()


def grader_text(path: str) -> str | None:
    """Text of a grade.sh, or None if unreadable. Memoised per (path, mtime, size)."""
    try:
        st = os.stat(path)
        key = (st.st_mtime_ns, st.st_size)
    except OSError:
        return None
    with _TEXT_CACHE_LOCK:
        hit = _TEXT_CACHE.get(path)
        if hit and hit[0] == key:
            return hit[1]
    try:
        text = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        text = None
    with _TEXT_CACHE_LOCK:
        _TEXT_CACHE[path] = (key, text)
    return text


NETWORK_PATTERNS = [
    ("pip_install", r"\bpip3?\s+install\b|\bpython3?\s+-m\s+pip\s+install\b|\buv\s+pip\s+install\b|\bpip3?\s+download\b"),
    ("npm_install", r"\bnpm\s+(?:install|i|ci)\b|\byarn\s+(?:add|install)\b|\bpnpm\s+(?:add|install)\b"),
    ("curl_wget", r"\bcurl\s|\bwget\s"),
    ("system_pkg", r"\bapt(?:-get)?\s+install\b|\bapk\s+add\b|\byum\s+install\b|\bdnf\s+install\b"),
    ("git_network", r"\bgit\s+(?:clone|fetch|pull)\b|\bgit\s+submodule\s+update\b"),
    ("lang_pkg", r"\bgo\s+get\b|\bgo\s+mod\s+download\b|\bcargo\s+(?:add|fetch)\b|\bgem\s+install\b|\bbundle\s+install\b"),
]
# Evaluated in order. A line matching image_only_venv has that substring removed
# before gitignored_venv is tried, so the same text is never counted twice.
IMAGE_VENV_LITERAL = "/usr/local/lib/venv"
VENV_PATTERNS = [
    ("image_only_venv", re.escape(IMAGE_VENV_LITERAL)),
    ("gitignored_venv", r"(?<![\w.])\.?venv/bin"),
]


def static_hermeticity(grade_sh_path: str) -> dict:
    """Scan grade.sh for grade-time network use and venv-path references."""
    text = grader_text(grade_sh_path)
    if text is None:
        return {"readable": False, "error": "unreadable", "network": [], "venv": []}

    net_hits, venv_hits = [], []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        if raw.lstrip().startswith("#"):
            continue  # full-line comment: not an invocation
        for name, pat in NETWORK_PATTERNS:
            if re.search(pat, raw):
                net_hits.append({"kind": name, "line": lineno, "text": raw.strip()[:200]})
        residual = raw
        for name, pat in VENV_PATTERNS:
            if re.search(pat, residual):
                venv_hits.append({"kind": name, "line": lineno, "text": raw.strip()[:200]})
                if name == "image_only_venv":
                    residual = residual.replace(IMAGE_VENV_LITERAL, "")
    return {"readable": True, "network": net_hits, "venv": venv_hits}


# ---------------------------------------------------------------------------
# Advisory: does the grader execute a script that lives in the agent's workspace?
# ---------------------------------------------------------------------------
# A grader that runs `python3 check_solution.py` after `cd "${WORKSPACE}"` is
# executing a file the agent can overwrite, so the agent controls its own score.
# This is reported, never gated, because the seven gates are fixed.

_CD_WORKSPACE_RE = re.compile(r"""cd\s+["']?\$\{?WORKSPACE\}?["']?""")
_EXEC_REL_SCRIPT_RE = re.compile(
    r"""^\s*(?:python3?|bash|sh|node|ruby|perl)\s+(?!-)([^\s"'|<>&;]+\.(?:py|sh|js|rb|pl))""")


def workspace_executed_scripts(grade_sh_path: str) -> list[dict]:
    """Relative scripts the grader runs after cd'ing into the agent's workspace."""
    text = grader_text(grade_sh_path)
    if text is None:
        return []
    lines = text.splitlines()
    hits, in_ws = [], False
    for lineno, raw in enumerate(lines, start=1):
        if raw.lstrip().startswith("#"):
            continue
        if _CD_WORKSPACE_RE.search(raw):
            in_ws = True
        if not in_ws:
            continue
        m = _EXEC_REL_SCRIPT_RE.match(raw)
        if m and not m.group(1).startswith("/"):
            hits.append({"line": lineno, "script": m.group(1), "text": raw.strip()[:200]})
    return hits


# ---------------------------------------------------------------------------
# Advisory: graders that write to a fixed /tmp path
# ---------------------------------------------------------------------------
# TRAP1's grader writes its intermediate results to the literal path
# /tmp/trap1_results.json. Two grades of that task running anywhere on the same
# host at the same time overwrite each other's file, and both report whatever
# the loser wrote. Measured on this repository: TRAP1's pristine floor read 0.40
# when graded alone and 0.10 when graded next to other work.
#
# A fixed /tmp path is therefore both a benchmark defect (the task's score
# depends on what else the machine is doing) and a threat to this sweep's own
# numbers, so the gate detects it, records it, and serialises its own
# invocations of any grader that has one.

_FIXED_TMP_RE = re.compile(r"/tmp/[A-Za-z0-9_.\-/]+")


def fixed_tmp_paths(grade_sh_path: str) -> list[str]:
    """Literal /tmp paths in a grader, excluding ones made unique at run time.

    A path immediately followed by a shell expansion ($$, ${...}, $RANDOM) is
    per-process and therefore safe; everything else is shared host-wide.
    """
    text = grader_text(grade_sh_path)
    if text is None:
        return []
    lines = text.splitlines()
    found = set()
    for raw in lines:
        if raw.lstrip().startswith("#"):
            continue
        for m in _FIXED_TMP_RE.finditer(raw):
            tail = raw[m.end():m.end() + 1]
            if tail in ("$", "{"):
                continue  # /tmp/foo_$$.json and friends are per-process
            found.add(m.group(0))
    return sorted(found)


# Serialises this process's grader invocations for any task whose grader uses a
# fixed /tmp path. It cannot protect against other processes on the host; the
# ledger flags those tasks so a reviewer knows the residual risk.
_FIXED_TMP_LOCK = threading.Lock()


class _MaybeLock:
    """Context manager that acquires the lock only when `active` is true."""

    def __init__(self, lock, active: bool):
        self._lock, self._active = lock, active

    def __enter__(self):
        if self._active:
            self._lock.acquire()
        return self

    def __exit__(self, *exc):
        if self._active:
            self._lock.release()
        return False


# ---------------------------------------------------------------------------
# G3: reference patch
# ---------------------------------------------------------------------------

def apply_reference_patch(task_id: str, task_dir: str, workspace: str, seed: int) -> dict:
    """Turn a staged pristine workspace into the upstream reference solution.

    Delegates to harness.reference_apply.build_reference_workspace, which applies
    the diff to the generator's own unparameterised base and then re-runs the
    generator's parameterisation with the symbol rename map frozen to the staged
    instance's map. See that module for the full method ladder and for why a
    naive `git apply` on the staged tree measures the applier rather than the
    benchmark.

    The previous implementation of this function tried `patch -p0` on
    `diff --git` patches. GNU patch "succeeds" at that by creating literal `a/`
    and `b/` directories, so it recorded applications that never touched the
    workspace. That ladder entry is gone and every application is now checked
    for stray `a/` and `b/` directories.
    """
    from harness.reference_apply import build_reference_workspace
    return build_reference_workspace(task_id, task_dir, workspace, seed=seed)


# ---------------------------------------------------------------------------
# Scope
# ---------------------------------------------------------------------------

def file_sha256(path: str) -> str | None:
    """Content hash of a file, or None if unreadable."""
    import hashlib
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 16), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def gradeable_tasks() -> list[str]:
    """Every directory under tasks/ that has a grade.sh, sorted."""
    out = []
    with os.scandir(TASKS_DIR) as it:
        for entry in it:
            if entry.is_dir() and os.path.isfile(os.path.join(entry.path, "grade.sh")):
                out.append(entry.name)
    return sorted(out)


def build_scope(sample_size: int, sample_seed: int, only: list[str] | None,
                reference_sample: int = 0) -> list[dict]:
    all_gradeable = gradeable_tasks()
    if only:
        known = set(all_gradeable)
        return [{"task_id": t, "scope": "explicit", "gradeable": t in known} for t in only]

    lb = json.load(open(LB90_PATH, encoding="utf-8"))
    lb_ids = [t["task_id"] for t in lb["tasks"]]
    lb_meta = {t["task_id"]: t for t in lb["tasks"]}
    lb_set = set(lb_ids)

    rest = [t for t in all_gradeable if t not in lb_set]
    n = min(sample_size, len(rest))
    rng = random.Random(sample_seed)
    sample = sorted(rng.sample(rest, n))

    # G3 (does a known-correct solution pass?) can only be evaluated where a
    # reference patch exists. A uniform draw over the corpus leaves it `unknown`
    # on most of the scope, so add a stratum drawn from the reference-bearing
    # population. Without this the gate reports G3 on whatever the uniform sample
    # happened to catch, which is not a measurement of anything in particular.
    ref_pool = [t for t in rest
                if t not in set(sample)
                and os.path.isfile(os.path.join(TASKS_DIR, t, "reference", "patch.diff"))]
    ref_n = min(reference_sample, len(ref_pool))
    ref_extra = sorted(rng.sample(ref_pool, ref_n)) if ref_n else []

    scope = []
    for t in lb_ids:
        m = lb_meta.get(t, {})
        scope.append({"task_id": t, "scope": "lb90",
                      "category": m.get("category"), "difficulty": m.get("difficulty")})
    for t in sample:
        scope.append({"task_id": t, "scope": "sample60", "category": None, "difficulty": None})
    for t in ref_extra:
        scope.append({"task_id": t, "scope": "reference", "category": None, "difficulty": None})
    return scope


def task_family(task_id: str) -> str:
    """Leading alphabetic run of the task id, e.g. GH103_... -> GH."""
    m = re.match(r"^([A-Za-z]+)", task_id)
    return m.group(1).upper() if m else "?"


# ---------------------------------------------------------------------------
# Per-task evaluation
# ---------------------------------------------------------------------------

_STAGE_LOCK = threading.Lock()


def stage(task_id: str, runs_dir: str, seed: int) -> tuple[str, str]:
    """Stage a pristine workspace using the harness's own setup_run."""
    from harness.run_all import setup_run
    # setup_run imports and instantiates generator modules; serialise it so
    # concurrent importlib activity cannot interleave. Staging costs ~0.1 s.
    with _STAGE_LOCK:
        _run_id, run_dir, task_dir = setup_run(task_id, TASKS_DIR, runs_dir, seed=seed)
    return run_dir, task_dir


def write_passing_attestation(run_dir: str, task_id: str) -> None:
    """Byte-identical to harness.ablation._write_passing_attestation."""
    submission = os.path.join(run_dir, "submission")
    os.makedirs(submission, exist_ok=True)
    att = {"task_id": task_id, "verdict": "pass", "checklist": [], "condition": "team_no_verify_stub"}
    with open(os.path.join(submission, "attestation.json"), "w", encoding="utf-8") as f:
        json.dump(att, f, indent=2)


def evaluate_task(entry: dict, cfg: dict) -> dict:
    task_id = entry["task_id"]
    task_dir = os.path.join(TASKS_DIR, task_id)
    workdir = cfg["workdir"]
    seed = cfg["seed"]
    timeout_s = cfg["grade_timeout"]

    rec: dict = {
        "task_id": task_id,
        "scope": entry.get("scope"),
        "family": task_family(task_id),
        "category": entry.get("category"),
        "difficulty": entry.get("difficulty"),
        "seed": seed,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        # Graders are edited by other work in this repository. Recording the exact
        # bytes that were graded is what makes a record re-checkable later.
        "grade_sh_sha256": file_sha256(os.path.join(task_dir, "grade.sh")),
        "grade_sh_mtime": (os.path.getmtime(os.path.join(task_dir, "grade.sh"))
                           if os.path.isfile(os.path.join(task_dir, "grade.sh")) else None),
        "artifacts": {
            "grade_sh": os.path.isfile(os.path.join(task_dir, "grade.sh")),
            "task_yaml": os.path.isfile(os.path.join(task_dir, "task.yaml")),
            "spec_md": os.path.isfile(os.path.join(task_dir, "spec.md")),
            "brief_md": os.path.isfile(os.path.join(task_dir, "brief.md")),
            "static_workspace": os.path.isdir(os.path.join(task_dir, "workspace")),
            "setup_sh": os.path.isfile(os.path.join(task_dir, "setup.sh")),
            "reference_patch": os.path.isfile(os.path.join(task_dir, "reference", "patch.diff")),
        },
        "gates": {g: {"verdict": "error", "detail": "not evaluated"} for g in GATE_IDS},
        "advisory": {},
        "errors": [],
    }

    # --- G5 is static and never depends on staging ------------------------
    herm = static_hermeticity(os.path.join(task_dir, "grade.sh"))
    rec["g5_detail"] = herm
    ws_exec = workspace_executed_scripts(os.path.join(task_dir, "grade.sh"))
    rec["advisory"]["workspace_executed_scripts"] = ws_exec
    tmp_paths = fixed_tmp_paths(os.path.join(task_dir, "grade.sh"))
    rec["advisory"]["fixed_tmp_paths"] = tmp_paths
    rec["concurrency_unsafe"] = bool(tmp_paths)
    if not herm.get("readable"):
        rec["gates"]["G5"] = {"verdict": "error", "detail": herm.get("error", "unreadable")}
    else:
        clean = not herm["network"] and not herm["venv"]
        rec["gates"]["G5"] = {
            "verdict": "pass" if clean else "fail",
            "network_hits": len(herm["network"]),
            "venv_hits": len(herm["venv"]),
            "kinds": sorted({h["kind"] for h in herm["network"] + herm["venv"]}),
        }

    if not rec["artifacts"]["grade_sh"]:
        for g in GATE_IDS:
            rec["gates"][g] = {"verdict": "error", "detail": "no grade.sh"}
        rec["errors"].append("no grade.sh")
        rec["admitted_strict"] = False
        rec["admitted_pending_reference"] = False
        return rec

    run_root = os.path.join(workdir, "runs")

    # --- Stage A: pristine -> G1, G2, G4, G6, G7 --------------------------
    try:
        run_a, task_dir_a = stage(task_id, run_root, seed)
    except Exception as exc:
        rec["errors"].append(f"stage_pristine: {type(exc).__name__}: {exc}")
        for g in ("G1", "G2", "G3", "G4", "G6", "G7"):
            rec["gates"][g] = {"verdict": "error", "detail": "staging failed"}
        rec["admitted_strict"] = False
        rec["admitted_pending_reference"] = False
        return rec

    with _MaybeLock(_FIXED_TMP_LOCK, bool(tmp_paths)):
        score_a1, el_a1, to_a1 = invoke_grader(task_id, task_dir_a, run_a, timeout_s)
    floor = partial_of(score_a1)
    pass_a1 = bool(score_a1.get("pass"))
    cl_a1 = checklist_of(score_a1)

    st_a1 = checklist_statuses(cl_a1)
    rec["pristine"] = {
        "partial_score": floor,
        "pass": pass_a1,
        "checks_passed": (score_a1.get("secondary") or {}).get("checks_passed"),
        "checks_total": (score_a1.get("secondary") or {}).get("checks_total"),
        "checklist_len": len(cl_a1),
        "checklist_readable": st_a1 is not None,
        "failure_modes": score_a1.get("failure_modes", []),
        "grade_seconds": round(el_a1, 2),
        "timed_out": to_a1,
        "free_check_ids": sorted(k for k, v in (st_a1 or {}).items() if v),
    }

    # G1
    if floor is None:
        rec["gates"]["G1"] = {"verdict": "error", "detail": "grader emitted no partial_score", "floor": None}
    else:
        # G1 used to require `floor == 0.0` on the RAW partial_score. That is
        # unreachable for any task that has a guard check, because guards pass
        # on an untouched workspace by definition: measured across the verified
        # core, 303 of 374 checks (81%) are guards and the mean raw floor is
        # 0.815. The gate was asking for something no well-formed task can
        # satisfy.
        #
        # The property actually worth gating is the one the benchmark now
        # reports: doing nothing scores zero on the DISCRIMINATIVE checks, the
        # ones that fail on a pristine workspace. That is zero by construction,
        # so the substantive half of the test is that the discriminative set is
        # non-empty; a task with no discriminative check cannot tell any two
        # submissions apart and must not be admitted.
        #
        # The raw floor is kept in the record, unchanged, because it is the
        # measure of how much of a reported score was credit for not
        # vandalising the workspace.
        checks_a1 = (score_a1.get("secondary") or {}).get("checks") \
            or score_a1.get("checklist") or []
        n_guard = sum(1 for c in checks_a1 if isinstance(c, dict) and c.get("ok"))
        n_disc = sum(1 for c in checks_a1 if isinstance(c, dict) and not c.get("ok"))
        rec["gates"]["G1"] = {
            "verdict": "pass" if n_disc > 0 else "fail",
            "floor": floor,
            "discriminative_floor": 0.0 if n_disc > 0 else None,
            "n_guard": n_guard, "n_discriminative": n_disc,
            "criterion": "discriminative set non-empty; scored floor is 0 by construction",
        }

    # G2
    rec["gates"]["G2"] = {"verdict": "fail" if pass_a1 else "pass", "pristine_pass": pass_a1}

    # G7
    rec["gates"]["G7"] = {
        "verdict": "fail" if to_a1 else "pass",
        "grade_seconds": round(el_a1, 2),
        "cap_seconds": HARNESS_GRADE_CAP_S,
    }

    # G6. Prefer the checklist when every entry's status resolves; otherwise fall
    # back to the grader's own checks_passed/checks_total counters. The source is
    # recorded so the number can be traced.
    sec_a1 = score_a1.get("secondary") or {}
    # Duplicate check ids would collapse in the id->status map and undercount the
    # total, which would flatter G6; fall back to the counters in that case.
    if st_a1 is not None and len(st_a1) == len(cl_a1):
        source, total, free = "checklist", len(st_a1), sum(1 for v in st_a1.values() if v)
    else:
        source = "counts"
        total = sec_a1.get("checks_total")
        free = sec_a1.get("checks_passed")
    if isinstance(total, int) and total > 0 and isinstance(free, int):
        disc = total - free
        rec["gates"]["G6"] = {
            "verdict": "pass" if disc / total >= 0.5 else "fail",
            "source": source, "checks_total": total, "free": free, "discriminative": disc,
            "discriminative_frac": round(disc / total, 4),
        }
    else:
        rec["gates"]["G6"] = {"verdict": "error", "detail": "grader reported no usable checks",
                              "source": source, "checks_total": total, "free": free}

    # G4: second grade on the SAME directory
    with _MaybeLock(_FIXED_TMP_LOCK, bool(tmp_paths)):
        score_a2, el_a2, to_a2 = invoke_grader(task_id, task_dir_a, run_a, timeout_s)
    n1 = normalized_score_text(score_a1, workdir)
    n2 = normalized_score_text(score_a2, workdir)
    rec["gates"]["G4"] = {
        "verdict": "pass" if n1 == n2 else "fail",
        "repeat_partial_score": partial_of(score_a2),
        "repeat_pass": bool(score_a2.get("pass")),
        "repeat_grade_seconds": round(el_a2, 2),
        "repeat_timed_out": to_a2,
    }
    if n1 != n2:
        rec["gates"]["G4"]["diff_sample"] = _first_diff(n1, n2)

    # --- Stage B: pristine + passing attestation (advisory) ---------------
    if cfg["measure_attestation"]:
        try:
            run_b, task_dir_b = stage(task_id, run_root, seed)
            write_passing_attestation(run_b, task_id)
            with _MaybeLock(_FIXED_TMP_LOCK, bool(tmp_paths)):
                score_b, el_b, to_b = invoke_grader(task_id, task_dir_b, run_b, timeout_s)
            floor_att = partial_of(score_b)
            rec["advisory"]["attestation"] = {
                "floor_attested": floor_att,
                "pass_attested": bool(score_b.get("pass")),
                "attestation_credit": (None if (floor_att is None or floor is None)
                                       else round(floor_att - floor, 4)),
                "grade_seconds": round(el_b, 2),
                "timed_out": to_b,
            }
            if not cfg["keep_runs"]:
                shutil.rmtree(run_b, ignore_errors=True)
        except Exception as exc:
            rec["errors"].append(f"attestation_probe: {type(exc).__name__}: {exc}")

    # --- Stage C: reference solution -> G3 --------------------------------
    patch_path = os.path.join(task_dir, "reference", "patch.diff")
    if not os.path.isfile(patch_path):
        rec["gates"]["G3"] = {"verdict": "unknown", "detail": "no tasks/<id>/reference/patch.diff"}
    else:
        try:
            run_c, task_dir_c = stage(task_id, run_root, seed)
            appl = apply_reference_patch(task_id, task_dir_c,
                                         os.path.join(run_c, "workspace"), seed)
            appl_summary = {k: appl.get(k) for k in (
                "method", "base_source", "hunks_total", "hunks_applied",
                "hunks_already", "hunks_failed", "files_total", "files_applied",
                "files_already", "files_failed", "files_out_of_scope",
                "files_unsupported", "no_effective_change", "notes")}
            if not appl["applied"]:
                rec["gates"]["G3"] = {
                    "verdict": "fail",
                    "detail": "reference could not be applied by any method",
                    "outcome": "c_unappliable",
                    "application": appl_summary,
                    "file_outcomes": appl.get("file_outcomes", [])[:20],
                }
            else:
                with _MaybeLock(_FIXED_TMP_LOCK, bool(tmp_paths)):
                    score_c, el_c, to_c = invoke_grader(task_id, task_dir_c, run_c, timeout_s)
                ref_partial = partial_of(score_c)
                ref_pass = bool(score_c.get("pass"))
                ok = (ref_partial == 1.0) and ref_pass
                rec["gates"]["G3"] = {
                    "verdict": "pass" if ok else "fail",
                    # a = validated, b = the grader rejects the upstream fix.
                    "outcome": "a_validated" if ok else "b_grader_rejects_reference",
                    "reference_partial_score": ref_partial,
                    "reference_pass": ref_pass,
                    "apply_method": appl["method"],
                    "application": appl_summary,
                    "no_effective_change": appl.get("no_effective_change"),
                    "grade_seconds": round(el_c, 2),
                    "timed_out": to_c,
                }
                # Strict discriminative count needs both endpoints.
                st_c = checklist_statuses(checklist_of(score_c))
                if st_a1 is not None and st_c is not None:
                    strict = [k for k, v in st_a1.items() if not v and st_c.get(k)]
                    rec["gates"]["G6"]["strict_discriminative"] = len(strict)
                    rec["gates"]["G6"]["strict_discriminative_ids"] = sorted(strict)
            if not cfg["keep_runs"]:
                shutil.rmtree(run_c, ignore_errors=True)
        except Exception as exc:
            rec["errors"].append(f"reference_probe: {type(exc).__name__}: {exc}")
            rec["gates"]["G3"] = {"verdict": "error", "detail": str(exc)[:300]}

    if not cfg["keep_runs"]:
        shutil.rmtree(run_a, ignore_errors=True)

    verdicts = {g: rec["gates"][g]["verdict"] for g in GATE_IDS}
    rec["verdicts"] = verdicts
    rec["admitted_strict"] = all(verdicts[g] == "pass" for g in GATE_IDS)
    rec["admitted_pending_reference"] = (
        all(verdicts[g] == "pass" for g in ("G1", "G2", "G4", "G5", "G6", "G7"))
        and verdicts["G3"] in ("pass", "unknown")
    )
    return rec


def _first_diff(a: str, b: str) -> dict:
    for i, (ca, cb) in enumerate(zip(a, b)):
        if ca != cb:
            lo = max(0, i - 60)
            return {"offset": i, "run1": a[lo:i + 60], "run2": b[lo:i + 60]}
    return {"offset": min(len(a), len(b)), "run1": a[-120:], "run2": b[-120:]}


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def corpus_static_scan(use_cache: bool = True) -> dict:
    """Apply the two static checks (G5 and the workspace-script advisory) to
    EVERY grader in tasks/, not just the sampled scope.

    Static checks cost a file read, so there is no reason to sample them. This
    gives the corpus-level denominator that the 150-task sweep cannot.
    """
    # 800+ file reads over a network filesystem, so the result is cached beside
    # the ledger. Delete admission_corpus_static.json, or pass --rescan-corpus,
    # to force a fresh scan after graders change.
    if use_cache and os.path.isfile(CORPUS_STATIC_PATH):
        try:
            cached = json.load(open(CORPUS_STATIC_PATH, encoding="utf-8"))
            cached["from_cache"] = True
            return cached
        except (OSError, json.JSONDecodeError):
            pass

    per_kind: dict[str, int] = {}
    n = clean = net = venv = wsx = tmpx = 0
    for tid in gradeable_tasks():
        path = os.path.join(TASKS_DIR, tid, "grade.sh")
        h = static_hermeticity(path)
        if not h.get("readable"):
            continue
        n += 1
        if h["network"]:
            net += 1
        if h["venv"]:
            venv += 1
        if not h["network"] and not h["venv"]:
            clean += 1
        for k in {x["kind"] for x in h["network"] + h["venv"]}:
            per_kind[k] = per_kind.get(k, 0) + 1
        if workspace_executed_scripts(path):
            wsx += 1
        if fixed_tmp_paths(path):
            tmpx += 1
    out = {
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "from_cache": False,
        "graders_scanned": n,
        "g5_clean": clean,
        "g5_clean_frac": round(clean / n, 4) if n else None,
        "with_grade_time_network": net,
        "with_venv_path_reference": venv,
        "executes_workspace_script": wsx,
        "fixed_tmp_path": tmpx,
        "tasks_per_kind": dict(sorted(per_kind.items(), key=lambda kv: -kv[1])),
    }
    try:
        os.makedirs(OUT_DIR, exist_ok=True)
        with open(CORPUS_STATIC_PATH, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2)
    except OSError:
        pass
    return out


def summarize(records: list[dict], meta: dict) -> dict:
    def bucket(rs):
        out = {"n": len(rs)}
        for g in GATE_IDS:
            c = {"pass": 0, "fail": 0, "unknown": 0, "error": 0}
            for r in rs:
                c[r.get("verdicts", {}).get(g, "error")] += 1
            out[g] = c
        out["admitted_strict"] = sum(1 for r in rs if r.get("admitted_strict"))
        out["admitted_pending_reference"] = sum(1 for r in rs if r.get("admitted_pending_reference"))
        floors = [r["gates"]["G1"].get("floor") for r in rs
                  if r.get("gates", {}).get("G1", {}).get("floor") is not None]
        if floors:
            floors_sorted = sorted(floors)
            out["floor"] = {
                "n": len(floors),
                "mean": round(sum(floors) / len(floors), 4),
                "median": round(floors_sorted[len(floors_sorted) // 2], 4),
                "zero": sum(1 for f in floors if f == 0.0),
                "ge_0_5": sum(1 for f in floors if f >= 0.5),
                "eq_1_0": sum(1 for f in floors if f >= 1.0),
                "max": max(floors),
            }
        credits = [r["advisory"]["attestation"]["attestation_credit"] for r in rs
                   if r.get("advisory", {}).get("attestation", {}).get("attestation_credit") is not None]
        if credits:
            out["attestation_credit"] = {
                "n": len(credits),
                "mean": round(sum(credits) / len(credits), 4),
                "nonzero": sum(1 for c in credits if c > 0),
                "max": round(max(credits), 4),
            }
        att_floor = [r["advisory"]["attestation"]["floor_attested"] for r in rs
                     if r.get("advisory", {}).get("attestation", {}).get("floor_attested") is not None]
        if att_floor:
            out["floor_attested_mean"] = round(sum(att_floor) / len(att_floor), 4)
            out["free_pass_when_attested"] = sum(
                1 for r in rs if r.get("advisory", {}).get("attestation", {}).get("pass_attested"))
        checks = [(r["gates"]["G6"].get("checks_total"), r["gates"]["G6"].get("free"))
                  for r in rs if isinstance(r.get("gates", {}).get("G6", {}).get("checks_total"), int)
                  and isinstance(r["gates"]["G6"].get("free"), int)]
        if checks:
            tot = sum(c[0] for c in checks)
            fre = sum(c[1] for c in checks)
            out["checks"] = {"executed": tot, "free": fre,
                             "free_frac": round(fre / tot, 4) if tot else None}
        return out

    lb = [r for r in records if r.get("scope") == "lb90"]
    sm = [r for r in records if r.get("scope") == "sample60"]

    herm = {}
    for r in records:
        for k in r.get("gates", {}).get("G5", {}).get("kinds", []) or []:
            herm[k] = herm.get(k, 0) + 1

    fam = {}
    for r in records:
        f = r.get("family", "?")
        d = fam.setdefault(f, {"n": 0, "admitted_strict": 0, "admitted_pending_reference": 0,
                               "floor_sum": 0.0, "floor_n": 0})
        d["n"] += 1
        d["admitted_strict"] += 1 if r.get("admitted_strict") else 0
        d["admitted_pending_reference"] += 1 if r.get("admitted_pending_reference") else 0
        fl = r.get("gates", {}).get("G1", {}).get("floor")
        if fl is not None:
            d["floor_sum"] += fl
            d["floor_n"] += 1
    for f, d in fam.items():
        d["mean_floor"] = round(d["floor_sum"] / d["floor_n"], 4) if d["floor_n"] else None
        d.pop("floor_sum")

    arts = {k: sum(1 for r in records if r.get("artifacts", {}).get(k))
            for k in ("grade_sh", "task_yaml", "spec_md", "brief_md", "reference_patch")}

    # Grading effort read back out of the records, so it stays correct when the
    # ledger is rebuilt from the checkpoint with --summarize-only.
    inv, secs = 0, 0.0
    for r in records:
        for v in (r.get("pristine", {}).get("grade_seconds"),
                  r.get("gates", {}).get("G4", {}).get("repeat_grade_seconds"),
                  r.get("advisory", {}).get("attestation", {}).get("grade_seconds"),
                  r.get("gates", {}).get("G3", {}).get("grade_seconds")):
            if isinstance(v, (int, float)):
                inv += 1
                secs += v
    grading = {"grader_invocations": inv, "grader_seconds_total": round(secs, 1),
               "grader_seconds_mean": round(secs / inv, 2) if inv else None}

    evaluated_at = sorted(r["evaluated_at"] for r in records if r.get("evaluated_at"))
    span = {"first_task_evaluated_at": evaluated_at[0] if evaluated_at else None,
            "last_task_evaluated_at": evaluated_at[-1] if evaluated_at else None}

    ws_exec_tasks = sorted(r["task_id"] for r in records
                           if r.get("advisory", {}).get("workspace_executed_scripts"))
    tmp_unsafe_tasks = sorted(r["task_id"] for r in records if r.get("concurrency_unsafe"))

    try:
        corpus = corpus_static_scan(use_cache=not meta.get("rescan_corpus"))
    except Exception as exc:  # never let an advisory scan break the ledger
        corpus = {"error": f"{type(exc).__name__}: {exc}"}

    return {
        "meta": meta,
        "corpus_static": corpus,
        "overall": bucket(records),
        "lb90": bucket(lb),
        "sample60": bucket(sm),
        "by_family": dict(sorted(fam.items(), key=lambda kv: -kv[1]["n"])),
        "hermeticity_kinds": dict(sorted(herm.items(), key=lambda kv: -kv[1])),
        "artifact_presence": arts,
        "grading_effort": grading,
        "evaluation_span": span,
        "grader_executes_workspace_script": {
            "n": len(ws_exec_tasks), "task_ids": ws_exec_tasks},
        "grader_fixed_tmp_path": {
            "n": len(tmp_unsafe_tasks), "task_ids": tmp_unsafe_tasks},
        "gate_titles": GATE_TITLES,
    }


def render_markdown(summary: dict, records: list[dict]) -> str:
    m, ov, lb, sm = summary["meta"], summary["overall"], summary["lb90"], summary["sample60"]
    L = []
    A = L.append
    A("# TeamBench Task Admission Gate")
    A("")
    A(f"Generated {m['generated_at']} from commit `{m.get('git_commit', 'unknown')}` "
      f"on branch `{m.get('git_branch', 'unknown')}`.")
    A("")
    A(f"Regenerate with: `python3 scripts/task_admission_gate.py --bootstrap`")
    A("")
    if not m.get("complete", True):
        A(f"> **Partial run.** {m.get('evaluated')} of {m.get('scope_size')} scoped tasks have "
          f"been evaluated so far. Every number below describes only those tasks. "
          f"Re-run without `--no-resume` to continue from the checkpoint.")
        A("")
    A(f"Scope: {ov['n']} tasks at seed {m['seed']} "
      f"({lb['n']} leaderboard tasks + {sm['n']} randomly sampled from the rest, "
      f"`random.Random({m['sample_seed']})`).")
    A("")
    A("## Gate results")
    A("")
    A("| Gate | Requirement | Pass | Fail | Unknown | Error |")
    A("|---|---|---:|---:|---:|---:|")
    for g in GATE_IDS:
        c = ov[g]
        A(f"| {g} | {GATE_TITLES[g]} | {c['pass']} | {c['fail']} | {c['unknown']} | {c['error']} |")
    A("")
    A("## Admission")
    A("")
    A("| | All tasks | Leaderboard 90 | Sample 60 |")
    A("|---|---:|---:|---:|")
    A(f"| Tasks evaluated | {ov['n']} | {lb['n']} | {sm['n']} |")
    A(f"| **Pass ALL seven gates** | **{ov['admitted_strict']}** | "
      f"**{lb['admitted_strict']}** | **{sm['admitted_strict']}** |")
    A(f"| Pass six gates, G3 unknown or pass | {ov['admitted_pending_reference']} | "
      f"{lb['admitted_pending_reference']} | {sm['admitted_pending_reference']} |")
    A("")
    A("`Pass ALL seven gates` is the honest size of the benchmark. The second row is the "
      "ceiling that becomes reachable once every task has a reference solution proving G3; "
      "it is not a substitute for it.")
    A("")
    A("Why the second row is not a substitute, concretely: `GH120_redis-py_3863` is a 22-line "
      "stub grader that writes `partial_score: 0.0` for every submission. Its floor is 0.0, it "
      "never free-passes, it is perfectly deterministic, it touches no network, its single "
      "check is never free, and it finishes instantly. It satisfies six of the seven gates. "
      "Only G3 can reject it, because no reference solution can ever score 1.0 against a "
      "grader that returns 0.0 unconditionally. A task with no demonstrated solution has not "
      "been shown to be solvable, and G3 `unknown` must never be counted as a pass.")
    A("")
    A("## G1: the pristine floor")
    A("")
    A("Score awarded for staging the workspace and doing nothing at all.")
    A("")
    A("| | All tasks | Leaderboard 90 | Sample 60 |")
    A("|---|---:|---:|---:|")
    for label, key in [("Tasks measured", "n"), ("Mean floor", "mean"), ("Median floor", "median"),
                       ("Floor == 0.00 (clean)", "zero"), ("Floor >= 0.50", "ge_0_5"),
                       ("Floor == 1.00", "eq_1_0"), ("Max floor", "max")]:
        row = [str(b.get("floor", {}).get(key, "n/a")) for b in (ov, lb, sm)]
        A(f"| {label} | {row[0]} | {row[1]} | {row[2]} |")
    A("")
    if ov.get("checks"):
        c = ov["checks"]
        A(f"Across all evaluated tasks, {c['free']} of {c['executed']} executed checks "
          f"({c['free_frac']:.1%}) pass on the untouched workspace.")
        A("")
    A("## Advisory: attestation credit")
    A("")
    A("`submission/attestation.json` is a scored check in many graders. These rows re-grade the "
      "same untouched workspace after writing the harness's own passing-attestation stub "
      "(`harness.ablation._write_passing_attestation`), which is exactly what the "
      "`team_no_verify` condition writes automatically. This is score a do-nothing agent "
      "collects for filing a report.")
    A("")
    A("| | All tasks | Leaderboard 90 | Sample 60 |")
    A("|---|---:|---:|---:|")
    A(f"| Mean floor, bare | {ov.get('floor', {}).get('mean', 'n/a')} | "
      f"{lb.get('floor', {}).get('mean', 'n/a')} | {sm.get('floor', {}).get('mean', 'n/a')} |")
    A(f"| Mean floor, with attestation | {ov.get('floor_attested_mean', 'n/a')} | "
      f"{lb.get('floor_attested_mean', 'n/a')} | {sm.get('floor_attested_mean', 'n/a')} |")
    for label, key in [("Tasks where attestation adds score", "nonzero"),
                       ("Mean credit", "mean"), ("Max credit", "max")]:
        row = [str(b.get("attestation_credit", {}).get(key, "n/a")) for b in (ov, lb, sm)]
        A(f"| {label} | {row[0]} | {row[1]} | {row[2]} |")
    A(f"| Tasks reaching pass=true with attestation alone | "
      f"{ov.get('free_pass_when_attested', 'n/a')} | {lb.get('free_pass_when_attested', 'n/a')} | "
      f"{sm.get('free_pass_when_attested', 'n/a')} |")
    A("")
    A("## G5: what the static hermeticity scan found")
    A("")
    A("| Violation kind | Tasks |")
    A("|---|---:|")
    for k, v in summary["hermeticity_kinds"].items():
        A(f"| {k} | {v} |")
    if not summary["hermeticity_kinds"]:
        A("| (none) | 0 |")
    A("")
    cs = summary.get("corpus_static", {})
    if cs.get("graders_scanned"):
        A("## Corpus-wide static scan (all graders, not just the sampled scope)")
        A("")
        A("The two static checks cost only a file read, so they were run over every "
          "`tasks/*/grade.sh` in the repository.")
        A("")
        A("| Measure | Tasks | of |")
        A("|---|---:|---:|")
        tot = cs["graders_scanned"]
        A(f"| Graders scanned | {tot} | {tot} |")
        A(f"| Pass G5 (no grade-time network, no venv-path reference) | {cs['g5_clean']} | {tot} |")
        A(f"| Install packages or fetch over the network at grade time | "
          f"{cs['with_grade_time_network']} | {tot} |")
        A(f"| Reference a gitignored or image-only venv path | "
          f"{cs['with_venv_path_reference']} | {tot} |")
        A(f"| Execute a script inside the agent-writable workspace | "
          f"{cs['executes_workspace_script']} | {tot} |")
        A(f"| Write to a fixed (host-shared) `/tmp` path | {cs.get('fixed_tmp_path', 'n/a')} | {tot} |")
        A("")
        A("| Violation kind | Tasks |")
        A("|---|---:|")
        for k, v in cs.get("tasks_per_kind", {}).items():
            A(f"| {k} | {v} |")
        A("")
    A("## By task family")
    A("")
    A("| Family | Tasks | Mean floor | Pass all 7 | Pass 6, G3 unknown |")
    A("|---|---:|---:|---:|---:|")
    for f, d in summary["by_family"].items():
        A(f"| {f} | {d['n']} | {d['mean_floor']} | {d['admitted_strict']} | "
          f"{d['admitted_pending_reference']} |")
    A("")
    A("## Artifact presence")
    A("")
    A("| Artifact | Tasks with it | of |")
    A("|---|---:|---:|")
    for k, v in summary["artifact_presence"].items():
        A(f"| `{k}` | {v} | {ov['n']} |")
    A("")
    A("A task with no on-disk `spec.md` hands the agent an empty specification: no harness "
      "caller writes a generator's in-memory spec to `task_dir` at run time.")
    A("")
    tu = summary["grader_fixed_tmp_path"]
    A("## Advisory: graders that write to a fixed `/tmp` path")
    A("")
    A(f"{tu['n']} of {ov['n']} evaluated graders write intermediate results to a literal "
      "`/tmp/...` path rather than a per-process one. Two grades of such a task running "
      "anywhere on the same host at the same time overwrite each other's file and both report "
      "whatever the loser wrote, so the task's score depends on what else the machine is doing. "
      "This sweep serialises its own invocations of these graders; it cannot serialise other "
      "processes on the host, so these rows carry residual risk.")
    if tu["task_ids"]:
        A("")
        for t in tu["task_ids"]:
            A(f"- `{t}`")
    A("")
    we = summary["grader_executes_workspace_script"]
    A("## Advisory: graders that execute a script inside the agent's workspace")
    A("")
    A(f"{we['n']} of {ov['n']} evaluated graders run a relative script after `cd`-ing into the "
      "workspace the agent can write. The agent controls that file, so it controls its own score.")
    if we["task_ids"]:
        A("")
        for t in we["task_ids"]:
            A(f"- `{t}`")
    A("")
    worst = sorted((r for r in records if r.get("gates", {}).get("G1", {}).get("floor") is not None),
                   key=lambda r: -r["gates"]["G1"]["floor"])[:25]
    A("## Worst 25 pristine floors")
    A("")
    A("| Task | Scope | Floor | Pristine pass | Free / total checks | Gates failed |")
    A("|---|---|---:|---|---|---|")
    for r in worst:
        g6 = r["gates"]["G6"]
        failed = ",".join(g for g in GATE_IDS if r.get("verdicts", {}).get(g) == "fail")
        A(f"| `{r['task_id']}` | {r['scope']} | {r['gates']['G1']['floor']} | "
          f"{r['pristine']['pass']} | {g6.get('free', '?')}/{g6.get('checks_total', '?')} | "
          f"{failed or '-'} |")
    A("")
    A("## Reproduction")
    A("")
    A(f"- Interpreter: `{m['python_executable']}` ({m['python_version']})")
    A(f"- Staging: `harness.run_all.setup_run`, unmodified, seed {m['seed']}")
    A(f"- Grading: `grade.sh` via a parameterised copy of `harness.run_all.grade_run` "
      f"(timeout {m['grade_timeout']} s; harness cap {HARNESS_GRADE_CAP_S} s)")
    ge = summary.get("grading_effort", {})
    sp = summary.get("evaluation_span", {})
    A(f"- Grader invocations: {ge.get('grader_invocations')} "
      f"({ge.get('grader_seconds_total')} s of grader time, "
      f"mean {ge.get('grader_seconds_mean')} s per invocation)")
    A(f"- Tasks evaluated between {sp.get('first_task_evaluated_at')} and "
      f"{sp.get('last_task_evaluated_at')}")
    if m.get("summarize_only"):
        A("- This page was rebuilt from the checkpoint with `--summarize-only`; it evaluated "
          "nothing itself. The numbers above come from the recorded per-task results.")
    A(f"- 1/5/15-minute load average when the summary was written: "
      f"{m.get('loadavg', 'n/a')}")
    A(f"- `harness/grader_helpers.sh` sha256: "
      f"`{str(m.get('grader_helpers_sha256'))[:16]}...` (sourced by most graders)")
    A("- Every task record carries the sha256 and mtime of the `grade.sh` that was actually "
      "run, so a verdict can be rechecked against the exact grader bytes it was derived from. "
      "Graders in this repository are under active repair; a record whose hash no longer "
      "matches the file on disk describes a grader that has since changed.")
    A("- G7 is wall-clock on this machine. Grader timings scale with whatever else the "
      "machine is running, so a G7 failure should be reconfirmed on an idle host before it "
      "is reported as a property of the task. Every invocation's `grade_seconds` is in the "
      "ledger.")
    if m.get("pip_delta"):
        A(f"- Packages installed into the throwaway venv by graders during the sweep: "
          f"{len(m['pip_delta'])} -> {', '.join(m['pip_delta'][:20])}")
    else:
        A("- Packages installed into the throwaway venv by graders during the sweep: 0")
    A("")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------------------
# Bootstrap / environment guard
# ---------------------------------------------------------------------------

def repo_venv_paths() -> list[str]:
    return [os.path.join(REPO_ROOT, "venv"), os.path.join(REPO_ROOT, ".venv")]


def build_gate_venv(path: str) -> str:
    """Throwaway venv whose sys.path includes the repo venv's site-packages.

    Graders run `pip install` at grade time. Running under the repo venv would
    mutate it, concurrently, from several workers. This venv reads the canonical
    dependency set through a .pth file and absorbs any write.
    """
    py = os.path.join(path, "bin", "python")
    if not os.path.isfile(py):
        base = sys.base_prefix
        base_py = os.path.join(base, "bin", "python3")
        if not os.path.isfile(base_py):
            base_py = shutil.which("python3") or sys.executable
        subprocess.run([base_py, "-m", "venv", path], check=True, capture_output=True)
    ver = f"python{sys.version_info.major}.{sys.version_info.minor}"
    sp = os.path.join(path, "lib", ver, "site-packages")
    os.makedirs(sp, exist_ok=True)
    lines = [REPO_ROOT]
    for v in repo_venv_paths():
        cand = os.path.join(v, "lib", ver, "site-packages")
        if os.path.isdir(cand):
            lines.append(cand)
    with open(os.path.join(sp, "_zz_teambench_repo_venv.pth"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return py


def pip_freeze() -> list[str]:
    try:
        r = subprocess.run([sys.executable, "-m", "pip", "freeze", "--local"],
                           capture_output=True, text=True, timeout=180)
        return sorted(l.strip() for l in r.stdout.splitlines() if l.strip())
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Parity check
# ---------------------------------------------------------------------------

def parity_check(task_ids: list[str], workdir: str, seed: int) -> dict:
    """Assert invoke_grader() matches the unmodified harness grade_run()."""
    from harness.run_all import grade_run as harness_grade_run
    out = []
    for t in task_ids:
        run_h, td = stage(t, os.path.join(workdir, "parity"), seed)
        s_h = harness_grade_run(t, td, run_h)
        run_g, td2 = stage(t, os.path.join(workdir, "parity"), seed)
        s_g, _, _ = invoke_grader(t, td2, run_g, HARNESS_GRADE_CAP_S)
        same = normalized_score_text(s_h, workdir) == normalized_score_text(s_g, workdir)
        out.append({"task_id": t, "identical": same,
                    "harness_partial": partial_of(s_h), "gate_partial": partial_of(s_g)})
        shutil.rmtree(run_h, ignore_errors=True)
        shutil.rmtree(run_g, ignore_errors=True)
    return {"n": len(out), "identical": sum(1 for o in out if o["identical"]), "detail": out}


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
# Two synthetic tasks are built in a temporary tasks tree and run through the
# same evaluate_task() the sweep uses. One is constructed to satisfy every gate,
# the other to violate G1, G5 and G6. If the gate cannot separate them, its
# verdicts on the real corpus mean nothing, so --selftest exits non-zero.

_SELFTEST_GOOD_APP = """def add(a, b):
    return a - b
"""

_SELFTEST_GOOD_GRADE = r"""#!/usr/bin/env bash
set -uo pipefail
WORKSPACE="$1"; REPORTS="$2"
cd "$WORKSPACE"
res=$(python3 - <<'EOF'
import json, importlib.util
spec = importlib.util.spec_from_file_location("app", "app.py")
mod = importlib.util.module_from_spec(spec)
out = {}
try:
    spec.loader.exec_module(mod)
    out["C1"] = mod.add(1, 2) == 3
    out["C2"] = mod.add(5, 3) == 8
    out["C3"] = mod.add(-1, -1) == -2
except Exception:
    out = {"C1": False, "C2": False, "C3": False}
out["C4"] = "a + b" in open("app.py").read()
print(json.dumps(out))
EOF
)
mkdir -p "$REPORTS"
python3 - "$res" "$REPORTS/score.json" <<'EOF'
import json, sys
d = json.loads(sys.argv[1])
cl = [{"id": k, "ok": bool(d[k]), "note": k} for k in sorted(d)]
n = sum(1 for c in cl if c["ok"])
json.dump({"pass": n == len(cl), "primary": {"success": int(n == len(cl))},
           "secondary": {"partial_score": round(n / len(cl), 2),
                         "checks_passed": n, "checks_total": len(cl)},
           "failure_modes": [], "checklist": cl}, open(sys.argv[2], "w"), indent=2)
EOF
"""

_SELFTEST_GOOD_PATCH = """--- a/app.py
+++ b/app.py
@@ -1,2 +1,2 @@
 def add(a, b):
-    return a - b
+    return a + b
"""

_SELFTEST_BAD_APP = '\n'.join([
    '"""A module."""',
    "",
    "",
    "def add(a, b):",
    "    return a - b",
    "",
])

_SELFTEST_BAD_GRADE = r"""#!/usr/bin/env bash
set -uo pipefail
WORKSPACE="$1"; REPORTS="$2"
cd "$WORKSPACE"
pip install pytest -q 2>/dev/null || true
res=$(python3 - <<'EOF'
import json, ast
src = open("app.py").read()
out = {}
out["C1"] = True
try:
    tree = ast.parse(src)
    out["C2"] = True
    out["C3"] = ast.get_docstring(tree) is not None
except Exception:
    out["C2"] = out["C3"] = False
out["C4"] = "a + b" in src
print(json.dumps(out))
EOF
)
mkdir -p "$REPORTS"
python3 - "$res" "$REPORTS/score.json" <<'EOF'
import json, sys
d = json.loads(sys.argv[1])
cl = [{"id": k, "ok": bool(d[k]), "note": k} for k in sorted(d)]
n = sum(1 for c in cl if c["ok"])
json.dump({"pass": n == len(cl), "primary": {"success": int(n == len(cl))},
           "secondary": {"partial_score": round(n / len(cl), 2),
                         "checks_passed": n, "checks_total": len(cl)},
           "failure_modes": [], "checklist": cl}, open(sys.argv[2], "w"), indent=2)
EOF
"""


def _write_selftest_tasks(root: str) -> None:
    good = os.path.join(root, "SELFTEST_GOOD")
    os.makedirs(os.path.join(good, "workspace"), exist_ok=True)
    os.makedirs(os.path.join(good, "reference"), exist_ok=True)
    open(os.path.join(good, "workspace", "app.py"), "w").write(_SELFTEST_GOOD_APP)
    open(os.path.join(good, "grade.sh"), "w").write(_SELFTEST_GOOD_GRADE)
    open(os.path.join(good, "reference", "patch.diff"), "w").write(_SELFTEST_GOOD_PATCH)

    bad = os.path.join(root, "SELFTEST_BAD")
    os.makedirs(os.path.join(bad, "workspace"), exist_ok=True)
    open(os.path.join(bad, "workspace", "app.py"), "w").write(_SELFTEST_BAD_APP)
    open(os.path.join(bad, "grade.sh"), "w").write(_SELFTEST_BAD_GRADE)


def selftest(workdir: str) -> bool:
    """Build two synthetic tasks with known properties and check the gate's verdicts."""
    global TASKS_DIR
    root = os.path.join(workdir, "selftest_tasks")
    shutil.rmtree(root, ignore_errors=True)
    os.makedirs(root, exist_ok=True)
    _write_selftest_tasks(root)

    real_tasks_dir = TASKS_DIR
    TASKS_DIR = root
    cfg = {"workdir": workdir, "seed": 0, "grade_timeout": 120,
           "keep_runs": False, "measure_attestation": True}
    try:
        good = evaluate_task({"task_id": "SELFTEST_GOOD", "scope": "selftest"}, cfg)
        bad = evaluate_task({"task_id": "SELFTEST_BAD", "scope": "selftest"}, cfg)
    finally:
        TASKS_DIR = real_tasks_dir

    expect_good = {"G1": "pass", "G2": "pass", "G3": "pass", "G4": "pass",
                   "G5": "pass", "G6": "pass", "G7": "pass"}
    expect_bad = {"G1": "fail", "G2": "pass", "G3": "unknown", "G4": "pass",
                  "G5": "fail", "G6": "fail", "G7": "pass"}

    ok = True
    for name, rec, expect, admit in (("SELFTEST_GOOD", good, expect_good, True),
                                     ("SELFTEST_BAD", bad, expect_bad, False)):
        got = rec.get("verdicts", {})
        for g in GATE_IDS:
            if got.get(g) != expect[g]:
                print(f"  SELFTEST FAIL {name} {g}: expected {expect[g]}, got {got.get(g)} "
                      f"-- {rec['gates'].get(g)}", file=sys.stderr)
                ok = False
        if bool(rec.get("admitted_strict")) != admit:
            print(f"  SELFTEST FAIL {name}: admitted_strict expected {admit}, "
                  f"got {rec.get('admitted_strict')}", file=sys.stderr)
            ok = False
        if rec.get("errors"):
            print(f"  SELFTEST FAIL {name}: errors {rec['errors']}", file=sys.stderr)
            ok = False
    print(f"  SELFTEST_GOOD floor={good['gates']['G1'].get('floor')} "
          f"reference={good['gates']['G3'].get('reference_partial_score')} "
          f"admitted={good.get('admitted_strict')}")
    print(f"  SELFTEST_BAD  floor={bad['gates']['G1'].get('floor')} "
          f"free={bad['gates']['G6'].get('free')}/{bad['gates']['G6'].get('checks_total')} "
          f"admitted={bad.get('admitted_strict')}")
    shutil.rmtree(root, ignore_errors=True)
    return ok


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def git_info() -> dict:
    def run(*a):
        try:
            return subprocess.run(a, cwd=REPO_ROOT, capture_output=True, text=True,
                                  timeout=30).stdout.strip()
        except Exception:
            return ""
    return {"git_commit": run("git", "rev-parse", "--short", "HEAD"),
            "git_branch": run("git", "rev-parse", "--abbrev-ref", "HEAD")}


def main() -> int:
    ap = argparse.ArgumentParser(
        description="TeamBench task admission gate (G1-G7).",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workdir", default=None,
                    help="Scratch dir for staged runs and the throwaway venv.")
    ap.add_argument("--seed", type=int, default=0, help="Task instance seed (default 0).")
    ap.add_argument("--sample-size", type=int, default=60,
                    help="Tasks sampled from outside the leaderboard (default 60).")
    ap.add_argument("--reference-sample", type=int, default=0,

                    help="Extra tasks drawn only from those that have a "

                         "reference patch, so G3 is evaluable on a defined "

                         "population instead of on whatever the uniform "

                         "sample happened to include.")
    ap.add_argument("--sample-seed", type=int, default=0,
                    help="Seed for the random sample (default 0).")
    ap.add_argument("--tasks", nargs="*", default=None, help="Evaluate only these task ids.")
    ap.add_argument("--workers", type=int, default=4, help="Concurrent tasks (default 4).")
    ap.add_argument("--grade-timeout", type=int, default=HARNESS_GRADE_CAP_S,
                    help=f"Per-grader timeout in seconds (default {HARNESS_GRADE_CAP_S}, "
                         "the harness cap; G7 is always judged against the harness cap).")
    ap.add_argument("--no-attestation", action="store_true",
                    help="Skip the advisory attestation-credit probe (one less grade per task).")
    ap.add_argument("--keep-runs", action="store_true", help="Do not delete staged run dirs.")
    ap.add_argument("--no-resume", action="store_true", help="Ignore the existing checkpoint.")
    ap.add_argument("--rescan-corpus", action="store_true",
                    help="Force a fresh corpus-wide static scan instead of reusing "
                         "admission_corpus_static.json.")
    ap.add_argument("--summarize-only", action="store_true",
                    help="Evaluate nothing. Rebuild admission_ledger.json and "
                         "admission_summary.md from whatever is already in the checkpoint. "
                         "Safe to run while a sweep is in progress; the summary then describes "
                         "the tasks completed so far and says so.")
    ap.add_argument("--bootstrap", action="store_true",
                    help="Build the throwaway grading venv and re-exec inside it.")
    ap.add_argument("--allow-shared-venv", action="store_true",
                    help="Permit running under the repository venv (grade-time pip installs "
                         "will mutate it).")
    ap.add_argument("--selftest", action="store_true",
                    help="Build two synthetic tasks with known gate outcomes, verify the gate "
                         "classifies both correctly, then exit.")
    ap.add_argument("--parity-check", type=int, default=0, metavar="N",
                    help="Assert on N tasks that this script's grader invocation matches "
                         "harness.run_all.grade_run exactly. The result is written to "
                         "admission_parity.json and folded into the ledger's meta, whether it "
                         "was produced by this invocation or an earlier --parity-only one.")
    ap.add_argument("--parity-only", action="store_true",
                    help="Run --parity-check, write admission_parity.json, and exit without "
                         "sweeping. Use this to prove parity on cheap tasks without paying for "
                         "it inside a long sweep.")
    args = ap.parse_args()

    workdir = os.path.abspath(args.workdir or os.path.join(
        os.environ.get("TMPDIR", "/tmp"), "teambench_admission_gate"))
    os.makedirs(workdir, exist_ok=True)

    if args.bootstrap:
        gate_venv = os.path.join(workdir, "gate_venv")
        py = build_gate_venv(gate_venv)
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

    prefix = os.path.realpath(sys.prefix)
    if not args.allow_shared_venv:
        for v in repo_venv_paths():
            if os.path.isdir(v) and prefix == os.path.realpath(v):
                print(f"REFUSING to run under the repository venv {v}.\n"
                      "Graders run `pip install` at grade time and would mutate it from "
                      f"{args.workers} concurrent workers.\n"
                      "Use --bootstrap (recommended) or --allow-shared-venv.", file=sys.stderr)
                return 2

    os.makedirs(OUT_DIR, exist_ok=True)

    if args.selftest:
        print("[selftest] building two synthetic tasks with known gate outcomes", flush=True)
        ok = selftest(workdir)
        print("[selftest] " + ("PASS: the gate separates them correctly" if ok
                               else "FAIL: the gate misclassified a synthetic task"), flush=True)
        return 0 if ok else 1

    os.makedirs(OUT_DIR, exist_ok=True)
    scope = build_scope(args.sample_size, args.sample_seed, args.tasks,
                        args.reference_sample)

    cfg = {"workdir": workdir, "seed": args.seed, "grade_timeout": args.grade_timeout,
           "keep_runs": args.keep_runs, "measure_attestation": not args.no_attestation}

    parity = None
    if args.parity_check:
        ids = [e["task_id"] for e in scope][:args.parity_check]
        print(f"[parity] checking {len(ids)} tasks against harness.run_all.grade_run", flush=True)
        parity = parity_check(ids, workdir, args.seed)
        parity["checked_at"] = datetime.now(timezone.utc).isoformat()
        with open(PARITY_PATH, "w", encoding="utf-8") as f:
            json.dump(parity, f, indent=2)
        print(f"[parity] identical on {parity['identical']}/{parity['n']} "
              f"-> {PARITY_PATH}", flush=True)
    elif os.path.isfile(PARITY_PATH):
        try:
            parity = json.load(open(PARITY_PATH, encoding="utf-8"))
            print(f"[parity] reusing {PARITY_PATH}: identical on "
                  f"{parity.get('identical')}/{parity.get('n')}", flush=True)
        except (OSError, json.JSONDecodeError):
            parity = None

    if args.parity_only:
        return 0 if (parity and parity.get("identical") == parity.get("n")) else 1

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
        print(f"[resume] {len(done)} tasks already in {CHECKPOINT_PATH}", flush=True)
    elif args.no_resume and os.path.isfile(CHECKPOINT_PATH):
        os.remove(CHECKPOINT_PATH)

    todo = [] if args.summarize_only else [e for e in scope if e["task_id"] not in done]
    print(f"[scope] {len(scope)} tasks, {len(todo)} to evaluate, "
          f"{args.workers} workers, workdir={workdir}", flush=True)

    freeze_before = pip_freeze()
    ck_lock = threading.Lock()
    t_start = time.monotonic()
    completed = 0

    with open(CHECKPOINT_PATH, "a", encoding="utf-8") as ck:
        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
            futs = {pool.submit(evaluate_task, e, cfg): e["task_id"] for e in todo}
            for fut in as_completed(futs):
                tid = futs[fut]
                try:
                    rec = fut.result()
                except Exception as exc:
                    rec = {"task_id": tid, "scope": next(
                        (e.get("scope") for e in scope if e["task_id"] == tid), None),
                        "family": task_family(tid), "errors": [f"{type(exc).__name__}: {exc}"],
                        "gates": {g: {"verdict": "error", "detail": "worker crashed"}
                                  for g in GATE_IDS},
                        "verdicts": {g: "error" for g in GATE_IDS},
                        "admitted_strict": False, "admitted_pending_reference": False,
                        "advisory": {}, "artifacts": {}}
                done[tid] = rec
                completed += 1
                with ck_lock:
                    ck.write(json.dumps(rec) + "\n")
                    ck.flush()
                    os.fsync(ck.fileno())
                fl = rec.get("gates", {}).get("G1", {}).get("floor")
                bad = ",".join(g for g in GATE_IDS if rec.get("verdicts", {}).get(g) == "fail")
                print(f"[{completed}/{len(todo)}] {tid} floor={fl} "
                      f"admitted={rec.get('admitted_strict')} failed={bad or '-'}", flush=True)

    wall = round(time.monotonic() - t_start, 1)
    freeze_after = pip_freeze()
    delta = sorted(set(freeze_after) - set(freeze_before))

    records = [done[e["task_id"]] for e in scope if e["task_id"] in done]
    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "seed": args.seed,
        "sample_size": args.sample_size,
        "sample_seed": args.sample_seed,
        "workers": args.workers,
        "grade_timeout": args.grade_timeout,
        "harness_grade_cap_s": HARNESS_GRADE_CAP_S,
        "python_executable": sys.executable,
        "python_version": sys.version.split()[0],
        "workdir": workdir,
        "wall_seconds": wall,
        "summarize_only": bool(args.summarize_only),
        "rescan_corpus": bool(args.rescan_corpus),
        "scope_size": len(scope),
        "evaluated": len(records),
        "complete": len(records) == len(scope),
        "loadavg": [round(x, 2) for x in os.getloadavg()],
        "pip_delta": delta,
        "parity_check": parity,
        "grader_helpers_sha256": file_sha256(
            os.path.join(REPO_ROOT, "harness", "grader_helpers.sh")),
        "staging_fn": "harness.run_all.setup_run",
        "grading_fn": "scripts/task_admission_gate.py:invoke_grader "
                      "(parameterised copy of harness.run_all.grade_run)",
        **git_info(),
    }
    summary = summarize(records, meta)

    with open(LEDGER_PATH, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "tasks": records}, f, indent=2, sort_keys=False)
    with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
        f.write(render_markdown(summary, records))

    ov = summary["overall"]
    print("\n" + "=" * 68)
    print(f"Evaluated {ov['n']} tasks in {wall}s")
    for g in GATE_IDS:
        c = ov[g]
        print(f"  {g} {GATE_TITLES[g]:<42} pass={c['pass']:<4} fail={c['fail']:<4} "
              f"unknown={c['unknown']:<4} error={c['error']}")
    print(f"  PASS ALL SEVEN GATES: {ov['admitted_strict']} / {ov['n']}")
    print(f"  (six gates, G3 unknown or pass): {ov['admitted_pending_reference']} / {ov['n']}")
    print(f"\nLedger : {LEDGER_PATH}")
    print(f"Summary: {SUMMARY_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
