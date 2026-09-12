#!/usr/bin/env python3
"""
Move the reference solution out of the agent-visible task material.

Scope: tasks/*/spec.md and tasks/*/brief.md ONLY (plus the new, grader-only
tasks/*/reference/ directory it creates). grade.sh, task.yaml and workspace/
are never touched.

The defect being fixed
----------------------
The Planner-visible spec.md hands over the gold patch, and the Executor-visible
brief.md hands over the file list. Measured on this tree before the change:

  633 spec.md  contain "## Files Changed in Fix"
  296 spec.md  contain "## Diff Summary (What the Fix Changes)" with a ```diff
               block holding the literal reference patch
  633 brief.md contain "## Files That May Need Changes"

So on 633 tasks neither role has to localize anything, and on 296 of those the
Planner can read the answer and dictate it. That is not a coordination
benchmark, it is a transcription exercise.

What this does
--------------
It MOVES, it does not delete. For every affected task:

  spec.md   the block from "## Files Changed in Fix" up to (not including)
            "## Acceptance Criteria" is cut. That block is exactly the fix
            disclosure: the changed-file list, the "## Diff Summary" heading,
            the ```diff hunks, and the per-file "[Code changes omitted]"
            stubs. Verified against the whole corpus: the only headings inside
            that span are those three shapes, and all 633 specs terminate the
            span with "## Acceptance Criteria".

  brief.md  the block from "## Files That May Need Changes" up to (not
            including) "## Verification". All 633 briefs terminate that way.

  spec.md   the Important Notes bullet "Only modify the source files listed
            above (not test files)" is rewritten to "Only modify source files,
            not test files", because after the cut there is no list above and
            a dangling cross-reference makes the spec incoherent.

The cut text lands verbatim in:

  tasks/<id>/reference/solution.md   human/grader-readable, with provenance
  tasks/<id>/reference/patch.diff    machine-readable unified diff, where a
                                     diff exists (296 tasks)

The issue description, the discussion, the acceptance criteria and the
verification command all stay in the spec. Those are the legitimate task
statement.

HARNESS REQUIREMENT (owned by another component, stated here for the record)
---------------------------------------------------------------------------
tasks/<id>/reference/ MUST be excluded from every agent role's allowed_roots.
It ships with the benchmark (the graders and the admission gate need it) but no
role may read it. Moving the leak here accomplishes nothing until that
exclusion is enforced.

Usage
-----
  python3 scripts/deleak_specs.py --report     # inventory, no writes
  python3 scripts/deleak_specs.py --dry-run    # counts only
  python3 scripts/deleak_specs.py --apply      # perform the move
  python3 scripts/deleak_specs.py --verify     # residual leak counts
  python3 scripts/deleak_specs.py --restore    # put everything back

Idempotent: a second --apply is a no-op. Reversible: --restore re-inserts each
block at its original line and deletes the reference files this script created.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASKS = os.path.join(REPO, "tasks")
MANIFEST = os.path.join(REPO, "scripts", "deleak_manifest.json")

SPEC_START = "Files Changed in Fix"
SPEC_ALT_START = "Diff Summary (What the Fix Changes)"
SPEC_END = "Acceptance Criteria"
BRIEF_START = "Files That May Need Changes"
BRIEF_END = "Verification"

DANGLING_BULLET = "- Only modify the source files listed above (not test files)"
DANGLING_REPLACEMENT = "- Only modify source files, not test files"

# Cutting the "Files Changed in Fix" block does not catch every disclosure. In
# GH1154_matplotlib_30795 a maintainer pasted the complete fix into the issue
# thread itself ("The patch:" followed by a ```diff block), which sits in the
# Issue Discussion section and therefore survives the span cut. Any ```diff
# block still present after the cut is a reference patch by definition, so it
# is moved out too and replaced by this marker.
INLINE_DIFF_MARKER = (
    "> _Reference patch removed from the agent-visible spec. "
    "It lives in `reference/` and is readable by the grader only._"
)

HEADING_RE = re.compile(r"^[ \t]*(#{2,6})[ \t]+(.*?)[ \t]*$")
PATH_HEADING_RE = re.compile(r"^[ \t]*#{2,6}[ \t]+`(.+?)`[ \t]*$")
FENCE_OPEN_DIFF_RE = re.compile(r"^[ \t]*```diff[ \t]*$")
FENCE_CLOSE_RE = re.compile(r"^[ \t]*```[ \t]*$")
LINE_TERM_RE = re.compile(r"(\r\n|\n|\r)")


# --------------------------------------------------------------------------
# I/O that does not rewrite line endings (see redact_pii.py for the same rule)
# --------------------------------------------------------------------------

def read_text(path: str) -> str:
    with open(path, encoding="utf-8", errors="replace", newline="") as f:
        return f.read()


def write_text(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def split_keepends(text: str):
    parts = LINE_TERM_RE.split(text)
    pairs = [(parts[i], parts[i + 1]) for i in range(0, len(parts) - 1, 2)]
    pairs.append((parts[-1], ""))
    return pairs


def join_pairs(pairs) -> str:
    return "".join(b + t for b, t in pairs)


def iter_tasks():
    try:
        entries = sorted(os.scandir(TASKS), key=lambda e: e.name)
    except FileNotFoundError:
        sys.exit("no tasks/ directory at %s" % TASKS)
    for e in entries:
        if e.is_dir():
            yield e.name, e.path


# --------------------------------------------------------------------------
# Span location
# --------------------------------------------------------------------------

def find_span(pairs, start_titles, end_title):
    """
    Return (start_idx, end_idx) of the leaking block, or None.

    start_idx is the line index of the first start heading found; end_idx is
    the line index of the terminating "## <end_title>" heading. The block is
    pairs[start_idx:end_idx].
    """
    heads = []
    for i, (body, _t) in enumerate(pairs):
        m = HEADING_RE.match(body)
        if m:
            heads.append((i, m.group(1), m.group(2)))

    start = None
    for i, lvl, txt in heads:
        if txt in start_titles:
            start = i
            break
    if start is None:
        return None

    end = None
    for i, lvl, txt in heads:
        if i > start and lvl == "##" and txt == end_title:
            end = i
            break
    if end is None:
        return None
    return start, end


# --------------------------------------------------------------------------
# patch.diff synthesis
# --------------------------------------------------------------------------

def build_patch(block_pairs):
    """
    Turn the moved spec block into a unified diff.

    The scraped blocks come in two shapes. Most are bare "@@" hunks under a
    "### `path`" heading, so the ---/+++ headers have to be synthesized from
    that heading. A few already carry their own "diff --git" header, and those
    are emitted verbatim.
    """
    out = []
    cur_path = None
    i = 0
    n = len(block_pairs)
    while i < n:
        body = block_pairs[i][0]
        m = PATH_HEADING_RE.match(body)
        if m:
            cur_path = m.group(1)
            i += 1
            continue
        if FENCE_OPEN_DIFF_RE.match(body):
            j = i + 1
            hunk = []
            while j < n and not FENCE_CLOSE_RE.match(block_pairs[j][0]):
                hunk.append(block_pairs[j][0])
                j += 1
            if hunk:
                first = hunk[0].lstrip()
                if first.startswith("diff --git") or first.startswith("--- "):
                    out.extend(hunk)          # already a complete diff
                elif cur_path:
                    out.append("diff --git a/%s b/%s" % (cur_path, cur_path))
                    out.append("--- a/%s" % cur_path)
                    out.append("+++ b/%s" % cur_path)
                    out.extend(hunk)
                else:
                    out.extend(hunk)
                out.append("")
            i = j + 1
            continue
        i += 1
    while out and out[-1] == "":
        out.pop()
    return ("\n".join(out) + "\n") if out else ""


HEADER = """# Reference solution — %s

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `%s`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/%s/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

