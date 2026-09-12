#!/usr/bin/env python3
"""
Mine real-world ML/DS GitHub PRs for TeamBench task conversion.

Searches curated ML/DS repositories for merged bug-fix PRs that are
suitable for TeamBench benchmarking. Filters by:
  - Merged PRs that fix bugs (not features/docs)
  - ≤15 files changed, ≤500 lines changed
  - Has linked issue OR descriptive PR body
  - Has test files in the changeset (so grading is automated)

Outputs a candidate list to shared/mlds_pr_candidates.json, which
can be fed to convert_pr_to_task.py --batch.

Usage:
  # Set GITHUB_TOKEN for higher rate limits
  export GITHUB_TOKEN=ghp_...

  # Mine all target repos (default: 20 PRs per repo)
  python scripts/mine_mlds_github_prs.py --per-repo 20

  # Mine specific repos
  python scripts/mine_mlds_github_prs.py --repos scikit-learn/scikit-learn,pytorch/pytorch

  # Convert mined candidates into tasks
  python scripts/convert_pr_to_task.py --batch shared/mlds_pr_candidates.json

  # Run everything end-to-end in tmux
  tmux new-session -d -s mlds_mine "cd /u/ybkim95/TeamBench && python scripts/mine_mlds_github_prs.py && python scripts/convert_pr_to_task.py --batch shared/mlds_pr_candidates.json"
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT))

# ──── Configuration ──────────────────────────────────────────────────────────

def _load_token() -> str:
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        env_file = ROOT / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.strip().startswith("GITHUB_TOKEN="):
                    token = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    return token

GITHUB_TOKEN = _load_token()
HEADERS = {"Accept": "application/vnd.github+json"}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"
else:
    print("WARNING: No GITHUB_TOKEN set. Rate limits will be very low (60/hr).")

# ──── Target repositories ───────────────────────────────────────────────────
# Curated list of high-impact ML/DS repos with active bug-fix PRs.
# Each entry: (owner/repo, category, pip_install_hint)

ML_DS_REPOS = [
    # ── Machine Learning Frameworks ──
    ("scikit-learn/scikit-learn", "ml_framework", "pip install scikit-learn pytest -q"),
    ("pytorch/pytorch", "ml_framework", "pip install torch pytest -q"),
    ("huggingface/transformers", "ml_framework", "pip install transformers pytest -q"),
    ("keras-team/keras", "ml_framework", "pip install keras pytest -q"),
    ("Lightning-AI/pytorch-lightning", "ml_framework", "pip install pytorch-lightning pytest -q"),

    # ── Data Science / Analytics ──
    ("pandas-dev/pandas", "ds_analytics", "pip install pandas pytest -q"),
    ("numpy/numpy", "ds_analytics", "pip install numpy pytest -q"),
    ("scipy/scipy", "ds_analytics", "pip install scipy pytest -q"),
    ("statsmodels/statsmodels", "ds_analytics", "pip install statsmodels pytest -q"),
    ("dask/dask", "ds_analytics", "pip install dask pytest -q"),
    ("polars-rs/polars", "ds_analytics", "pip install polars pytest -q"),

    # ── ML Ops / Experimentation ──
    ("mlflow/mlflow", "mlops", "pip install mlflow pytest -q"),
    ("iterative/dvc", "mlops", "pip install dvc pytest -q"),
    ("wandb/wandb", "mlops", "pip install wandb pytest -q"),
    ("ray-project/ray", "mlops", "pip install ray pytest -q"),

    # ── NLP / Computer Vision ──
    ("explosion/spaCy", "nlp", "pip install spacy pytest -q"),
    ("facebookresearch/detectron2", "cv", "pip install detectron2 pytest -q"),
    ("ultralytics/ultralytics", "cv", "pip install ultralytics pytest -q"),

    # ── Data Engineering ──
    ("apache/airflow", "data_eng", "pip install apache-airflow pytest -q"),
    ("great-expectations/great_expectations", "data_eng", "pip install great_expectations pytest -q"),

    # ── Evaluation / Metrics ──
    ("huggingface/evaluate", "eval", "pip install evaluate pytest -q"),

    # ── Feature Engineering / AutoML ──
    ("alteryx/featuretools", "feature_eng", "pip install featuretools pytest -q"),
    ("autogluon/autogluon", "automl", "pip install autogluon pytest -q"),
    ("microsoft/FLAML", "automl", "pip install flaml pytest -q"),

    # ── Probabilistic / Bayesian ──
    ("pymc-devs/pymc", "bayesian", "pip install pymc pytest -q"),
    ("cornellius-gp/gpytorch", "bayesian", "pip install gpytorch pytest -q"),

    # ── Time Series ──
    ("sktime/sktime", "timeseries", "pip install sktime pytest -q"),
    ("unit8co/darts", "timeseries", "pip install darts pytest -q"),

    # ── Visualization ──
    ("matplotlib/matplotlib", "viz", "pip install matplotlib pytest -q"),
    ("plotly/plotly.py", "viz", "pip install plotly pytest -q"),
]


# ──── PR quality filters ─────────────────────────────────────────────────────

# Keywords that suggest a bug-fix PR (in title or labels)
BUG_KEYWORDS = [
    "fix", "bug", "error", "crash", "wrong", "incorrect", "regression",
    "issue", "broken", "patch", "resolve", "repair", "correct",
    "NaN", "inf", "overflow", "underflow", "leak", "deadlock",
    "race", "inconsisten", "mismatch", "invalid", "unexpected",
]

# Keywords that suggest non-bug PRs (exclude these)
EXCLUDE_KEYWORDS = [
    "doc", "typo", "readme", "deprecat", "style", "lint", "format",
    "ci", "github action", "release", "version bump", "changelog",
    "refactor", "cleanup", "rename", "move", "reorgan",
]

# Label patterns that indicate bug-fix PRs
BUG_LABELS = ["bug", "bugfix", "fix", "defect", "regression", "type:bug"]
EXCLUDE_LABELS = ["documentation", "enhancement", "feature", "wontfix", "duplicate"]

MAX_FILES = 15
MAX_LINES = 500
MIN_TESTS = 1  # Must have at least 1 test file in changeset


# ──── GitHub API ──────────────────────────────────────────────────────────────

def gh_get(url: str, params: dict = None) -> dict | list:
    if not url.startswith("http"):
        url = f"https://api.github.com{url}"
    for attempt in range(3):
        r = requests.get(url, headers=HEADERS, params=params, timeout=30)
        if r.status_code == 403 and "rate limit" in r.text.lower():
            reset = int(r.headers.get("X-RateLimit-Reset", 0))
            wait = max(reset - int(time.time()), 10)
            wait = min(wait, 120)
            remaining = r.headers.get("X-RateLimit-Remaining", "?")
            print(f"  [rate-limit] remaining={remaining}, waiting {wait}s...")
            time.sleep(wait)
            continue
        if r.status_code == 404:
            return []
        if r.status_code == 422:
            # Unprocessable — skip
            return []
        r.raise_for_status()
        return r.json()
    return []


# ──── Mining logic ────────────────────────────────────────────────────────────

@dataclass
class PRCandidate:
    repo: str
    category: str
    pr_number: int
    pr_url: str
    pr_title: str
    issue_url: str | None
    files_changed: int
    lines_changed: int
    test_files: int
    has_linked_issue: bool
    bug_score: float  # 0-1 confidence this is a real bug fix
    labels: list[str] = field(default_factory=list)


def _is_bug_fix(pr: dict) -> tuple[bool, float]:
    """Determine if a PR is likely a bug fix. Returns (is_bug, confidence)."""
    title = (pr.get("title") or "").lower()
    body = (pr.get("body") or "").lower()
    labels = [l.get("name", "").lower() for l in pr.get("labels", [])]

    score = 0.0

    # Check labels (strongest signal)
    for label in labels:
        if any(bl in label for bl in BUG_LABELS):
            score += 0.4
            break
    for label in labels:
        if any(el in label for el in EXCLUDE_LABELS):
            return False, 0.0

    # Check title keywords
    title_hits = sum(1 for kw in BUG_KEYWORDS if kw in title)
    title_excludes = sum(1 for kw in EXCLUDE_KEYWORDS if kw in title)
    if title_excludes > 0:
        return False, 0.0
    score += min(title_hits * 0.15, 0.3)

    # Check body keywords
    body_hits = sum(1 for kw in BUG_KEYWORDS if kw in body[:500])
    score += min(body_hits * 0.05, 0.15)

    # "Fixes #NNN" in body is a strong signal
    if re.search(r"(?:fixes|closes|resolves)\s+#\d+", body, re.IGNORECASE):
        score += 0.2

    return score >= 0.2, min(score, 1.0)


def _count_test_files(files: list[dict]) -> int:
    return sum(1 for f in files
               if "test" in f.get("filename", "").lower()
               and f.get("filename", "").endswith(".py"))


def mine_repo(repo: str, category: str, per_repo: int = 20) -> list[PRCandidate]:
    """Mine a single repository for suitable bug-fix PRs."""
    print(f"\n  Mining {repo} ({category})...")
    candidates = []

    # Search for merged PRs sorted by most recently updated
    # Use search API for better filtering
    query = f"repo:{repo} is:pr is:merged label:bug"
    search_results = gh_get(
        "/search/issues",
        params={"q": query, "sort": "updated", "order": "desc", "per_page": 50}
    )
    items = search_results.get("items", []) if isinstance(search_results, dict) else []

    if len(items) < 10:
        # Fallback: search without label filter
        query2 = f"repo:{repo} is:pr is:merged fix OR bug OR error in:title"
        search_results2 = gh_get(
            "/search/issues",
            params={"q": query2, "sort": "updated", "order": "desc", "per_page": 50}
        )
        items2 = search_results2.get("items", []) if isinstance(search_results2, dict) else []
        # Merge, deduplicate
        seen = {i["number"] for i in items}
        for i2 in items2:
            if i2["number"] not in seen:
                items.append(i2)
                seen.add(i2["number"])

    print(f"    Found {len(items)} candidate PRs")

    for item in items:
        if len(candidates) >= per_repo:
            break

        pr_number = item["number"]

        # Check if it's a PR (search /issues returns both)
        if "pull_request" not in item:
            continue

        # Check bug-fix likelihood
        is_bug, bug_score = _is_bug_fix(item)
        if not is_bug:
            continue

        # Fetch PR details for file count
        try:
            pr_detail = gh_get(f"/repos/{repo}/pulls/{pr_number}")
            if not pr_detail or not isinstance(pr_detail, dict):
                continue
        except Exception:
            continue

        files_changed = pr_detail.get("changed_files", 0)
        lines_changed = pr_detail.get("additions", 0) + pr_detail.get("deletions", 0)

        # Size filters
        if files_changed > MAX_FILES or files_changed == 0:
            continue
        if lines_changed > MAX_LINES or lines_changed == 0:
            continue

        # Fetch file list to count test files
        try:
            pr_files = gh_get(f"/repos/{repo}/pulls/{pr_number}/files",
                              params={"per_page": 30})
            if not isinstance(pr_files, list):
                continue
        except Exception:
            continue

        n_test_files = _count_test_files(pr_files)
        if n_test_files < MIN_TESTS:
            continue

        # Check for linked issue
        body = (item.get("body") or "").lower()
        has_issue = bool(re.search(
            r"(?:fixes|closes|resolves)\s+#\d+", body, re.IGNORECASE
        ))
        issue_url = None
        if has_issue:
            m = re.search(r"(?:fixes|closes|resolves)\s+#(\d+)", body, re.IGNORECASE)
            if m:
                issue_url = f"https://github.com/{repo}/issues/{m.group(1)}"

        labels = [l.get("name", "") for l in item.get("labels", [])]

        candidate = PRCandidate(
            repo=repo,
            category=category,
            pr_number=pr_number,
            pr_url=f"https://github.com/{repo}/pull/{pr_number}",
            pr_title=item.get("title", ""),
            issue_url=issue_url,
            files_changed=files_changed,
            lines_changed=lines_changed,
            test_files=n_test_files,
            has_linked_issue=has_issue,
            bug_score=round(bug_score, 3),
            labels=labels,
        )
        candidates.append(candidate)
        print(f"    ✓ PR #{pr_number} ({files_changed} files, {lines_changed} lines, "
              f"{n_test_files} tests, score={bug_score:.2f}): {item.get('title', '')[:60]}")

        time.sleep(0.5)  # Rate limit politeness

    return candidates


# ──── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Mine ML/DS GitHub PRs for TeamBench")
    parser.add_argument("--per-repo", type=int, default=20,
                        help="Max PRs to mine per repository")
    parser.add_argument("--repos", type=str, default="",
                        help="Comma-separated repos to mine (default: all)")
    parser.add_argument("--output", type=str,
                        default=str(ROOT / "shared" / "mlds_pr_candidates.json"))
    parser.add_argument("--dry-run", action="store_true",
                        help="Print candidates without saving")
    args = parser.parse_args()

    # Select repos
    if args.repos:
        repo_names = set(args.repos.split(","))
        repos = [(r, c, p) for r, c, p in ML_DS_REPOS if r in repo_names]
    else:
        repos = ML_DS_REPOS

    print(f"\n{'='*70}")
    print(f"  TeamBench ML/DS GitHub PR Mining Pipeline")
    print(f"  Repos: {len(repos)}")
    print(f"  Per-repo limit: {args.per_repo}")
    print(f"  Token: {'set' if GITHUB_TOKEN else 'NOT SET (low rate limit!)'}")
    print(f"  Started: {datetime.now(timezone.utc).isoformat()}")
    print(f"{'='*70}")

    all_candidates: list[PRCandidate] = []

    for repo, category, pip_hint in repos:
        try:
            candidates = mine_repo(repo, category, per_repo=args.per_repo)
            all_candidates.extend(candidates)
        except Exception as e:
            print(f"    ERROR mining {repo}: {type(e).__name__}: {e}")
            continue
        time.sleep(1)  # Between repos

    # Sort by bug_score descending
    all_candidates.sort(key=lambda c: -c.bug_score)

    # Build output in the format convert_pr_to_task.py --batch expects
    batch_output = []
    for i, c in enumerate(all_candidates):
        # Generate task_id: GHML_{i+1}_{repo_short}_{pr_number}
        repo_short = c.repo.split("/")[1].replace("-", "_")[:15]
        task_id = f"GH{858 + i + 1}_{repo_short}_{c.pr_number}"

        batch_output.append({
            "pr": c.pr_url,
            "id": task_id,
            "repo": c.repo,
            "category": c.category,
            "bug_score": c.bug_score,
            "files_changed": c.files_changed,
            "lines_changed": c.lines_changed,
            "test_files": c.test_files,
            "has_linked_issue": c.has_linked_issue,
            "labels": c.labels,
        })

    # Summary
    print(f"\n{'='*70}")
    print(f"  MINING RESULTS")
    print(f"  Total candidates: {len(all_candidates)}")
    by_cat = {}
    for c in all_candidates:
        by_cat.setdefault(c.category, []).append(c)
    for cat, cs in sorted(by_cat.items()):
        print(f"    {cat}: {len(cs)} PRs")
    print(f"  Avg bug_score: {sum(c.bug_score for c in all_candidates) / max(len(all_candidates), 1):.3f}")
    print(f"  With linked issue: {sum(1 for c in all_candidates if c.has_linked_issue)}/{len(all_candidates)}")
    print(f"{'='*70}")

    if args.dry_run:
        print("\n  [DRY RUN] Not saving. Use without --dry-run to save.")
        for entry in batch_output[:10]:
            print(f"    {entry['id']}: {entry['pr']}")
        return

    # Save
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(batch_output, f, indent=2)
    print(f"\n  Saved {len(batch_output)} candidates to: {args.output}")
    print(f"\n  Next step: python scripts/convert_pr_to_task.py --batch {args.output}")


if __name__ == "__main__":
    main()
