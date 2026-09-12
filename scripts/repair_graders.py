#!/usr/bin/env python3
"""
Repair the TeamBench measurement instrument (tasks/*/grade.sh).

This script is IDEMPOTENT: running it twice is a no-op the second time.
It is REVERSIBLE: every file it touches is git-tracked, so `git checkout --
tasks/*/grade.sh harness/grader_helpers.sh` restores the pre-repair state.
It is AUDITABLE: `--dry-run` prints the exact set of edits without writing,
and every run emits a JSON manifest of what changed.

Four defects are repaired, plus one that is only reported.

  R1  C3 IndentationError / inverted check
      All 633 auto-generated GH graders emit the whole script body indented
      8 spaces. C3 passes its check body to `python3 -c "<multi-line>"`, so
      the interpreter receives an indented block and raises IndentationError
      unconditionally. Because the failure is swallowed by `2>/dev/null ||
      tests_unmodified=false`, C3 FAILS whenever the test file exists and
      PASSES (vacuously, loop body never entered) when it is missing. The
      check is exactly inverted.
      Fix: rewrite the block as a column-0 `python3 - <<'_TBPY'` heredoc
      (the same construct C9/C10 in these files already use correctly), pass
      the filename through the environment instead of shell interpolation,
      and make a missing test file FAIL instead of silently passing.
      Where the shipped workspace ships NONE of the listed test files the
      check is not evaluable at all, so it is removed and the denominator
      decremented rather than left permanently unwinnable.

  R2  C4 duplicate / vacuous check
      `no test failures (0 FAILED)` counts `^FAILED` lines in pytest output.
      A collection error prints ERROR, not FAILED, so the check free-passes
      exactly when the test suite is most broken. It is also a strict
      duplicate of C1 (same pytest target). Removed; denominator decremented.

  R3  attestation.json scored as an artifact check
      attestation.json is a PROTOCOL property of the run (already enforced
      as a hard gate by harness/grade_task.py) and not a property of the
      submitted artifact. Scoring it lets an agent buy partial credit by
      writing one JSON file. Removed from partial_score; still recorded to
      grader stdout as metadata.

  R4  RDS answer-key-in-workspace
      8 graders `cd $WORKSPACE && python3 check_solution.py`, but
      check_solution.py is written INTO the agent-writable workspace by the
      generator and contains the full rubric. Overwriting it flips the task
      to pass. Fixed: the grader now resolves a grader-only copy (REPORTS/,
      then TASK_DIR/reference/, then a fresh deterministic regeneration from
      the task generator) and refuses to execute the workspace copy.

  R5  tasks/GH120_redis-py_3863/grade.sh  (REPORTED, NOT MODIFIED)
      A 22-line stub that hardcodes partial_score 0.0 for every submission.
      It is a member of the 90-task leaderboard. Removing it from LB90 is a
      leaderboard-definition decision, not a grader edit.

Reversibility
-------------
Only 183 of the 821 tasks/*/grade.sh files are git-tracked (most GH task
directories are untracked), so `git checkout` alone cannot undo this. The
complete pre-repair state of all 821 graders plus harness/grader_helpers.sh
is therefore archived, byte-for-byte, in

    shared/grader_repair_backup.tar.gz          (content)
    shared/grader_repair_backup_sha256.json     (per-file sha256 manifest)

`--revert` restores every file from that archive and verifies each restored
file against the recorded sha256. `--verify-backup` checks the archive alone.

Usage:
    python3 scripts/repair_graders.py --dry-run
    python3 scripts/repair_graders.py --apply
    python3 scripts/repair_graders.py --verify-backup
    python3 scripts/repair_graders.py --revert
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tarfile
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASKS_DIR = os.path.join(ROOT, "tasks")
HELPERS = os.path.join(ROOT, "harness", "grader_helpers.sh")
BACKUP_TAR = os.path.join(ROOT, "shared", "grader_repair_backup.tar.gz")
BACKUP_SHA = os.path.join(ROOT, "shared", "grader_repair_backup_sha256.json")

MARK_C3 = "# repaired-by: scripts/repair_graders.py (R1 c3-heredoc)"
MARK_C3_DROP = "# removed-by: scripts/repair_graders.py (R1 c3-not-evaluable)"
MARK_C4 = "# removed-by: scripts/repair_graders.py (R2 c4-vacuous-duplicate)"
MARK_ATT = "# de-scored-by: scripts/repair_graders.py (R3 attestation-is-protocol)"
MARK_RDS = "# repaired-by: scripts/repair_graders.py (R4 grader-only-rubric)"
MARK_HELPERS = "# hardened-by: scripts/repair_graders.py"

STUB_TASK = "GH120_redis-py_3863"


# ───────────────────────────── helpers ──────────────────────────────────────
def read(p: str) -> str:
    with open(p, encoding="utf-8", errors="surrogateescape") as f:
        return f.read()


def write(p: str, s: str) -> None:
    with open(p, "w", encoding="utf-8", errors="surrogateescape") as f:
        f.write(s)


def bump_init_grader(src: str, delta: int) -> tuple[str, int | None, int | None]:
    """Adjust the `init_grader N` denominator by `delta`. Returns (src, old, new)."""
    m = re.search(r"^(\s*)init_grader\s+(\d+)\s*$", src, re.M)
    if not m:
        return src, None, None
    old = int(m.group(2))
    new = max(1, old + delta)
    src = src[: m.start()] + f"{m.group(1)}init_grader {new}" + src[m.end():]
    return src, old, new


def find_check_invocations(src: str) -> list[tuple[int, int]]:
    """Return (start, end) char spans of legacy `check "ARG1" "ARG2"` calls.

    Spans are found by counting double quotes that are not backslash-escaped;
    a call ends once four unescaped quotes have been consumed and the line
    ends. This correctly handles the multi-line python payloads these graders
    embed (both `check "python3 -c \\"...\\"" "name"` and
    `check "python3 -c '...'" "name"` forms).
    """
    spans = []
    for m in re.finditer(r"^[ \t]*check[ \t]+\"", src, re.M):
        i = m.end() - 1  # index of the opening quote of ARG1
        q = 0
        n = len(src)
        while i < n:
            c = src[i]
            if c == "\\":
                i += 2
                continue
            if c == '"':
                q += 1
                if q == 4:
                    # consume to end of line
                    j = src.find("\n", i)
                    end = n if j == -1 else j + 1
                    spans.append((m.start(), end))
                    break
            i += 1
    return spans


# ───────────────────────────── R1 / R2: GH graders ──────────────────────────
C3_RE = re.compile(
    r"[ \t]*# ── C3: No test files modified[^\n]*\n"
    r"(?:[^\n]*\n)*?"
    r"[ \t]*check \"C3\" \"test files present and intact\"[^\n]*\n"
)
C4_RE = re.compile(
    r"[ \t]*# ── C4: Specific failure mode no longer triggers[^\n]*\n"
    r"(?:[^\n]*\n)*?"
    r"[ \t]*check \"C4\" \"no test failures \(0 FAILED\)\"[^\n]*\n"
)
TFILE_RE = re.compile(r"for tfile in (.*?); do")

C3_NEW_TMPL = """\
# ── C3: Test files present and intact ─────────────────────────────────
{mark}
# (Agents must not cheat by deleting or gutting the tests.)
# The inline python is a column-0 heredoc so it actually parses; the
# filename is passed via the environment, not interpolated into source;
# and a MISSING test file now fails instead of vacuously passing.
tests_unmodified=true
for tfile in {tfiles}; do
    if [ ! -f "$tfile" ]; then
        tests_unmodified=false
        continue
    fi
    TB_TFILE="$tfile" python3 - <<'_TBPY' 2>/dev/null || tests_unmodified=false
