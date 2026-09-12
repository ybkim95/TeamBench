#!/usr/bin/env python3
"""
Behavioural tests for scripts/redact_pii.py. Run: python3 scripts/test_redact_pii.py

Each case pins one decision the redactor has to get right. The FAIL-mode of
this script is the thing that matters most: over-redaction silently breaks a
task, so most cases assert that something is LEFT ALONE.
"""
import importlib.util, os, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("rp", os.path.join(HERE, "redact_pii.py"))
rp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rp)

# value None == "must come back byte-identical"
CASES = {
    # byte fidelity
    "CRLF preserved":             ("a\r\nHi @bob\r\nb\r\n", "a\r\nHi [user]\r\nb\r\n"),
    "mixed CRLF/LF":              ("x\r\n@bob\nz", "x\r\n[user]\nz"),
    "lone CR":                    ("@bob\rq", "[user]\rq"),
    "no trailing newline":        ("@bob", "[user]"),
    # code must survive untouched
    "fence protects decorator":   ("```py\n@property\ndef f(): pass\n```\n", None),
    "fence protects diff":        ("```diff\n-@ray.remote\n+@ray.remote\n```\n", None),
    "inline span protects email": ("valid: `user+tag@example.com` ok\n", None),
    "inline span protects x.com": ("- Email: `bad email@x.com` (space)\n", None),
    "example.com in fence kept":  ("```\nAuthor-email: a@example.com\n```\n", None),
    "decorator in prose":         ("use @property here\n", None),
    "repo url untouched":         ("see https://github.com/redis/redis-py/pull/1\n", None),
    "npm scope kept":             ("```\n@prisma/client       : 7.4.0\n```\n", None),
    "npm scope kept in prose":    ("install @prisma/client now\n", None),
    "no bogus backtrack":         ("@prisma/engines\n", None),
    "code-span decorator kept":   ("the `@given` decorator\n", None),
    "bot command span kept":      ("- `@home-assistant close` Closes it.\n", None),
    "pytest.mark span kept":      ("add `@pytest.mark.skip` here\n", None),
    "balanced fence still code":  ("```python\n@staticmethod\n@notarealuser\n```\n", None),
    # PII must go
    "reporter line":              ("**Reporter**: Jane Doe (jane@gmail.com)\r\n",
                                   "**Reporter**: [reporter]\r\n"),
    "profile link collapse":      ("> [@denialhaag](https://github.com/denialhaag) x\n", "> [user] x\n"),
    "bare profile url":           ("cc https://github.com/jeffdaily now\n",
                                   "cc https://github.com/[user] now\n"),
    "pkg metadata in fence":      ("```console\nAuthor: Andrew Svetlov\n"
                                   "Author-email: andrew.svetlov@gmail.com\n```\n",
                                   "```console\nAuthor: [redacted]\n"
                                   "Author-email: [email redacted]\n```\n"),
    "bot handle":                 ("### Comment 2 (@github-actions[bot]):\n",
                                   "### Comment 2 ([user]):\n"),
    "codeowners quoted":          ('```json\n  "codeowners": ["@emontnemery"],\n```\n',
                                   '```json\n  "codeowners": ["[user]"],\n```\n'),
    "code-span mention":          ("`@jacek-prisma`, the concern is valid\n",
                                   "[user], the concern is valid\n"),
    "malformed fence fallback":   ("```python\ncode\n### Comment 8 (@mspacek):\n@tacaswell hi\n",
                                   "```python\ncode\n### Comment 8 ([user]):\n[user] hi\n"),
}


def main():
    failures = 0
    for name, (src, want) in CASES.items():
        got = rp.process_text(src, Counter())
        exp = src if want is None else want
        if got == exp:
            print("PASS  %s" % name)
        else:
            failures += 1
            print("FAIL  %s\n        got =%r\n        want=%r" % (name, got, exp))

    s = "Hi @bob `@carol` \"@dave\" jane@gmail.com\r\n"
    o1 = rp.process_text(s, Counter())
    o2 = rp.process_text(o1, Counter())
    if o1 == o2:
        print("PASS  idempotent -> %r" % o1)
    else:
        failures += 1
        print("FAIL  idempotent: %r != %r" % (o1, o2))

    print("\n%d case(s) failed" % failures)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
