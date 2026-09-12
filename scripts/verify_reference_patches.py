#!/usr/bin/env python3
"""
Sanity-check the reference patches extracted by scripts/deleak_specs.py.

This does NOT prove a patch applies (the workspaces are re-parameterized copies,
not the upstream checkout, so line offsets will not match). It checks the far
weaker property that the extracted text is a well-formed unified diff with the
file headers and hunk headers a downstream tool needs:

  * every patch has at least one "--- a/<path>" / "+++ b/<path>" pair
  * every hunk header parses as "@@ -l,s +l,s @@"
  * the counted +/-/context lines match the hunk header's declared sizes
  * the patch is non-empty

A hunk whose declared "@@ -l,s +l,s @@" sizes do not match its body means the
```diff block in the source spec was truncated by the scraper, sometimes
mid-word. Such a patch is NOT a usable reference-solution oracle: it cannot be
applied and it does not describe the whole fix. With --write-meta the result is
recorded per task in tasks/<id>/reference/patch_meta.json so the admission gate
can tell a complete oracle from a truncated fragment instead of assuming.

Run: python3 scripts/verify_reference_patches.py [--write-meta]
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

HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def check_patch(path):
    problems = []
    with open(path, encoding="utf-8", errors="replace", newline="") as f:
        lines = f.read().split("\n")
    if not any(l.strip() for l in lines):
        return ["empty patch"]

    has_minus = any(l.startswith("--- ") for l in lines)
    has_plus = any(l.startswith("+++ ") for l in lines)
    if not (has_minus and has_plus):
        problems.append("missing ---/+++ file headers")

    n_hunks = 0
    i = 0
    while i < len(lines):
        m = HUNK_RE.match(lines[i])
        if not m:
            i += 1
            continue
        n_hunks += 1
        old_len = int(m.group(2)) if m.group(2) is not None else 1
        new_len = int(m.group(4)) if m.group(4) is not None else 1
        old_seen = new_seen = 0
        j = i + 1
        while j < len(lines):
            l = lines[j]
            if HUNK_RE.match(l) or l.startswith("diff --git") or l.startswith("--- "):
                break
            if l.startswith("-"):
                old_seen += 1
            elif l.startswith("+"):
                new_seen += 1
            elif l.startswith(" ") or l == "":
                old_seen += 1
                new_seen += 1
            elif l.startswith("\\"):
                pass
            else:
                break
            j += 1
        # A trailing blank line separator inflates both counts by one.
        if old_seen not in (old_len, old_len + 1) or new_seen not in (new_len, new_len + 1):
            problems.append(
                "hunk at line %d declares -%d/+%d but body has -%d/+%d"
                % (i + 1, old_len, new_len, old_seen, new_seen))
        i = j

    if n_hunks == 0:
        problems.append("no @@ hunk headers")
    return problems


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write-meta", action="store_true",
                    help="write tasks/<id>/reference/patch_meta.json for each patch")
    args = ap.parse_args()

    paths = []
    for e in sorted(os.scandir(TASKS), key=lambda x: x.name):
        if not e.is_dir():
            continue
        p = os.path.join(e.path, "reference", "patch.diff")
        if os.path.exists(p):
            paths.append((e.name, p))

    if not paths:
        print("no reference/patch.diff files found")
        return 0

    def run(item):
        task, path = item
        probs = check_patch(path)
        if args.write_meta:
            meta = {
                "task": task,
                "patch": os.path.relpath(path, REPO),
                "complete": not probs,
                "problems": probs,
                "note": ("Extracted from the spec.md ```diff block by "
                         "scripts/deleak_specs.py. 'complete': false means the "
                         "source block was truncated by the scraper, so this "
                         "patch cannot serve as a reference-solution oracle "
                         "until the full diff is re-fetched from the upstream "
                         "PR (see curation_notes.json for repo/pr_number/head_sha)."),
            }
            with open(os.path.join(os.path.dirname(path), "patch_meta.json"),
                      "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=1)
        return task, probs

    with ThreadPoolExecutor(max_workers=4) as ex:
        results = list(ex.map(run, paths))

    kinds = Counter()
    bad = []
    for task, probs in results:
        if probs:
            bad.append((task, probs))
            for p in probs:
                kinds[re.sub(r"\d+", "N", p)] += 1

    print("reference/patch.diff files checked : %d" % len(paths))
    print("well-formed                        : %d" % (len(paths) - len(bad)))
    print("with problems                      : %d" % len(bad))
    for k, v in kinds.most_common():
        print("    %4d  %s" % (v, k))
    for task, probs in bad[:15]:
        print("    e.g. %s: %s" % (task, probs[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
