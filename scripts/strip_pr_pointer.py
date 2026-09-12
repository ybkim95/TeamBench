#!/usr/bin/env python3
"""Remove the link to the fix PR from the documents the agents read.

Measured: 635 spec.md and 271 brief.md files name the pull request that fixes
the bug, by URL:

    - PR: https://github.com/redis/redis-py/pull/3998

That is a pointer to the answer. A model that has seen GitHub can recall the diff
from the PR number alone, so the task stops measuring whether the agents can
diagnose and repair and starts measuring whether the model memorised the
repository. SWE-bench gives the ISSUE statement for exactly this reason and
withholds the PR.

Issue links are kept: the issue is the legitimate problem statement, and the
issue text is already quoted in the spec. Repository links are kept too, since
knowing which project this is is part of the task.

Known and not addressed here: the task id itself ends in the PR number
(GH140_marshmallow_2874). Renaming 650 task directories would invalidate every
recorded result, run path and experiment config, so it is recorded as a residual
leak rather than fixed in passing. It is a weaker pointer than a URL, since it
requires the model to resolve "marshmallow 2874" on its own.

Usage:
  python scripts/strip_pr_pointer.py --dry-run
  python scripts/strip_pr_pointer.py --apply
"""
from __future__ import annotations

import argparse
import collections
import os
import re
import shutil
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Two shapes occur. The second appears inside quoted issue discussion, where a
# commenter suggests installing straight from the fix branch, and it names the
# same PR: pip install git+https://github.com/org/repo.git@refs/pull/123/head
PR_URL = re.compile(
    r"https?://github\.com/[\w.-]+/[\w.-]+(?:\.git)?"
    r"(?:/(?:pull|commit)/[\w]+/?|@refs/pull/\d+/\w+)")
PR_LINE = re.compile(r"^(\s*[-*]?\s*(?:PR|Pull Request|Fix|Commit)\s*:\s*).*$",
                     re.M | re.I)
WITHHELD = "(withheld: the upstream fix is not part of the task)"
DOCS = ("spec.md", "brief.md", "analysis_guidance.md")


def scrub(text: str):
    n = 0

    def line_sub(m):
        nonlocal n
        if PR_URL.search(m.group(0)):
            n += 1
            return m.group(1) + WITHHELD
        return m.group(0)

    text = PR_LINE.sub(line_sub, text)
    text, k = PR_URL.subn(WITHHELD, text)
    return text, n + k


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--backup", default=os.path.join(REPO, ".cache", "doc_backup"))
    a = ap.parse_args()
    apply = a.apply and not a.dry_run

    stats = collections.Counter()
    total = 0
    for d in sorted(os.listdir(os.path.join(REPO, "tasks"))):
        if not d.startswith("GH"):
            continue
        for name in DOCS:
            p = os.path.join(REPO, "tasks", d, name)
            if not os.path.isfile(p):
                continue
            src = open(p, encoding="utf-8", errors="replace").read()
            new, n = scrub(src)
            if n == 0:
                continue
            stats[name] += 1
            total += n
            if apply:
                bd = os.path.join(a.backup, d)
                os.makedirs(bd, exist_ok=True)
                shutil.copy(p, os.path.join(bd, name))
                open(p, "w", encoding="utf-8").write(new)

    for k, v in stats.most_common():
        print("  %-24s %d files" % (k, v))
    print("\n  pointers %s: %d" % ("removed" if apply else "that WOULD be removed",
                                   total))
    if not apply:
        print("  (dry run; --apply writes, backups go to %s)" % a.backup)
    return 0


if __name__ == "__main__":
    sys.exit(main())