import ast, os, sys
src = open(os.environ['TB_TFILE']).read()
tree = ast.parse(src)
fns = [n.name for n in ast.walk(tree)
       if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
       and n.name.startswith('test_')]
sys.exit(0 if fns else 1)
_TBPY
done
check "C3" "test files present and intact" "$([ $tests_unmodified = true ] && echo pass || echo fail)"
"""


def repair_gh(task: str, path: str, src: str, rec: dict) -> str:
    """Apply R1 and R2 to one auto-generated GH grader."""
    delta = 0

    # ── R2: drop the vacuous duplicate C4 ────────────────────────────────
    if MARK_C4 not in src:
        m = C4_RE.search(src)
        if m:
            src = src[: m.start()] + (
                "# ── C4 (no test failures / 0 FAILED) REMOVED ─────────────────────────\n"
                f"{MARK_C4}\n"
                "# It counted `^FAILED` lines, so a pytest COLLECTION ERROR (which\n"
                "# prints ERROR, not FAILED) free-passed it, and it duplicated C1's\n"
                "# pytest target. Denominator decremented accordingly.\n"
            ) + src[m.end():]
            delta -= 1
            rec["c4_removed"] = True

    # ── R1: fix or drop C3 ───────────────────────────────────────────────
    if MARK_C3 not in src and MARK_C3_DROP not in src:
        m = C3_RE.search(src)
        if m:
            block = m.group(0)
            tm = TFILE_RE.search(block)
            listed = tm.group(1).split() if tm else []
            ws = os.path.join(TASKS_DIR, task, "workspace")
            shipped = [t for t in listed if os.path.exists(os.path.join(ws, t))]
            rec["c3_listed"] = listed
            rec["c3_shipped"] = shipped
            if shipped:
                new = C3_NEW_TMPL.format(mark=MARK_C3, tfiles=" ".join(shipped))
                rec["c3_fixed"] = True
                rec["c3_dropped_paths"] = [t for t in listed if t not in shipped]
            else:
                new = (
                    "# ── C3 (test files present and intact) REMOVED ───────────────────────\n"
                    f"{MARK_C3_DROP}\n"
                    "# The shipped workspace contains NONE of the test files this check\n"
                    "# named, so the check is not evaluable for this task. Scoring an\n"
                    "# unevaluable check either awards free credit (the pre-repair\n"
                    "# behaviour) or caps partial_score below 1.0 forever. Removed and\n"
                    "# denominator decremented instead.\n"
                    f"# not evaluable: {' '.join(listed) if listed else '(no files listed)'}\n"
                )
                delta -= 1
                rec["c3_removed"] = True
            src = src[: m.start()] + new + src[m.end():]

    if delta:
        src, old, new = bump_init_grader(src, delta)
        rec["init_grader"] = {"old": old, "new": new, "delta": delta}
    return src


# ───────────────────────────── R3: attestation ──────────────────────────────
ATT_META = """\
# ── Attestation recorded as METADATA, never scored ───────────────────────
{mark}
# attestation.json is a PROTOCOL property of the run (already enforced as a
# hard gate in harness/grade_task.py), not a property of the submitted
# artifact. Scoring it let an agent buy partial credit by writing one JSON
# file, which is the confound behind the withdrawn "removing the Verifier
# improves partial score" result. Recorded here, excluded from partial_score.
echo "metadata: attestation_present=$([ -f "${{SUBMISSION:-}}/attestation.json" ] && echo yes || echo no)"
"""

GO_ATT_RE = re.compile(
    r"[ \t]*# Check \d+: attestation\.json[^\n]*\n"
    r"[ \t]*CHECKS=\$\(\(CHECKS \+ 1\)\)\n"
    r"[ \t]*if python3 -c \"\n"
    r"(?:[^\n]*\n)*?"
    r"[ \t]*fi\n"
)


def descore_attestation(path: str, src: str, rec: dict) -> str:
    if MARK_ATT in src:
        return src
    removed = 0

    # form B: GO*-style manual CHECKS increment around an if/fi block
    m = GO_ATT_RE.search(src)
    if m and "attestation.json" in m.group(0):
        src = src[: m.start()] + ATT_META.format(mark=MARK_ATT) + src[m.end():]
        removed += 1

    # forms A / A2: legacy `check "<payload containing attestation.json>" "<name>"`
    while True:
        hit = None
        for s, e in find_check_invocations(src):
            if "attestation.json" in src[s:e]:
                hit = (s, e)
                break
        if hit is None:
            break
        s, e = hit
        repl = ATT_META.format(mark=MARK_ATT) if removed == 0 else ""
        src = src[:s] + repl + src[e:]
        removed += 1

    if removed:
        rec["attestation_checks_removed"] = removed
    return src


# ───────────────────────────── R4: RDS rubric ───────────────────────────────
RDS_OLD_TAIL = re.compile(
    r'cd "\$\{WORKSPACE\}"\n'
    r'python3 check_solution\.py \|\| true[^\n]*\n?'
)

RDS_NEW_TAIL = f"""\
# ── Resolve a GRADER-ONLY copy of the rubric script ──────────────────────
{MARK_RDS}
# check_solution.py is written into the agent-writable workspace by the task
# generator and contains the full rubric. Executing the workspace copy let an
# agent overwrite it and grade itself (measured: 4/4 probed tasks flipped to
# pass=true / partial 1.00 by dropping in a stub). We never execute the
# workspace copy. Resolution order:
#   1. "$REPORTS/check_solution.py"            (grader-only staging dir)
#   2. "$TASK_DIR/reference/check_solution.py" (static grader-only copy)
#   3. deterministic regeneration from the task generator at this run's seed
TASK_DIR="${{4:-$(cd "$(dirname "$0")" && pwd)}}"
TB_GDIR="$(mktemp -d)"
trap 'rm -rf "$TB_GDIR"' EXIT
TB_RUBRIC=""

