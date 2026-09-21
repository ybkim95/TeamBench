#!/usr/bin/env python3
"""Fail if a built PDF would identify the authors.

Anonymity is not a property you set once in \\author{}. It leaks from PDF
metadata, from a figure's embedded producer string, from a project name that is
searchable, from an acknowledgements paragraph added late, from a repository URL
in a footnote. Each of those is invisible in the LaTeX source you happen to be
looking at, so this checks the artifact that actually gets uploaded.

Usage:
  python scripts/check_anonymity.py paper/manuscript/main.pdf
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys

# Names, handles and hosts that would identify this group. Extend rather than
# relax: a false alarm costs a second, a miss costs the submission.
IDENTIFYING = [
    r"\bybkim\w*", r"\byubin\b", r"\bkim\b",
    r"\bMIT\b", r"\bMedia\s+Lab\b", r"\bmedia\.mit\.edu\b",
    r"\bTeamBench\b",
    r"github\.com/\S+", r"huggingface\.co/\S+",
    r"[\w.+-]+@[\w-]+\.(?:edu|com|org)",
]
# Sections that conventionally carry identity and must be absent under review.
FORBIDDEN_SECTIONS = [r"^\s*Acknowledg"]
# Metadata fields that must be empty.
META_FIELDS = ("Author", "Subject", "Keywords")


def text_of(pdf: str) -> str:
    return subprocess.run(["pdftotext", pdf, "-"], capture_output=True,
                          text=True).stdout


def meta_of(pdf: str) -> dict:
    out = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout
    d = {}
    for line in out.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            d[k.strip()] = v.strip()
    return d


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--allow", action="append", default=[],
                    help="regex to exempt, e.g. a masked placeholder")
    a = ap.parse_args()

    txt = text_of(a.pdf)
    findings = []

    for pat in IDENTIFYING:
        for m in re.finditer(pat, txt, re.I):
            frag = m.group(0)
            if any(re.search(x, frag, re.I) for x in a.allow):
                continue
            ctx = txt[max(0, m.start() - 40):m.end() + 40].replace("\n", " ")
            findings.append(("text", frag, ctx))

    for pat in FORBIDDEN_SECTIONS:
        if re.search(pat, txt, re.M | re.I):
            findings.append(("section", pat, "a section of this kind is present"))

    meta = meta_of(a.pdf)
    for f in META_FIELDS:
        if meta.get(f):
            findings.append(("metadata", "%s=%s" % (f, meta[f]), "must be empty"))

    if not findings:
        print("anonymity: clean (%d chars of text, metadata empty)" % len(txt))
        return 0

    print("anonymity: %d problem(s) in %s" % (len(findings), a.pdf))
    seen = set()
    for kind, what, ctx in findings:
        k = (kind, what.lower())
        if k in seen:
            continue
        seen.add(k)
        print("  [%s] %s" % (kind, what))
        print("        ...%s..." % ctx.strip()[:100])
    return 1


if __name__ == "__main__":
    sys.exit(main())
