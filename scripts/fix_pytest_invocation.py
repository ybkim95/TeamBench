#!/usr/bin/env python3
"""Stop a repo's own pytest addopts from deciding the grader's verdict.

Measured on GH444_arrow_1184 with the maintainers' merged fix applied and the
held-out tests injected:

    223 passed in 5.08s
    FAIL Required test coverage of 99% not reached. Total coverage: 55.06%

Every test passes and pytest still exits 1. arrow's setup.cfg puts
`--cov --cov-fail-under=99` in addopts, and the grader runs ONE test file, so
coverage is necessarily far below the project gate. The same applies to any
addopts entry that can fail a run on its own: -p flags, --strict-markers,
--benchmark options, a --numprocesses that needs xdist.

This is not a task defect and not something a submission can fix. It made the
reference fix look broken on all 9 arrow tasks, all 4 poetry tasks and all 3
starlette tasks in the staged validation, every one of them failing C1 alone.

build_verified_core.py already neutralises this with --override-ini=addopts=
when it decides whether a task discriminates. The graders must agree with it, or
verification and grading measure different things.

`filterwarnings` is cleared for the same reason: a DeprecationWarning raised by a
DEPENDENCY, escalated to an error by the repo's own config, is not the bug under
test. Clearing it is conservative: a task whose fix is precisely "stop emitting
this warning" then passes without the fix, fails G_fail, and is rejected.

Usage:
  python scripts/fix_pytest_invocation.py --dry-run
  python scripts/fix_pytest_invocation.py --apply
"""
from __future__ import annotations

import argparse
import collections
import glob
import os
import re
import shutil
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FLAGS = "-p no:cacheprovider --override-ini=addopts= --override-ini=filterwarnings="

# `VAR=$(pytest ... 2>&1)` or `VAR=$(python -m pytest ... 2>&1)`
CALL = re.compile(
    r"(?P<head>\$\(\s*(?:python3?\s+-m\s+)?pytest\s)(?P<args>[^\n)]*?)(?P<tail>\s*2>&1\s*\))")


def rewrite(text: str):
    def sub(m):
        if "--override-ini=addopts=" in m.group("args"):
            return m.group(0)
        return m.group("head") + m.group("args").rstrip() + " " + FLAGS + m.group("tail")
    return CALL.subn(sub, text)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--backup", default=os.path.join(REPO, ".cache", "grader_backup_pytest"))
    a = ap.parse_args()
    apply = a.apply and not a.dry_run

    stats = collections.Counter()
    changed = 0
    for g in sorted(glob.glob(os.path.join(REPO, "tasks", "*", "grade.sh"))):
        src = open(g, encoding="utf-8", errors="replace").read()
        if "pytest" not in src:
            stats["no pytest"] += 1
            continue
        new, n = rewrite(src)
        if n == 0:
            stats["pytest present, no canonical capture"] += 1
            continue
        stats["rewritten"] += 1
        changed += n
        if apply:
            os.makedirs(a.backup, exist_ok=True)
            shutil.copy(g, os.path.join(
                a.backup, os.path.basename(os.path.dirname(g)) + ".grade.sh"))
            open(g, "w", encoding="utf-8").write(new)

    for k, v in stats.most_common():
        print("  %5d  %s" % (v, k))
    print("\n  pytest calls %s: %d" % ("rewritten" if apply else "that WOULD be rewritten",
                                       changed))
    if not apply:
        print("  (dry run; --apply writes, backups go to %s)" % a.backup)
    return 0


if __name__ == "__main__":
    sys.exit(main())