if [ -f "${{REPORTS}}/check_solution.py" ]; then
    TB_RUBRIC="${{REPORTS}}/check_solution.py"
elif [ -f "${{TASK_DIR}}/reference/check_solution.py" ]; then
    TB_RUBRIC="${{TASK_DIR}}/reference/check_solution.py"
else
    TB_REPO_ROOT="$(cd "${{TASK_DIR}}/../.." && pwd)"
    TB_TASK_ID="$(basename "${{TASK_DIR}}")"
    TB_SEED="$(python3 - "$(dirname "${{REPORTS}}")/run_meta.json" <<'_TBPY' 2>/dev/null || echo 0
import json, sys
try:
    print(int(json.load(open(sys.argv[1])).get("seed", 0)))
except Exception:
    print(0)
_TBPY
)"
    if TB_REPO_ROOT="$TB_REPO_ROOT" TB_TASK_ID="$TB_TASK_ID" TB_SEED="$TB_SEED" \\
       TB_OUT="${{TB_GDIR}}/check_solution.py" python3 - <<'_TBPY' 2>/dev/null; then
import os, sys
sys.path.insert(0, os.environ["TB_REPO_ROOT"])
from generators.registry import get_generator
gen = get_generator(os.environ["TB_TASK_ID"])
res = gen.generate(seed=int(os.environ["TB_SEED"]))
src = res.workspace_files.get("check_solution.py")
if not src:
    sys.exit(1)
