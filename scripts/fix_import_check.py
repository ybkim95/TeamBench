#!/usr/bin/env python3
"""Replace the graders' file-path import check with a package-name import.

The check as generated does:

    spec = importlib.util.spec_from_file_location('mod', src_path)
    spec.loader.exec_module(module_from_spec(spec))

which loads a package-internal file as a detached top-level module named 'mod'.
Every relative import inside that file then raises

    ImportError: attempted relative import with no known parent package

so the check cannot pass whatever the submission does. Measured: it fails with
the maintainers' own merged fix applied on 37 of 59 staged tasks. That is not a
cosmetic defect. The grader's overall `pass` requires every check, so those tasks
were unsolvable by construction; partial_score was capped below 1.0; and because
the check fails on the pristine workspace too, the discriminative rescore counted
it as a check a solution is supposed to fix.

The replacement calls tb_import_module from harness/grader_helpers.sh, which
derives the dotted module name from the path and imports it, so relative imports
resolve the way Python resolves them. The question the check asks is unchanged.

Usage:
  python scripts/fix_import_check.py --dry-run
  python scripts/fix_import_check.py --apply
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

BLOCK = re.compile(
    r"(?P<ind>[ \t]*)python3 - \"\$(?P<var>_?src)\" <<'PYEOF'(?P<tail>[^\n]*)\n"
    r".*?\nPYEOF\n",
    re.S)


def rewrite(text: str):
    """Return (new_text, n_replacements)."""
    def sub(m):
        return '%stb_import_module "$%s"%s\n' % (m.group("ind"), m.group("var"),
                                                 m.group("tail"))
    new, n = BLOCK.subn(sub, text)
    return new, n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--backup", default=os.path.join(REPO, ".cache", "grader_backup"))
    a = ap.parse_args()
    apply = a.apply and not a.dry_run

    stats = collections.Counter()
    changed = []
    for g in sorted(glob.glob(os.path.join(REPO, "tasks", "*", "grade.sh"))):
        src = open(g, encoding="utf-8", errors="replace").read()
        if "spec_from_file_location" not in src:
            stats["no import check"] += 1
            continue
        new, n = rewrite(src)
        if n == 0:
            stats["import check present but not the canonical shape"] += 1
            continue
        if "spec_from_file_location" in new:
            stats["rewrote one block, another remains"] += 1
        stats["rewritten"] += 1
        changed.append((g, n))
        if apply:
            os.makedirs(a.backup, exist_ok=True)
            shutil.copy(g, os.path.join(
                a.backup, os.path.basename(os.path.dirname(g)) + ".grade.sh"))
            open(g, "w", encoding="utf-8").write(new)

    for k, v in stats.most_common():
        print("  %5d  %s" % (v, k))
    print("\n  graders %s: %d" % ("rewritten" if apply else "that WOULD be rewritten",
                                  len(changed)))
    if not apply:
        print("  (dry run; pass --apply to write, backups go to %s)" % a.backup)
    return 0


if __name__ == "__main__":
    sys.exit(main())
