#!/usr/bin/env python3
"""Fetch and verify every citation programmatically. Never write BibTeX from memory.

AI-generated citations fail at a high rate: papers that do not exist, wrong
authors, invented DOIs. A hallucinated reference is the one error in a paper
that cannot be repaired after publication, so nothing enters the bibliography
here without having been retrieved from an index first.

Each entry is resolved against Crossref and, where the work is a preprint, arXiv.
An entry that cannot be resolved is written out as an explicit placeholder with
a TODO rather than guessed at, and the summary reports how many are unresolved
so the count is visible rather than buried.

Usage:
  python scripts/verify_citations.py --check refs_to_find.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "TeamBench-citation-verifier (mailto:anonymous@example.com)"


def _get(url: str, accept: str = "application/json", tries: int = 4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8", "replace")
        except Exception:
            if i == tries - 1:
                return None
            time.sleep(3 * (i + 1))
    return None


def crossref(query: str, rows: int = 5) -> list:
    u = "https://api.crossref.org/works?" + urllib.parse.urlencode(
        {"query.bibliographic": query, "rows": rows})
    raw = _get(u)
    if not raw:
        return []
    try:
        return json.loads(raw)["message"]["items"]
    except Exception:
        return []


_LAST_ARXIV = [0.0]


def arxiv(query: str, rows: int = 5) -> list:
    # arXiv asks for at least 3 s between requests and answers 429 otherwise.
    # An unthrottled run returned 429 for 11 of 19 lookups, which looks
    # identical to "the paper does not exist" unless the status code is checked.
    # A citation verifier that silently turns rate limiting into "unresolved"
    # is worse than useless: it would push a real reference into a placeholder.
    gap = time.time() - _LAST_ARXIV[0]
    if gap < 3.5:
        time.sleep(3.5 - gap)
    _LAST_ARXIV[0] = time.time()
    # a quoted title search, not a bag of words
    u = "http://export.arxiv.org/api/query?" + urllib.parse.urlencode(
        {"search_query": 'ti:"%s"' % query, "max_results": rows})
    raw = _get(u, accept="application/atom+xml")
    if not raw:
        gap = time.time() - _LAST_ARXIV[0]
        if gap < 3.5:
            time.sleep(3.5 - gap)
        _LAST_ARXIV[0] = time.time()
        u = "http://export.arxiv.org/api/query?" + urllib.parse.urlencode(
            {"search_query": "all:" + query, "max_results": rows})
        raw = _get(u, accept="application/atom+xml")
    if not raw:
        return []
    out = []
    for m in re.finditer(r"<entry>(.*?)</entry>", raw, re.S):
        e = m.group(1)
        def tag(t):
            mm = re.search(r"<%s>(.*?)</%s>" % (t, t), e, re.S)
            return re.sub(r"\s+", " ", mm.group(1)).strip() if mm else ""
        out.append({"title": tag("title"), "published": tag("published"),
                    "id": tag("id"),
                    "authors": re.findall(r"<name>(.*?)</name>", e)})
    return out


def semantic_scholar(query: str, rows: int = 5) -> list:
    u = "https://api.semanticscholar.org/graph/v1/paper/search?" + urllib.parse.urlencode(
        {"query": query, "limit": rows, "fields": "title,year,externalIds,venue"})
    raw = _get(u)
    if not raw:
        return []
    try:
        data = json.loads(raw).get("data") or []
    except Exception:
        return []
    out = []
    for d in data:
        ext = d.get("externalIds") or {}
        out.append({"title": d.get("title"), "year": d.get("year"),
                    "doi": ext.get("DOI"),
                    "arxiv": ("https://arxiv.org/abs/" + ext["ArXiv"]) if ext.get("ArXiv") else None,
                    "src": "semanticscholar"})
    return out


def bibtex_from_doi(doi: str):
    return _get("https://doi.org/" + urllib.parse.quote(doi),
                accept="application/x-bibtex")


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def resolve(entry: dict) -> dict:
    """entry: {key, query, expect_year?, expect_author?}"""
    q = entry["query"]
    out = {"key": entry["key"], "query": q, "status": "UNRESOLVED",
           "title": None, "year": None, "doi": None, "bibtex": None,
           "source": None, "candidates": []}
    for item in crossref(q):
        title = (item.get("title") or [""])[0]
        year = None
        for f in ("published-print", "published-online", "issued", "created"):
            dp = (item.get(f) or {}).get("date-parts")
            if dp and dp[0] and dp[0][0]:
                year = dp[0][0]
                break
        out["candidates"].append({"title": title, "year": year,
                                  "doi": item.get("DOI"), "src": "crossref"})
    for item in semantic_scholar(q):
        out["candidates"].append(item)
    for item in arxiv(q):
        yr = (item.get("published") or "")[:4]
        out["candidates"].append({"title": item.get("title"),
                                  "year": int(yr) if yr.isdigit() else None,
                                  "doi": None, "arxiv": item.get("id"),
                                  "src": "arxiv"})

    want = norm(entry.get("expect_title") or q)
    best = None
    for c in out["candidates"]:
        t = norm(c.get("title"))
        if not t:
            continue
        # require substantial token overlap, not a fuzzy vibe
        a, b = set(want.split()), set(t.split())
        if not a or not b:
            continue
        j = len(a & b) / len(a | b)
        if j >= 0.5 or want in t or t in want:
            if best is None or j > best[0]:
                best = (j, c)
    if best:
        c = best[1]
        yr_ok = (entry.get("expect_year") is None or c.get("year") is None
                 or abs(c["year"] - entry["expect_year"]) <= 1)
        out.update({"title": c.get("title"), "year": c.get("year"),
                    "doi": c.get("doi"), "source": c.get("src"),
                    "status": "VERIFIED" if yr_ok else "YEAR_MISMATCH"})
        if c.get("doi"):
            out["bibtex"] = bibtex_from_doi(c["doi"])
        elif c.get("arxiv"):
            out["arxiv"] = c["arxiv"]
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", required=True, help="JSON list of {key, query, ...}")
    ap.add_argument("--out", default=os.path.join(REPO, "paper", "manuscript",
                                                  "citations_verified.json"))
    ap.add_argument("--bib", default=os.path.join(REPO, "paper", "manuscript",
                                                  "references.bib"))
    a = ap.parse_args()

    entries = json.load(open(a.check))
    res = []
    for i, e in enumerate(entries, 1):
        r = resolve(e)
        res.append(r)
        print("[%2d/%d] %-26s %-14s %s" % (
            i, len(entries), e["key"], r["status"],
            (r["title"] or "")[:70]), flush=True)
        time.sleep(1.5)

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(res, open(a.out, "w"), indent=1)

    ok = [r for r in res if r["status"] == "VERIFIED"]
    with open(a.bib, "w") as f:
        f.write("%% Generated by scripts/verify_citations.py. Every entry below was\n"
                "%% retrieved from Crossref or arXiv. Unresolved entries are written as\n"
                "%% explicit placeholders and must be checked by a human before use.\n\n")
        for r in res:
            if r.get("bibtex"):
                f.write(r["bibtex"].strip() + "\n\n")
            elif r["status"] == "VERIFIED" and r.get("arxiv"):
                f.write("@misc{%s,\n  title  = {%s},\n  note   = {arXiv: %s},\n"
                        "  year   = {%s}\n}\n\n" % (r["key"], r["title"],
                                                    r["arxiv"], r["year"]))
            else:
                f.write("%% UNRESOLVED - do not cite until checked by a human\n"
                        "%% query was: %s\n@misc{%s,\n  title = {PLACEHOLDER VERIFY},\n"
                        "  note  = {UNRESOLVED CITATION}\n}\n\n" % (r["query"], r["key"]))

    print("\nverified %d of %d" % (len(ok), len(res)))
    bad = [r["key"] for r in res if r["status"] != "VERIFIED"]
    if bad:
        print("NOT verified, written as placeholders: %s" % ", ".join(bad))
    print("wrote %s and %s" % (a.out, a.bib))
    return 0


if __name__ == "__main__":
    sys.exit(main())