open(os.environ["TB_OUT"], "w", encoding="utf-8").write(src)
_TBPY
        TB_RUBRIC="${{TB_GDIR}}/check_solution.py"
    fi
fi

if [ -z "$TB_RUBRIC" ] || [ ! -s "$TB_RUBRIC" ]; then
    mkdir -p "${{REPORTS}}"
    cat > "${{REPORTS}}/score.json" <<EOF
{{
  "pass": false,
  "primary": {{"success": 0}},
  "secondary": {{"partial_score": 0.0, "checks_passed": 0, "checks_total": 0}},
  "failure_modes": ["grader_rubric_unavailable"]
}}
EOF
    exit 0
fi

# Execute the trusted rubric with __file__ pinned to the workspace so the
# script's own path resolution (workspace_dir = __file__.parent,
# reports_dir = workspace_dir.parent/"reports") is unchanged. The workspace
# copy, whatever the agent left there, is never executed.
TB_RUBRIC="$TB_RUBRIC" TB_WORKSPACE="${{WORKSPACE}}" python3 - <<'_TBPY' || true
import os, runpy, sys
src = open(os.environ["TB_RUBRIC"], encoding="utf-8").read()
fake = os.path.join(os.environ["TB_WORKSPACE"], "check_solution.py")
g = {{"__name__": "__main__", "__file__": fake, "__builtins__": __builtins__}}
os.chdir(os.environ["TB_WORKSPACE"])
try:
    exec(compile(src, fake, "exec"), g)
except SystemExit:
    pass