"""


def build_solution_md(task_id, spec_block, brief_block):
    parts = [HEADER % (task_id, task_id, task_id)]
    if spec_block:
        parts.append("## Moved from `spec.md`\n\n")
        parts.append(spec_block.rstrip("\r\n"))
        parts.append("\n")
    if brief_block:
        parts.append("\n## Moved from `brief.md`\n\n")
        parts.append(brief_block.rstrip("\r\n"))
        parts.append("\n")
    return "".join(parts)


# --------------------------------------------------------------------------
# Commands
# --------------------------------------------------------------------------

def _scan_one(args):
    """Read and classify one task dir. Pure I/O, safe to run on a thread."""
    task, tdir = args
    spec_p = os.path.join(tdir, "spec.md")
    brief_p = os.path.join(tdir, "brief.md")
    rec = {"task": task, "dir": tdir}
    try:
        spec_text = read_text(spec_p) if os.path.exists(spec_p) else None
    except OSError:
        spec_text = None
    try:
        brief_text = read_text(brief_p) if os.path.exists(brief_p) else None
    except OSError:
        brief_text = None

    if spec_text is not None and (
        SPEC_START in spec_text
        or SPEC_ALT_START in spec_text
        or DANGLING_BULLET in spec_text
        or "```diff" in spec_text
    ):
        pairs = split_keepends(spec_text)
        span = find_span(pairs, {SPEC_START, SPEC_ALT_START}, SPEC_END)
        if span:
            rec["spec"] = span
            rec["spec_text"] = spec_text
            rec["spec_has_diff"] = "```diff" in join_pairs(pairs[span[0]:span[1]])
            outside = join_pairs(pairs[:span[0]] + pairs[span[1]:])
        else:
            outside = spec_text
        if "```diff" in outside:
            rec["inline_diff"] = True
            rec.setdefault("spec_text", spec_text)
        rec["dangling"] = sum(1 for b, _ in pairs if b.strip() == DANGLING_BULLET)

    if brief_text is not None and BRIEF_START in brief_text:
        pairs = split_keepends(brief_text)
        span = find_span(pairs, {BRIEF_START}, BRIEF_END)
        if span:
            rec["brief"] = span
            rec["brief_text"] = brief_text

    if ("spec" in rec or "brief" in rec or rec.get("dangling")
            or rec.get("inline_diff")):
        return rec
    return None


def scan(workers=4):
    """
    Inventory pass. Returns a list of per-task findings.

    The tree is ~1263 task dirs on a slow NFS mount and this is entirely
    I/O-bound (measured: 9 minutes wall, 0.7s CPU, single-threaded). Reads run
    on a small thread pool for that reason; the cap stays low deliberately
    because other agents are working the same mount. A cheap substring test
    skips the line-splitting for the ~1776 files that carry no marker.
    """
    todo = list(iter_tasks())
    with ThreadPoolExecutor(max_workers=workers) as ex:
        results = list(ex.map(_scan_one, todo))
    return [r for r in results if r is not None]


def cmd_report():
    found = scan()
    n_spec = sum(1 for r in found if "spec" in r)
    n_diff = sum(1 for r in found if r.get("spec_has_diff"))
    n_brief = sum(1 for r in found if "brief" in r)
    n_dang = sum(r.get("dangling", 0) for r in found)
    print("=" * 72)
    print("REFERENCE-SOLUTION LEAK INVENTORY")
    print("=" * 72)
    print("spec.md  with '## %s' block          : %d" % (SPEC_START, n_spec))
    print("  of which carry a literal ```diff patch      : %d" % n_diff)
    print("brief.md with '## %s'    : %d" % (BRIEF_START, n_brief))
    print("spec.md  with the dangling 'listed above' bullet : %d" % n_dang)
    print()
    print("affected task directories                        : %d" % len(found))
    return found


def strip_inline_diffs(pairs):
    """
    Pull any ```diff fenced block out of `pairs`, replacing each with
    INLINE_DIFF_MARKER. Returns (new_pairs, [block_text, ...]).
    """
    out = []
    removed = []
    i = 0
    n = len(pairs)
    while i < n:
        body, term = pairs[i]
        if FENCE_OPEN_DIFF_RE.match(body):
            j = i + 1
            while j < n and not FENCE_CLOSE_RE.match(pairs[j][0]):
                j += 1
            j = min(j + 1, n)                       # include the closing fence
            removed.append(join_pairs(pairs[i:j]))
            out.append((INLINE_DIFF_MARKER, term or "\n"))
            i = j
            continue
        out.append((body, term))
        i += 1
    return out, removed


def _apply_one(rec, dry_run):
    """Transform one task dir. Returns (task, manifest_entry, stats)."""
    task, tdir = rec["task"], rec["dir"]
    stats = Counter()
    entry = {}
    spec_block = brief_block = ""

    if "spec" not in rec and rec.get("inline_diff"):
        pairs = split_keepends(rec["spec_text"])
        pairs, inline = strip_inline_diffs(pairs)
        if inline:
            entry["inline_diffs"] = inline
            entry.setdefault("spec_only_inline", True)
            stats["inline_diff_blocks_moved"] += len(inline)
            if not dry_run:
                write_text(os.path.join(tdir, "spec.md"), join_pairs(pairs))

    if "spec" in rec:
        pairs = split_keepends(rec["spec_text"])
        s, e = rec["spec"]
        spec_block = join_pairs(pairs[s:e])
        entry["spec"] = {"start": s, "text": spec_block}
        pairs = pairs[:s] + pairs[e:]
        n_fixed = 0
        for i, (b, t) in enumerate(pairs):
            if b.strip() == DANGLING_BULLET:
                indent = b[: len(b) - len(b.lstrip())]
                pairs[i] = (indent + DANGLING_REPLACEMENT, t)
                n_fixed += 1
        if n_fixed:
            entry["dangling_fixed"] = n_fixed
            stats["dangling_bullets_rewritten"] += n_fixed
        pairs, inline = strip_inline_diffs(pairs)
        if inline:
            entry["inline_diffs"] = inline
            stats["inline_diff_blocks_moved"] += len(inline)
        if not dry_run:
            write_text(os.path.join(tdir, "spec.md"), join_pairs(pairs))
        stats["spec_blocks_moved"] += 1

    if "brief" in rec:
        pairs = split_keepends(rec["brief_text"])
        s, e = rec["brief"]
        brief_block = join_pairs(pairs[s:e])
        entry["brief"] = {"start": s, "text": brief_block}
        pairs = pairs[:s] + pairs[e:]
        if not dry_run:
            write_text(os.path.join(tdir, "brief.md"), join_pairs(pairs))
        stats["brief_blocks_moved"] += 1

    if not entry:
        return task, None, stats

    refdir = os.path.join(tdir, "reference")
    sol = os.path.join(refdir, "solution.md")
    pat = os.path.join(refdir, "patch.diff")
    patch_text = build_patch(split_keepends(spec_block)) if spec_block else ""
    for blk in entry.get("inline_diffs", []):
        body = "\n".join(
            b for b, _ in split_keepends(blk)
            if not FENCE_OPEN_DIFF_RE.match(b) and not FENCE_CLOSE_RE.match(b))
        patch_text = (patch_text.rstrip("\n") + "\n\n" if patch_text else "") + body.strip("\n") + "\n"
    entry["reference"] = {
        "solution.md": os.path.relpath(sol, REPO),
        "patch.diff": os.path.relpath(pat, REPO) if patch_text else None,
    }
    # A later pass can find an inline diff in a spec whose span was already
    # moved by an earlier pass. In that case spec_block/brief_block are empty,
    # so writing solution.md would clobber what the earlier pass put there and
    # writing patch.diff would drop the earlier patch. Append instead.
    second_pass = (not spec_block and not brief_block
                   and os.path.exists(sol))
    if not dry_run:
        os.makedirs(refdir, exist_ok=True)
        if second_pass:
            existing = read_text(sol).rstrip("\n")
            add = "\n".join(entry.get("inline_diffs", []))
            write_text(sol, existing + "\n\n## Reference patch found inline in the issue text\n\n"
                       + add.rstrip("\n") + "\n")
        else:
            write_text(sol, build_solution_md(task, spec_block, brief_block))
        if patch_text:
            if second_pass and os.path.exists(pat):
                write_text(pat, read_text(pat).rstrip("\n") + "\n\n" + patch_text)
            else:
                write_text(pat, patch_text)
    stats["reference_solution_md_written"] += 1
    if patch_text:
        stats["reference_patch_diff_written"] += 1
    return task, entry, stats


def cmd_apply(dry_run=False, workers=4):
    found = scan(workers)
    manifest = {"version": 1, "tasks": {}}
    stats = Counter()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for task, entry, st in ex.map(lambda r: _apply_one(r, dry_run), found):
            stats.update(st)
            if entry:
                manifest["tasks"][task] = entry

    if not dry_run:
        if os.path.exists(MANIFEST):
            try:
                old_m = json.load(open(MANIFEST, encoding="utf-8"))
                for k, v in old_m.get("tasks", {}).items():
                    if k in manifest["tasks"]:
                        # A later pass records only what IT changed. Merge
                        # key-by-key so the earlier pass's undo data survives.
                        merged = dict(v)
                        merged.update(manifest["tasks"][k])
                        manifest["tasks"][k] = merged
                    else:
                        manifest["tasks"][k] = v
            except (ValueError, OSError):
                pass
        with open(MANIFEST, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=1)

    print("%s: %d task dirs touched" % ("DRY RUN" if dry_run else "APPLIED",
                                        len(manifest["tasks"])))
    for k in sorted(stats):
        print("    %-34s %d" % (k, stats[k]))
    if not dry_run:
        print("    manifest -> %s" % os.path.relpath(MANIFEST, REPO))
    return stats


def cmd_restore():
    if not os.path.exists(MANIFEST):
        sys.exit("no manifest at %s; nothing to restore" % MANIFEST)
    manifest = json.load(open(MANIFEST, encoding="utf-8"))
    n = 0
    for task, entry in manifest["tasks"].items():
        tdir = os.path.join(TASKS, task)

        # Inline diffs first. Each was collapsed to a one-line marker, so the
        # file is short by (block_len - 1) lines; putting them back restores
        # the original line numbering that the span's saved index refers to.
        sp = os.path.join(tdir, "spec.md")
        if entry.get("inline_diffs") and os.path.exists(sp):
            pairs = split_keepends(read_text(sp))
            blocks = list(entry["inline_diffs"])
            out = []
            for body, term in pairs:
                if body == INLINE_DIFF_MARKER and blocks:
                    out.extend(split_keepends(blocks.pop(0))[:-1])
                else:
                    out.append((body, term))
            write_text(sp, join_pairs(out))

        for key, fn in (("spec", "spec.md"), ("brief", "brief.md")):
            if key not in entry:
                continue
            p = os.path.join(tdir, fn)
            if not os.path.exists(p):
                print("  MISSING %s" % p)
                continue
            pairs = split_keepends(read_text(p))
            blk = split_keepends(entry[key]["text"])
            if blk and blk[-1] == ("", ""):
                blk = blk[:-1]
            s = entry[key]["start"]
            body_now = join_pairs(pairs)
            if entry[key]["text"] in body_now:
                continue                      # already restored
            pairs = pairs[:s] + blk + pairs[s:]
            if key == "spec" and entry.get("dangling_fixed"):
                for i, (b, t) in enumerate(pairs):
                    if b.strip() == DANGLING_REPLACEMENT:
                        indent = b[: len(b) - len(b.lstrip())]
                        pairs[i] = (indent + DANGLING_BULLET, t)
            write_text(p, join_pairs(pairs))
        ref = entry.get("reference", {})
        for rel in (ref.get("solution.md"), ref.get("patch.diff")):
            if rel:
                fp = os.path.join(REPO, rel)
                if os.path.exists(fp):
                    os.remove(fp)
        refdir = os.path.join(tdir, "reference")
        if os.path.isdir(refdir) and not os.listdir(refdir):
            os.rmdir(refdir)
        n += 1
    print("restored %d task dirs from manifest" % n)


def _verify_one(args):
    task, tdir = args
    out = dict(spec=0, diff=0, brief=0, dangling=0, sol=0, patch=0)
    sp = os.path.join(tdir, "spec.md")
    if os.path.exists(sp):
        t = read_text(sp)
        if "## " + SPEC_START in t:
            out["spec"] = 1
        if "## " + SPEC_ALT_START in t or "```diff" in t:
            out["diff"] = 1
        if DANGLING_BULLET in t:
            out["dangling"] = 1
    bp = os.path.join(tdir, "brief.md")
    if os.path.exists(bp) and "## " + BRIEF_START in read_text(bp):
        out["brief"] = 1
    if os.path.exists(os.path.join(tdir, "reference", "solution.md")):
        out["sol"] = 1
    if os.path.exists(os.path.join(tdir, "reference", "patch.diff")):
        out["patch"] = 1
    return out


def cmd_verify(workers=4):
    todo = list(iter_tasks())
    with ThreadPoolExecutor(max_workers=workers) as ex:
        rows = list(ex.map(_verify_one, todo))
    agg = Counter()
    for r in rows:
        agg.update(r)
    print("RESIDUAL IN AGENT-VISIBLE MATERIAL")
    print("  spec.md  with '## %s'        : %d" % (SPEC_START, agg["spec"]))
    print("  spec.md  with a ```diff block or Diff Summary : %d" % agg["diff"])
    print("  brief.md with '## %s'  : %d" % (BRIEF_START, agg["brief"]))
    print("  spec.md  with dangling 'listed above' bullet  : %d" % agg["dangling"])
    print("MOVED TO GRADER-ONLY reference/")
    print("  reference/solution.md files                   : %d" % agg["sol"])
    print("  reference/patch.diff files                    : %d" % agg["patch"])
    return agg


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--restore", action="store_true")
    a = ap.parse_args()
    if a.restore:
        cmd_restore()
    elif a.apply:
        cmd_apply(False)
    elif a.dry_run:
        cmd_apply(True)
    elif a.verify:
        cmd_verify()
    else:
        cmd_report()


if __name__ == "__main__":
    main()
