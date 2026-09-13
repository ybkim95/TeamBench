#!/usr/bin/env python3
"""A benchmark-agnostic validity audit, with criteria fixed before any data is read.

Motivation. Our own corpus reported a complete set of results while 31 of 76
graders could not separate a correct submission from an empty one, and two check
families could not be satisfied by any submission at all. That condition is
invisible to the usual reporting pipeline: a grader that awards every submission
the same score still produces a leaderboard.

The obvious objection to reporting that is "you fixed your own bug". This audit
exists to answer it. The criteria below are the benchmark-agnostic form of the
checks that caught our defects, and they are stated here, in code, before any
external dataset is downloaded. A benchmark that clears them is reported as
clear; finding nothing is a result, not a failed experiment.

Criteria, all decidable from a task's metadata without running a model:

  A1  discriminating test declared   a test that fails before the fix is named
  A2  fix touches source             the reference patch changes a non-test file
  A3  tests held out                 the discriminating tests are supplied by
                                     the harness, not shipped in the workspace.
                                     Applies only to PR-mined corpora; a
                                     bug-injection corpus has no test patch and
                                     is scored not-applicable.
  A4  no contradictory labelling     no test is listed as both fail-to-pass and
                                     pass-to-pass
  A5  held-out tests are the ones    every declared fail-to-pass test lives in a
      that discriminate              file the test patch actually touches

A1, A2 and A5 are the metadata form of the fail-to-pass criterion. A3 is the
condition whose absence let 40 of our tasks ship the acceptance criterion inside
the agent's workspace and left 189 others unable to distinguish any two
submissions.

Static by design. Running a grader requires the benchmark's own container
images and is out of scope here; what a static audit can establish is whether
the corpus is internally consistent about what discriminates.

Usage:
  python scripts/audit_external_benchmark.py --dataset princeton-nlp/SWE-bench_Verified
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import re
import sys
import urllib.parse
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "shared", "paper", "quality")
TEST_RE = re.compile(r"(^|/)(tests?|testing)/|(^|/)(test_[^/]*|[^/]*_test)\.(py|js|ts|go|rb|java)$")


def touched_files(patch: str) -> list:
    out = []
    for line in (patch or "").splitlines():
        if line.startswith("+++ "):
            p = line[4:].strip()
            p = p[2:] if p.startswith("b/") else p
            if p and p != "/dev/null":
                out.append(p)
    return out


def _test_id_to_paths(t: str) -> list:
    """Candidate source paths for a test identifier.

    Two formats occur and assuming one produced a false positive on 61% of
    SWE-bench Verified before this was fixed:

      pytest          tests/test_x.py::TestCls::test_name
      django/unittest test_name (test_utils.tests.OverrideSettingsTests)

    The second names a dotted module, not a path, so splitting on "::" returns
    the whole string and never matches any file the test patch touches. The
    dotted form is converted back to a path suffix; the comparison at the call
    site is suffix-based because a repository may or may not prefix `tests/`.
    """
    t = (t or "").strip()
    if "::" in t:
        return [t.split("::")[0]]
    m = re.match(r"^\S+\s+\(([\w.]+)\)$", t)
    if m:
        # EVERY prefix of the dotted path is a candidate module. Stripping a
        # trailing CamelCase class name is not enough: newer Django labels embed
        # the class AND the method,
        #   test_zero_values (template_tests...test_floatformat.FunctionTests.test_zero_values)
        # so the last component is lowercase and nothing gets stripped. Trying
        # all prefixes covers every variant without encoding a per-runner rule,
        # and the caller matches on suffix, so a wrong-length guess simply does
        # not match rather than producing a false verdict.
        parts = m.group(1).split(".")
        return ["/".join(parts[:i]) + ".py" for i in range(len(parts), 0, -1)]
    if t.endswith(".py"):
        return [t]
    return []


def is_test_path(p: str) -> bool:
    return bool(TEST_RE.search(p))


def fetch_rows(dataset: str, split: str, limit: int) -> list:
    """Page through the HF datasets server. No auth needed for public datasets."""
    # Cached so a rerun of the audit does not depend on the dataset server being
    # up, and so the exact rows a reported number came from stay on disk.
    cache = os.path.join(OUT, "cache_%s_%s.json" % (dataset.replace("/", "_"), split))
    if os.path.isfile(cache):
        try:
            cached = json.load(open(cache))
            if len(cached) >= min(limit, 1):
                print("  using cached rows: %d" % len(cached), flush=True)
                return cached[:limit]
        except Exception:
            pass
    import time
    rows, offset = [], 0
    while len(rows) < limit:
        q = urllib.parse.urlencode({"dataset": dataset, "config": "default",
                                    "split": split, "offset": offset, "length": 100})
        url = "https://datasets-server.huggingface.co/rows?" + q
        req = urllib.request.Request(url, headers={"User-Agent": "tb-audit"})
        j = None
        for attempt in range(6):
            try:
                with urllib.request.urlopen(req, timeout=120) as r:
                    j = json.loads(r.read())
                break
            except Exception as exc:
                if attempt == 5:
                    raise
                print("    %s; retry %d" % (str(exc)[:60], attempt + 1), flush=True)
                time.sleep(5 * (attempt + 1))
        batch = [x["row"] for x in j.get("rows", [])]
        if not batch:
            break
        rows.extend(batch)
        offset += len(batch)
        if offset >= j.get("num_rows_total", 0):
            break
    os.makedirs(OUT, exist_ok=True)
    json.dump(rows, open(cache, "w"))
    return rows[:limit]


def audit_row(r: dict) -> dict:
    gold = r.get("patch") or ""
    tpatch = r.get("test_patch") or ""

    def as_list(v):
        if isinstance(v, list):
            return v
        if isinstance(v, str) and v.strip().startswith("["):
            try:
                return json.loads(v)
            except Exception:
                return []
        return []

    f2p, p2p = as_list(r.get("FAIL_TO_PASS")), as_list(r.get("PASS_TO_PASS"))
    gold_files = touched_files(gold)
    test_files = touched_files(tpatch)
    src = [f for f in gold_files if not is_test_path(f)]

    # A5 is three-valued. Some test runners label a test by its DOCSTRING
    #   'Migration directories without an __init__.py file are loaded.'
    # which names no path at all, and some test patches supply fixture data
    # rather than the test file. In both cases the criterion cannot be decided
    # from metadata, and scoring it as a failure would be a false positive: an
    # earlier version of this audit did exactly that and reported 113 spurious
    # defects in a benchmark that has none. An audit that cries wolf is worse
    # than no audit.
    # Two further conventions make A5 undecidable rather than failed. Both were
    # found by running this audit against benchmarks with no known defect and
    # checking every reported failure by hand.
    #
    #   plugin pseudo-tests   pytest-mypy emits one "test" per source file,
    #                         `path.py::mypy` and `::mypy-status`. These are not
    #                         tests the fix patch can add.
    #   fixture-data patches  a test patch that touches only data files changes
    #                         what an EXISTING test asserts. The discriminating
    #                         test is real but lives in a file the patch never
    #                         opens.
    PLUGIN = re.compile(r"::(mypy|mypy-status|black|flake8|isort|ruff)\b")
    if any(PLUGIN.search(t or "") for t in f2p):
        parsed = {}
        undecidable = list(f2p)
    elif test_files and not any(f.endswith(".py") for f in test_files):
        parsed = {}
        undecidable = list(f2p)
    else:
        parsed = {t: _test_id_to_paths(t) for t in f2p}
        undecidable = [t for t, v in parsed.items() if not v]
    tf = set(test_files)

    def _matches(cands):
        return any(p.endswith(c) or c.endswith(p) for c in cands for p in tf)

    decidable = {t: v for t, v in parsed.items() if v}
    matched = {t for t, v in decidable.items() if _matches(v)}
    f2p_files, covered = set(decidable), matched

    return {
        "id": r.get("instance_id"),
        "A1_discriminating_test_declared": len(f2p) > 0,
        "A2_fix_touches_source": len(src) > 0,
        # A3 applies only to benchmarks MINED FROM PULL REQUESTS, where the
        # discriminating test is the one the PR adds and the agent must not see
        # it. It does not apply to bug-injection corpora such as SWE-smith,
        # which break working code so that the repository's EXISTING tests fail:
        # there the failing test is part of the problem statement and is meant
        # to be visible. Those corpora carry no test_patch field at all, and
        # scoring them as failing here would falsely condemn every instance of a
        # sound benchmark. Absence of the field means "not applicable", not
        # "failed".
        "A3_tests_held_out": (None if "test_patch" not in r
                              else len(test_files) > 0),
        "A4_no_contradictory_label": not (set(f2p) & set(p2p)),
        "A5_held_out_are_discriminating": (
            None if (undecidable or not f2p_files) else covered == f2p_files),
        "A5_undecidable_labels": len(undecidable),
        "n_fail_to_pass": len(f2p), "n_pass_to_pass": len(p2p),
        "n_source_files": len(src), "n_test_files": len(test_files),
        "gold_touches_tests_only": bool(gold_files) and not src,
    }


def local_teambench_rows(limit: int) -> list:
    """Our own corpus, expressed in the same schema, so the audit is identical.

    v1 shipped no fail-to-pass declaration at all: there was no field naming the
    test that distinguishes a fix from no fix, which is precisely the condition
    A1 exists to detect. The reference patch is reconstructed from
    tasks/<id>/reference/patch.diff and split into its source and test hunks the
    same way the external schema splits `patch` from `test_patch`, and the
    workspace is inspected to see whether the discriminating test was shipped to
    the agent.
    """
    import importlib.util
    sp = importlib.util.spec_from_file_location(
        "bvc", os.path.join(REPO, "scripts", "build_verified_core.py"))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)

    tasks_dir = os.path.join(REPO, "tasks")
    rows = []
    for d in sorted(os.listdir(tasks_dir)):
        if not d.startswith("GH") or len(rows) >= limit:
            continue
        pp = os.path.join(tasks_dir, d, "reference", "patch.diff")
        if not os.path.isfile(pp):
            continue
        patch = open(pp, encoding="utf-8", errors="replace").read()
        files, names = m.added_test_names(pp)

        # split the single diff into source and test halves
        src_parts, test_parts, cur, keep = [], [], [], None
        for line in patch.splitlines(True):
            if line.startswith("diff --git"):
                if cur:
                    (test_parts if keep else src_parts).extend(cur)
                cur, keep = [line], None
            else:
                if line.startswith("+++ ") and keep is None:
                    q = line[4:].strip()
                    q = q[2:] if q.startswith("b/") else q
                    keep = is_test_path(q)
                cur.append(line)
        if cur:
            (test_parts if keep else src_parts).extend(cur)

        # was the discriminating test shipped inside the agent's workspace?
        ws = os.path.join(tasks_dir, d, "workspace")
        leaked = False
        for f in files:
            q = os.path.join(ws, f)
            if os.path.isfile(q) and any(
                    n in open(q, errors="ignore").read() for n in names):
                leaked = True
        rows.append({
            "instance_id": d,
            "repo": (json.load(open(os.path.join(tasks_dir, d, "curation_notes.json")))
                     .get("repo") if os.path.isfile(
                         os.path.join(tasks_dir, d, "curation_notes.json")) else ""),
            "patch": "".join(src_parts),
            # v1 shipped no held-out test patch: the tests were either absent
            # from the corpus entirely or already inside the workspace
            "test_patch": "" if leaked else "".join(test_parts),
            # and no instance declared which test discriminates
            "FAIL_TO_PASS": [],
            "PASS_TO_PASS": [],
        })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True,
                    help="an HF dataset id, or `local:teambench-v1`")
    ap.add_argument("--split", default="test")
    ap.add_argument("--limit", type=int, default=1000)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    print("auditing %s (%s), criteria fixed in source before download" % (a.dataset, a.split),
          flush=True)
    rows = (local_teambench_rows(a.limit) if a.dataset.startswith("local:")
            else fetch_rows(a.dataset, a.split, a.limit))
    print("instances fetched: %d\n" % len(rows), flush=True)
    res = [audit_row(r) for r in rows]

    gates = [k for k in res[0] if k.startswith("A") and not k.endswith("_labels")]
    print("%-36s %8s %8s %12s" % ("criterion", "pass", "fail", "undecidable"))
    print("-" * 68)
    for g in gates:
        p = sum(1 for x in res if x[g] is True)
        f = sum(1 for x in res if x[g] is False)
        u = sum(1 for x in res if x[g] is None)
        print("%-36s %8d %8d %12s" % (g, p, f, u if u else "-"))

    # A criterion that could not be decided is not a failure.
    clean = sum(1 for x in res if all(x[g] is not False for g in gates))
    print("\ninstances with no criterion FAILING: %d of %d (%.1f%%)"
          % (clean, len(res), 100 * clean / max(1, len(res))))

    bad = collections.Counter()
    for x in res:
        f = tuple(g for g in gates if x[g] is False)
        if f:
            bad[f] += 1
    if bad:
        print("\nfailing combinations:")
        for k, v in bad.most_common(8):
            print("   %5d  %s" % (v, ", ".join(k)))

    # ":" is legal in a POSIX filename and breaks a checkout on macOS and
    # Windows, so it is normalised out of the dataset id.
    safe = a.dataset.replace("/", "_").replace(":", "_")
    out = a.out or os.path.join(OUT, "audit_%s.json" % safe)
    os.makedirs(OUT, exist_ok=True)
    json.dump({"dataset": a.dataset, "split": a.split, "n": len(res),
               "clean": clean, "rows": res}, open(out, "w"), indent=1)
    print("\nwrote %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