_TBPY
"""


def repair_rds(path: str, src: str, rec: dict) -> str:
    if MARK_RDS in src:
        return src
    m = RDS_OLD_TAIL.search(src)
    if not m:
        return src
    src = src[: m.start()] + RDS_NEW_TAIL + src[m.end():]
    rec["rds_rubric_hardened"] = True
    return src


# ───────────────────────────── helpers library ──────────────────────────────
def repair_helpers(dry: bool, manifest: dict) -> None:
    src = read(HELPERS)
    if MARK_HELPERS in src:
        manifest["grader_helpers"] = "already-hardened"
        return
    old = "    partial_score=$(python3 -c \"print(round($_GRADER_PARTIAL / $_GRADER_TOTAL, 2))\")"
    if old not in src:
        manifest["grader_helpers"] = "pattern-not-found (unchanged)"
        return
    new = (
        f"    {MARK_HELPERS}: guard a zero denominator so a grader whose checks\n"
        "    # were all removed still emits a well-formed score.json instead of\n"
        "    # dying on ZeroDivisionError and producing no score at all.\n"
        "    if [ \"${_GRADER_TOTAL:-0}\" -le 0 ]; then _GRADER_TOTAL=1; fi\n"
        + old
    )
    src = src.replace(old, new, 1)
    if not dry:
        write(HELPERS, src)
    manifest["grader_helpers"] = "hardened (zero-denominator guard)"



# ───────────────────── pre-repair backup / revert ───────────────────────────
def _backup_members() -> dict:
    """Read the pre-repair archive into {repo_relative_path: bytes}."""
    if not os.path.isfile(BACKUP_TAR):
        raise SystemExit(f"missing backup archive: {BACKUP_TAR}")
    out = {}
    with tarfile.open(BACKUP_TAR, "r:gz") as tf:
        for m in tf.getmembers():
            if not m.isfile():
                continue
            f = tf.extractfile(m)
            if f is not None:
                out[m.name] = f.read()
    return out


def ensure_backup() -> dict:
    """Create the pre-repair archive from the CURRENT on-disk state if it does
    not exist yet. Refuses to overwrite an existing archive, so the archive
    always holds the true pre-repair bytes."""
    if os.path.isfile(BACKUP_TAR):
        return {"backup": "already present (not overwritten)", "path": BACKUP_TAR}
    paths = []
    for e in sorted(os.scandir(TASKS_DIR), key=lambda x: x.name):
        if e.is_dir() and os.path.isfile(os.path.join(e.path, "grade.sh")):
            paths.append(f"tasks/{e.name}/grade.sh")
    paths.append("harness/grader_helpers.sh")
    shas = {}
    os.makedirs(os.path.dirname(BACKUP_TAR), exist_ok=True)
    with tarfile.open(BACKUP_TAR, "w:gz") as tf:
        for rel in paths:
            with open(os.path.join(ROOT, rel), "rb") as fh:
                data = fh.read()
            ti = tarfile.TarInfo(rel)
            ti.size = len(data)
            ti.mtime = 0
            ti.mode = 0o644
            tf.addfile(ti, io.BytesIO(data))
            shas[rel] = hashlib.sha256(data).hexdigest()
    with open(BACKUP_SHA, "w", encoding="utf-8") as fh:
        json.dump({"created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                   "n_files": len(shas), "sha256": shas}, fh, indent=1, sort_keys=True)
    return {"backup": "created", "path": BACKUP_TAR, "n_files": len(shas)}


def verify_backup() -> dict:
    members = _backup_members()
    shas = json.load(open(BACKUP_SHA, encoding="utf-8"))["sha256"]
    bad = [p for p, b in members.items()
           if hashlib.sha256(b).hexdigest() != shas.get(p)]
    ondisk_clean = 0
    for p, b in members.items():
        fp = os.path.join(ROOT, p)
        if os.path.isfile(fp) and open(fp, "rb").read() == b:
            ondisk_clean += 1
    return {"archive_files": len(members), "sha256_mismatches": bad,
            "files_currently_identical_to_backup": ondisk_clean,
            "files_currently_modified": len(members) - ondisk_clean}


def revert(dry: bool) -> dict:
    members = _backup_members()
    shas = json.load(open(BACKUP_SHA, encoding="utf-8"))["sha256"]
    restored, already, failed = 0, 0, []
    for p, b in sorted(members.items()):
        if hashlib.sha256(b).hexdigest() != shas.get(p):
            failed.append(f"{p}: backup sha256 mismatch")
            continue
        fp = os.path.join(ROOT, p)
        if os.path.isfile(fp) and open(fp, "rb").read() == b:
            already += 1
            continue
        if not dry:
            os.makedirs(os.path.dirname(fp), exist_ok=True)
            with open(fp, "wb") as fh:
                fh.write(b)
            if open(fp, "rb").read() != b:
                failed.append(f"{p}: write-back verification failed")
                continue
        restored += 1
    return {"restored": restored, "already_pristine": already, "failed": failed}


# ───────────────────────────── main ─────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--apply", action="store_true", help="write changes")
    g.add_argument("--dry-run", action="store_true", help="report only")
    g.add_argument("--revert", action="store_true",
                   help="restore every grader from shared/grader_repair_backup.tar.gz")
    g.add_argument("--verify-backup", action="store_true",
                   help="verify the pre-repair archive against its sha256 manifest")
    ap.add_argument("--manifest", default=os.path.join(ROOT, "shared", "grader_repair_manifest.json"))
    a = ap.parse_args()

    if a.verify_backup:
        print(json.dumps(verify_backup(), indent=1))
        return 0
    if a.revert:
        r = revert(dry=False)
        print(json.dumps(r, indent=1))
        return 1 if r["failed"] else 0

    dry = a.dry_run

    if not dry:
        manifest_backup = ensure_backup()
    else:
        manifest_backup = {"backup": "skipped (dry-run)"}

    manifest: dict = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mode": "dry-run" if dry else "apply",
        "tasks": {},
        "totals": {},
        "reported_not_modified": {},
        "backup": manifest_backup,
    }

    for e in sorted(os.scandir(TASKS_DIR), key=lambda x: x.name):
        if not e.is_dir():
            continue
        path = os.path.join(e.path, "grade.sh")
        if not os.path.isfile(path):
            continue
        if e.name == STUB_TASK:
            manifest["reported_not_modified"][e.name] = (
                "R5: 22-line stub hardcoding partial_score 0.0 for every submission; "
                "member of the 90-task leaderboard. Not modified — remove from LB90."
            )
            continue
        src0 = read(path)
        src = src0
        rec: dict = {}

        is_gh_auto = "no test failures (0 FAILED)" in src or MARK_C4 in src
        if is_gh_auto:
            src = repair_gh(e.name, path, src, rec)
        if "attestation.json" in src:
            src = descore_attestation(path, src, rec)
        if "check_solution.py" in src:
            src = repair_rds(path, src, rec)

        if src != src0:
            if not dry:
                write(path, src)
            manifest["tasks"][e.name] = rec

    repair_helpers(dry, manifest)

    t = manifest["totals"]
    recs = manifest["tasks"].values()
    t["files_changed"] = len(manifest["tasks"])
    t["c3_fixed"] = sum(1 for r in recs if r.get("c3_fixed"))
    t["c3_removed_not_evaluable"] = sum(1 for r in recs if r.get("c3_removed"))
    t["c4_removed"] = sum(1 for r in recs if r.get("c4_removed"))
    t["attestation_checks_removed"] = sum(r.get("attestation_checks_removed", 0) for r in recs)
    t["attestation_files"] = sum(1 for r in recs if r.get("attestation_checks_removed"))
    t["rds_rubric_hardened"] = sum(1 for r in recs if r.get("rds_rubric_hardened"))

    os.makedirs(os.path.dirname(a.manifest), exist_ok=True)
    if not dry:
        # A no-op re-run must not clobber the manifest that recorded the real
        # edits; only write when this run actually changed something or when
        # no manifest exists yet.
        if t["files_changed"] or not os.path.isfile(a.manifest):
            with open(a.manifest, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=1, sort_keys=True)
        else:
            manifest["note"] = f"no-op run; existing manifest at {a.manifest} left intact"
    print(json.dumps({"mode": manifest["mode"], "backup": manifest_backup, "totals": t,
                      "grader_helpers": manifest["grader_helpers"],
                      "reported_not_modified": list(manifest["reported_not_modified"])},
                     indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
