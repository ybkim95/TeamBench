#!/usr/bin/env python3
"""
Redact personally identifying information from agent-visible task material.

Scope: tasks/*/spec.md and tasks/*/brief.md ONLY. Nothing else is touched.

Motivation
----------
Many GH* tasks were built by scraping real GitHub issues and pull requests.
The scraped text carries third-party personal data into a published benchmark:
real names, personal email addresses, and GitHub account handles. The
checklist for this work claimed "no scraped personal data", which was false.

What gets redacted
------------------
  emails    ->  [email redacted]
  reporter  ->  [reporter]          (the "**Reporter**: Name (email)" pattern)
  @handle   ->  [user]
  bare GitHub profile URLs -> https://github.com/[user]

What is deliberately NOT redacted (over-redaction breaks tasks)
---------------------------------------------------------------
  * Anything inside a fenced code block (``` / ~~~), except attribution-key
    lines and real-mail-provider addresses (see EMAIL rules below). Diff
    hunks, test fixtures and sample code must survive byte-identical.
  * Anything inside an inline code span (`like this`). This is what protects
    e.g. INT1_pipeline_repair's `user+tag@example.com` requirement and
    DS30_data_contract's `bad email@x.com` validation example.
  * Decorators. `@property`, `@pytest.mark`, `@staticmethod`, `@dataclass`,
    `@ts-ignore` and friends are code, not people. They are additionally
    guarded by DECORATOR_ALLOWLIST for the case where a decorator appears in
    prose or in an unfenced indented block.
  * Placeholder / documentation addresses (example.com and friends) even when
    they appear outside code, because tasks assert on them.

Usage
-----
  python3 scripts/redact_pii.py --report            # inventory only, no writes
  python3 scripts/redact_pii.py --apply             # redact in place
  python3 scripts/redact_pii.py --verify            # confirm residual counts
  python3 scripts/redact_pii.py --restore           # undo, from the manifest

The script is idempotent: a second --apply is a no-op. Every changed line is
recorded in scripts/pii_redaction_manifest.json with its original text, so
--restore returns the tree byte-for-byte.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASKS = os.path.join(REPO, "tasks")
MANIFEST = os.path.join(REPO, "scripts", "pii_redaction_manifest.json")
TARGET_FILES = ("spec.md", "brief.md")

EMAIL_TOKEN = "[email redacted]"
REPORTER_TOKEN = "[reporter]"
USER_TOKEN = "[user]"

# --------------------------------------------------------------------------
# Patterns
# --------------------------------------------------------------------------

# Local part must START alphanumeric. This is what stops a unified-diff line
# such as "-@ray.remote" / "+@ray.remote" from being read as an address.
EMAIL_RE = re.compile(
    r"(?<![\w.+-])[A-Za-z0-9_%][A-Za-z0-9._%+\-]*@[A-Za-z0-9]([A-Za-z0-9.\-]*[A-Za-z0-9])?\.[A-Za-z]{2,}"
)

# A GitHub handle mention. The (?<![\w/]) guard keeps us out of URLs
# (github.com/foo) and out of the middle of identifiers (a@b).
# The trailing (?![A-Za-z0-9\-_/]) is what stops an npm scope such as
# "@prisma/client" from being read as a mention of a person named "prisma".
# Greedy matching plus this boundary makes the whole match fail rather than
# backtracking to a shorter bogus handle.
HANDLE_RE = re.compile(
    r"(?<![\w/])@([A-Za-z0-9][A-Za-z0-9\-_]{0,37}(?:\[bot\])?)(?![A-Za-z0-9\-_/])"
)

FENCE_RE = re.compile(r"^\s{0,3}(```|~~~)")
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")

# Line splitting that preserves the exact terminator. Reading these files in
# Python's default universal-newline mode and writing them back silently
# rewrites CRLF to LF, which is an unrequested byte-level edit to scraped
# issue text. Everything below therefore reads with newline="" and carries
# each line's own terminator through untouched.
LINE_TERM_RE = re.compile(r"(\r\n|\n|\r)")

REPORTER_LINE_RE = re.compile(
    r"^(\s*\*\*(?:Reporter|Reported by|Submitter|Contact)\*\*\s*:\s*).+$"
)

# "[@handle](https://github.com/handle)" -> collapse the whole link.
PROFILE_LINK_RE = re.compile(
    r"\[@[A-Za-z0-9][A-Za-z0-9\-_]{0,37}(?:\[bot\])?\]\(https://github\.com/[A-Za-z0-9\-_]+/?\)"
)
# Bare profile URL: github.com/<one segment> and nothing after it.
PROFILE_URL_RE = re.compile(
    r"(https://github\.com/)([A-Za-z0-9][A-Za-z0-9\-_]*)(?![A-Za-z0-9\-_/])"
)

# Attribution keys inside code fences: packaging metadata, git trailers, mail
# headers. These are attribution, never assertions, so they are safe to redact
# even in a fence.
FENCE_ATTRIBUTION_KEY_RE = re.compile(
    r"^\s*(Author-email|Maintainer-email|Reporter|From|To|Cc|Signed-off-by|Co-authored-by|Committer|Reported-by)\s*:",
    re.IGNORECASE,
)
# "Author: Some Person" immediately followed by an Author-email: line.
FENCE_AUTHOR_NAME_RE = re.compile(r"^(\s*(?:Author|Maintainer)\s*:\s*)(\S.*)$")
FENCE_AUTHOR_EMAIL_NEXT_RE = re.compile(r"^\s*(?:Author|Maintainer)-email\s*:", re.I)

# Real mailbox providers. An address on one of these inside a code fence is a
# real person's mailbox pasted into an issue, not a test fixture.
REAL_MAIL_DOMAINS = {
    "gmail.com", "googlemail.com", "outlook.com", "hotmail.com", "live.com",
    "yahoo.com", "yahoo.co.uk", "protonmail.com", "proton.me", "icloud.com",
    "me.com", "mac.com", "aol.com", "gmx.de", "gmx.net", "gmx.com",
    "web.de", "qq.com", "163.com", "126.com", "yandex.ru", "mail.ru",
    "fastmail.com", "zoho.com", "hey.com", "posteo.de", "tutanota.com",
}

# Documentation / example addresses reserved by RFC 2606 and common fixtures.
# Never redacted, anywhere, because tasks assert on their exact text.
PLACEHOLDER_EMAIL_DOMAINS = {
    "example.com", "example.org", "example.net", "example.edu",
    "test.com", "test.org", "localhost", "invalid", "domain.com",
    "foo.com", "bar.com", "x.com", "email.com", "mail.com",
    "company.com", "acme.com", "corp.com", "site.com",
}

# Tokens that look like @handles but are code. Belt-and-braces on top of the
# code-fence and inline-span exclusions.
DECORATOR_ALLOWLIST = {
    # python stdlib / typing
    "property", "staticmethod", "classmethod", "abstractmethod", "overload",
    "dataclass", "dataclasses", "wraps", "cached", "cached_property",
    "contextmanager", "functools", "lru_cache", "singledispatch",
    "no_type_check", "final", "runtime_checkable", "total_ordering",
    # test frameworks
    "pytest", "mock", "patch", "fixture", "given", "parametrize", "unittest",
    "hypothesis", "mark", "settings", "example",
    # attrs / pydantic / prisma / sqlalchemy / django
    "attr", "attrs", "define", "field", "validator", "root_validator",
    "computed_field", "model_validator", "field_validator",
    "id", "updatedAt", "createdAt", "relation", "index", "map", "unique",
    "default", "db", "ignore", "override_settings", "receiver",
    "login_required", "csrf_exempt", "admin", "register", "registry",
    # ts / js
    "ts-ignore", "ts-expect-error", "ts-nocheck", "override", "Component",
    "Injectable", "NgModule", "Input", "Output", "Module", "Controller",
    # frameworks / libs seen in this corpus
    "app", "task", "dag", "serve", "ray", "torch", "np", "numpy", "jax",
    "njit", "jit", "vectorize", "guvectorize", "public_api", "callback",
    "line_profiler", "magics_class", "derived_from", "deprecate_kwarg",
    "record_usage_event", "register_lowering", "if_delegate_has_method",
    "insert_meta_param_description", "array_function_dispatch",
    "dataframe_creation_dispatch", "dataclass_state", "new_method_or_class",
    "rate_limit", "repeating", "requires_crt", "pass_context", "domain",
    "multi_ts_support", "xp_capabilities", "require_torch_greater_or_equal",
    "SESSION", "FASTPARQUET_MARK", "test", "main", "wrapt", "typing",
    "deprecated", "experimental", "abstract", "singleton", "memoize",
}


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def iter_target_files():
    """One os.scandir pass. NFS-friendly: no repeated globbing."""
    try:
        entries = sorted(os.scandir(TASKS), key=lambda e: e.name)
    except FileNotFoundError:
        sys.exit("no tasks/ directory at %s" % TASKS)
    for e in entries:
        if not e.is_dir():
            continue
        for fn in TARGET_FILES:
            p = os.path.join(e.path, fn)
            if os.path.exists(p):
                yield e.name, fn, p


def read_text(path: str) -> str:
    """Read without newline translation, so CRLF survives a round trip."""
    with open(path, encoding="utf-8", errors="replace", newline="") as f:
        return f.read()


def write_text(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def split_keepends(text: str):
    """[(body, terminator), ...]; ''.join(b + t for b, t in ...) == text."""
    parts = LINE_TERM_RE.split(text)
    pairs = [(parts[i], parts[i + 1]) for i in range(0, len(parts) - 1, 2)]
    pairs.append((parts[-1], ""))
    return pairs


def mask_inline_code(line: str) -> str:
    """Blank inline `code spans` so matches inside them are invisible."""
    return INLINE_CODE_RE.sub(lambda m: "\x00" * len(m.group(0)), line)


def email_domain(addr: str) -> str:
    return addr.rsplit("@", 1)[-1].lower()


def sub_outside_masked(line: str, masked: str, pattern, repl_fn):
    """
    Apply `pattern` against `masked` (inline code blanked) but splice the
    replacement into the real `line`, so we never edit inside a code span.
    """
    out = []
    idx = 0
    changed = False
    for m in pattern.finditer(masked):
        rep = repl_fn(m)
        if rep is None:
            continue
        out.append(line[idx:m.start()])
        out.append(rep)
        idx = m.end()
        changed = True
    out.append(line[idx:])
    return ("".join(out) if changed else line), changed


# --------------------------------------------------------------------------
# Core line transform
# --------------------------------------------------------------------------

# A mention can be dressed as code. Two shapes occur in this corpus and both
# are attribution, not program text, so they are redacted whether or not the
# line sits inside a fence:
#   `@handle`   an inline span whose ENTIRE content is one handle
#   "@handle"   a fully quoted handle, e.g. a CODEOWNERS / manifest.json entry
# Anything richer than a bare handle (`@home-assistant close`, `@pytest.mark.skip`)
# does not match, and DECORATOR_ALLOWLIST still wins over both.
CODE_SPAN_MENTION_RE = re.compile(r"`@([A-Za-z0-9][A-Za-z0-9\-_]{0,37}(?:\[bot\])?)`")
QUOTED_MENTION_RE = re.compile(r'"@([A-Za-z0-9][A-Za-z0-9\-_]{0,37}(?:\[bot\])?)"')


def redact_code_formatted_mentions(line: str, stats: Counter) -> str:
    def _span(m):
        if m.group(1) in DECORATOR_ALLOWLIST:
            return m.group(0)
        stats["mention_in_code_span"] += 1
        return USER_TOKEN

    def _quoted(m):
        if m.group(1) in DECORATOR_ALLOWLIST:
            return m.group(0)
        stats["mention_quoted"] += 1
        return '"%s"' % USER_TOKEN

    line = CODE_SPAN_MENTION_RE.sub(_span, line)
    return QUOTED_MENTION_RE.sub(_quoted, line)


def redact_line(line: str, in_fence: bool, next_line: str, stats: Counter):
    """Return the redacted line. `stats` accumulates counts by kind."""
    orig = line
    line = redact_code_formatted_mentions(line, stats)

    if in_fence:
        # Inside code: only attribution metadata and real-mailbox addresses.
        if FENCE_ATTRIBUTION_KEY_RE.match(line):
            line, ch = sub_outside_masked(
                line, line, EMAIL_RE,
                lambda m: (None if email_domain(m.group(0)) in PLACEHOLDER_EMAIL_DOMAINS
                           else EMAIL_TOKEN))
            if ch:
                stats["email_in_code_attribution"] += 1
        else:
            def _fence_email(m):
                d = email_domain(m.group(0))
                if d in PLACEHOLDER_EMAIL_DOMAINS or d not in REAL_MAIL_DOMAINS:
                    return None
                return EMAIL_TOKEN
            line, ch = sub_outside_masked(line, line, EMAIL_RE, _fence_email)
            if ch:
                stats["email_in_code_realmailbox"] += 1

        # "Author: Real Name" directly above an "Author-email:" line.
        m = FENCE_AUTHOR_NAME_RE.match(line)
        if m and FENCE_AUTHOR_EMAIL_NEXT_RE.match(next_line or ""):
            if m.group(2) != "[redacted]":   # already redacted; do not double-count
                line = m.group(1) + "[redacted]"
                stats["author_name_in_code"] += 1
        if line != orig:
            stats["lines_changed"] += 1
        return line

    # ---- outside code ----------------------------------------------------

    # 1. Whole "**Reporter**: Name (email)" line.
    m = REPORTER_LINE_RE.match(line)
    if m:
        if line == m.group(1) + REPORTER_TOKEN:
            return line          # already redacted; do not double-count
        stats["reporter_line"] += 1
        return m.group(1) + REPORTER_TOKEN

    masked = mask_inline_code(line)

    # 2. "[@handle](https://github.com/handle)" -> "[user]"
    line, ch = sub_outside_masked(line, masked, PROFILE_LINK_RE, lambda m: USER_TOKEN)
    if ch:
        stats["profile_link"] += 1
        masked = mask_inline_code(line)

    # 3. Emails.
    def _email(m):
        if email_domain(m.group(0)) in PLACEHOLDER_EMAIL_DOMAINS:
            return None
        return EMAIL_TOKEN
    line, ch = sub_outside_masked(line, masked, EMAIL_RE, _email)
    if ch:
        stats["email"] += 1
        masked = mask_inline_code(line)

    # 4. @handles (emails already gone, so no local@domain confusion).
    def _handle(m):
        h = m.group(1)
        if h in DECORATOR_ALLOWLIST:
            return None
        return USER_TOKEN
    line, ch = sub_outside_masked(line, masked, HANDLE_RE, _handle)
    if ch:
        stats["handle"] += 1
        masked = mask_inline_code(line)

    # 5. Bare GitHub profile URLs.
    line, ch = sub_outside_masked(
        line, masked, PROFILE_URL_RE,
        lambda m: m.group(1) + USER_TOKEN)
    if ch:
        stats["profile_url"] += 1

    assert line is not None
    if line != orig:
        stats["lines_changed"] += 1
    return line


def process_text(text: str, stats: Counter):
    """
    Fence tracking is a toggle, so a file with an ODD number of fence markers
    leaves every line after the last unmatched marker looking like code, and
    redaction silently stops there. Nine spec.md files in this corpus are
    malformed that way: the scraper concatenated an unterminated code block
    from an issue body with the comment thread that followed it, swallowing
    real "### Comment N (@handle):" lines into a phantom code block.

    When the markers do not balance, fence state is not trustworthy, so we
    ignore it and treat the whole file as prose. The inline-code mask and
    DECORATOR_ALLOWLIST still protect genuine code tokens. Measured on this
    corpus: that recovers 53 real handle mentions across 36 people and puts
    zero decorators at risk.
    """
    pairs = split_keepends(text)
    n_markers = sum(1 for b, _ in pairs if FENCE_RE.match(b))
    trust_fences = (n_markers % 2 == 0)
    if not trust_fences:
        stats["malformed_fence_file_prose_fallback"] += 1

    out = []
    in_fence = False
    for i, (body, term) in enumerate(pairs):
        if FENCE_RE.match(body):
            in_fence = not in_fence
            out.append(body + term)
            continue
        nxt = pairs[i + 1][0] if i + 1 < len(pairs) else ""
        eff_fence = in_fence and trust_fences
        out.append(redact_line(body, eff_fence, nxt, stats) + term)
    return "".join(out)


# --------------------------------------------------------------------------
# Commands
# --------------------------------------------------------------------------

def cmd_report(show_all: bool = False):
    emails = Counter()
    handles = Counter()
    reporters = Counter()
    profile_urls = Counter()
    by_kind = defaultdict(set)
    n_files = 0
    skipped_placeholder = Counter()
    skipped_decorator = Counter()

    for task, fn, path in iter_target_files():
        n_files += 1
        text = read_text(path)
        lines = [b for b, _ in split_keepends(text)]
        in_fence = False
        for i, ln in enumerate(lines):
            if FENCE_RE.match(ln):
                in_fence = not in_fence
                continue
            nxt = lines[i + 1] if i + 1 < len(lines) else ""
            if in_fence:
                if FENCE_ATTRIBUTION_KEY_RE.match(ln):
                    for a in EMAIL_RE.findall(ln):
                        pass
                    for m in EMAIL_RE.finditer(ln):
                        if email_domain(m.group(0)) not in PLACEHOLDER_EMAIL_DOMAINS:
                            emails[m.group(0)] += 1
                            by_kind["email"].add(task)
                else:
                    for m in EMAIL_RE.finditer(ln):
                        d = email_domain(m.group(0))
                        if d in REAL_MAIL_DOMAINS:
                            emails[m.group(0)] += 1
                            by_kind["email"].add(task)
                        elif d in PLACEHOLDER_EMAIL_DOMAINS:
                            skipped_placeholder[m.group(0)] += 1
                if FENCE_AUTHOR_NAME_RE.match(ln) and FENCE_AUTHOR_EMAIL_NEXT_RE.match(nxt):
                    reporters["(pkg metadata) " + ln.strip()] += 1
                    by_kind["reporter"].add(task)
                continue

            if REPORTER_LINE_RE.match(ln):
                reporters[ln.strip()] += 1
                by_kind["reporter"].add(task)
                continue

            masked = mask_inline_code(ln)
            for m in EMAIL_RE.finditer(masked):
                if email_domain(m.group(0)) in PLACEHOLDER_EMAIL_DOMAINS:
                    skipped_placeholder[m.group(0)] += 1
                else:
                    emails[m.group(0)] += 1
                    by_kind["email"].add(task)
            m2 = EMAIL_RE.sub(lambda m: " " * len(m.group(0)), masked)
            for m in HANDLE_RE.finditer(m2):
                if m.group(1) in DECORATOR_ALLOWLIST:
                    skipped_decorator[m.group(1)] += 1
                else:
                    handles[m.group(1)] += 1
                    by_kind["handle"].add(task)
            for m in PROFILE_URL_RE.finditer(m2):
                profile_urls[m.group(2)] += 1
                by_kind["profile_url"].add(task)

    print("=" * 74)
    print("PII INVENTORY  (tasks/*/spec.md and tasks/*/brief.md)")
    print("=" * 74)
    print("files scanned                : %d" % n_files)
    print()
    print("EMAIL ADDRESSES  : %d distinct, %d occurrences, %d task dirs"
          % (len(emails), sum(emails.values()), len(by_kind["email"])))
    for k, v in emails.most_common():
        print("      %4d  %s" % (v, k))
    print()
    print("REPORTER / AUTHOR ATTRIBUTION : %d distinct, %d occurrences, %d task dirs"
          % (len(reporters), sum(reporters.values()), len(by_kind["reporter"])))
    for k, v in reporters.most_common():
        print("      %4d  %s" % (v, k))
    print()
    print("GITHUB @HANDLES  : %d distinct, %d occurrences, %d task dirs"
          % (len(handles), sum(handles.values()), len(by_kind["handle"])))
    top = handles.most_common() if show_all else handles.most_common(25)
    for k, v in top:
        print("      %4d  @%s" % (v, k))
    if not show_all and len(handles) > 25:
        print("      ... %d more distinct handles (use --all)" % (len(handles) - 25))
    print()
    print("BARE GITHUB PROFILE URLS : %d distinct, %d occurrences, %d task dirs"
          % (len(profile_urls), sum(profile_urls.values()), len(by_kind["profile_url"])))
    for k, v in profile_urls.most_common():
        print("      %4d  https://github.com/%s" % (v, k))
    print()
    print("-" * 74)
    print("DELIBERATELY NOT REDACTED")
    print("-" * 74)
    print("placeholder/example addresses (tasks assert on these) : %d occurrences"
          % sum(skipped_placeholder.values()))
    for k, v in skipped_placeholder.most_common():
        print("      %4d  %s" % (v, k))
    print("code decorators matching @token                        : %d occurrences"
          % sum(skipped_decorator.values()))
    for k, v in skipped_decorator.most_common(15):
        print("      %4d  @%s" % (v, k))
    print()
    affected = sorted(set().union(*by_kind.values())) if by_kind else []
    print("AFFECTED TASK DIRECTORIES : %d" % len(affected))
    for t in affected:
        print("    %s" % t)
    return affected


def cmd_apply(dry_run: bool = False):
    stats = Counter()
    manifest = {
        "version": 1,
        "_warning": (
            "THIS FILE CONTAINS THE UNREDACTED PII. It stores the original "
            "text of every changed line so redaction can be reversed. It must "
            "NOT be published with the benchmark: exclude it from the release "
            "tarball and from any public git history."
        ),
        "files": {},
    }
    changed_files = 0
    for task, fn, path in iter_target_files():
        original = read_text(path)
        new = process_text(original, stats)
        if new == original:
            continue
        changed_files += 1
        rel = os.path.relpath(path, REPO)
        diffs = []
        obodies = [x for x, _ in split_keepends(original)]
        nbodies = [x for x, _ in split_keepends(new)]
        for i, (a, b) in enumerate(zip(obodies, nbodies), 1):
            if a != b:
                diffs.append({"line": i, "before": a, "after": b})
        manifest["files"][rel] = diffs
        if not dry_run:
            write_text(path, new)
    if not dry_run:
        # Merge with any earlier manifest so --restore stays complete and
        # a second --apply (a no-op) cannot wipe the record.
        if os.path.exists(MANIFEST):
            try:
                old = json.load(open(MANIFEST, encoding="utf-8"))
                for k, v in old.get("files", {}).items():
                    manifest["files"].setdefault(k, v)
            except (ValueError, OSError):
                pass
        with open(MANIFEST, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=1)
    print("%s: %d files changed, %d lines changed"
          % ("DRY RUN" if dry_run else "APPLIED", changed_files, stats["lines_changed"]))
    for k in sorted(stats):
        if k != "lines_changed":
            print("    %-32s %d" % (k, stats[k]))
    if not dry_run:
        print("    manifest -> %s" % os.path.relpath(MANIFEST, REPO))
    return changed_files


def cmd_restore():
    if not os.path.exists(MANIFEST):
        sys.exit("no manifest at %s; nothing to restore" % MANIFEST)
    manifest = json.load(open(MANIFEST, encoding="utf-8"))
    n = 0
    for rel, diffs in manifest["files"].items():
        path = os.path.join(REPO, rel)
        if not os.path.exists(path):
            print("  MISSING %s" % rel)
            continue
        pairs = split_keepends(read_text(path))
        for d in diffs:
            i = d["line"] - 1
            if 0 <= i < len(pairs) and pairs[i][0] == d["after"]:
                pairs[i] = (d["before"], pairs[i][1])
        write_text(path, "".join(b + t for b, t in pairs))
        n += 1
    print("restored %d files from manifest" % n)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--report", action="store_true", help="inventory only (default)")
    ap.add_argument("--all", action="store_true", help="report every handle, not the top 25")
    ap.add_argument("--apply", action="store_true", help="redact in place")
    ap.add_argument("--dry-run", action="store_true", help="show counts without writing")
    ap.add_argument("--verify", action="store_true", help="re-scan and print residual counts")
    ap.add_argument("--restore", action="store_true", help="undo using the manifest")
    a = ap.parse_args()

    if a.restore:
        cmd_restore()
    elif a.apply:
        cmd_apply(dry_run=False)
    elif a.dry_run:
        cmd_apply(dry_run=True)
    elif a.verify:
        cmd_report(show_all=a.all)
    else:
        cmd_report(show_all=a.all)


if __name__ == "__main__":
    main()
