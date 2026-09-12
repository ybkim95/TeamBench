#!/usr/bin/env python3
"""Curate real-world GitHub issues for TeamBench tasks.

Searches popular Python repos for issues that have:
  1. Natural information asymmetry (rich discussion > brief title)
  2. A linked/closing PR (ground truth for grading)
  3. Test-friendly fixes (deterministic grading possible)
  4. Small-medium scope (5-60 lines changed)

Usage:
    python scripts/curate_github_tasks.py --search
    python scripts/curate_github_tasks.py --analyze ISSUE_URL
    python scripts/curate_github_tasks.py --scaffold ISSUE_URL
"""
import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path

import requests

# Target repos: well-maintained Python projects with detailed issues
TARGET_REPOS = [
    "tiangolo/fastapi",
    "pydantic/pydantic",
    "pallets/flask",
    "psf/requests",
    "encode/httpx",
    "encode/starlette",
    "pallets/click",
    "aio-libs/aiohttp",
]

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
HEADERS = {"Accept": "application/vnd.github+json"}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"

# Issue quality filters
MIN_COMMENTS = 3
MAX_LINES_CHANGED = 200
MIN_LINES_CHANGED = 5
MAX_FILES_CHANGED = 8


def gh_get(url: str, params: dict = None) -> dict | list:
    """GET from GitHub API with rate-limit handling."""
    if not url.startswith("http"):
        url = f"https://api.github.com{url}"
    r = requests.get(url, headers=HEADERS, params=params, timeout=15)
    if r.status_code == 403 and "rate limit" in r.text.lower():
        reset = int(r.headers.get("X-RateLimit-Reset", 0))
        wait = max(reset - int(time.time()), 10)
        print(f"  Rate limited. Waiting {wait}s...")
        time.sleep(min(wait, 60))
        r = requests.get(url, headers=HEADERS, params=params, timeout=15)
    r.raise_for_status()
    return r.json()


def search_issues(repo: str, max_results: int = 15) -> list[dict]:
    """Find closed issues with many comments from a repo."""
    issues = gh_get(f"/repos/{repo}/issues", params={
        "state": "closed",
        "sort": "comments",
        "direction": "desc",
        "per_page": max_results,
    })
    # Filter out PRs (GitHub API returns PRs as issues too)
    return [i for i in issues if "pull_request" not in i]


def find_closing_pr(repo: str, issue_number: int) -> dict | None:
    """Find the PR that closed this issue via timeline events."""
    try:
        events = gh_get(f"/repos/{repo}/issues/{issue_number}/events")
        for event in events:
            if event.get("event") == "closed" and event.get("commit_id"):
                # Find PR for this commit
                try:
                    prs = gh_get(f"/repos/{repo}/commits/{event['commit_id']}/pulls")
                    if prs:
                        return prs[0]
                except Exception:
                    pass
            if event.get("event") == "referenced":
                commit_id = event.get("commit_id")
                if commit_id:
                    try:
                        prs = gh_get(f"/repos/{repo}/commits/{commit_id}/pulls")
                        if prs and prs[0].get("merged_at"):
                            return prs[0]
                    except Exception:
                        pass
    except Exception as e:
        print(f"    Events lookup failed: {e}")
    return None


def analyze_pr_files(repo: str, pr_number: int) -> dict:
    """Get PR file changes."""
    try:
        files = gh_get(f"/repos/{repo}/pulls/{pr_number}/files")
    except Exception:
        return {"files": [], "has_tests": False, "python_files": []}

    python_files = [f["filename"] for f in files if f["filename"].endswith(".py")]
    test_files = [f["filename"] for f in files if "test" in f["filename"].lower()]

    return {
        "files": [f["filename"] for f in files],
        "python_files": python_files,
        "test_files": test_files,
        "has_tests": len(test_files) > 0,
        "patches": {f["filename"]: f.get("patch", "")[:500] for f in files},
    }


def score_candidate(issue: dict, pr: dict | None, pr_files: dict | None) -> tuple[float, dict]:
    """Score an issue for TeamBench suitability."""
    title = issue.get("title", "")
    body = issue.get("body", "") or ""
    comments = issue.get("comments", 0)

    reasons = {}

    # Has linked PR?
    if pr:
        reasons["has_pr"] = True
        additions = pr.get("additions", 0)
        deletions = pr.get("deletions", 0)
        total_changes = additions + deletions
        changed_files = pr.get("changed_files", 0)

        reasons["pr_size"] = total_changes
        reasons["pr_files"] = changed_files
        reasons["size_ok"] = MIN_LINES_CHANGED <= total_changes <= MAX_LINES_CHANGED
        reasons["files_ok"] = changed_files <= MAX_FILES_CHANGED
    else:
        reasons["has_pr"] = False
        reasons["size_ok"] = False
        reasons["files_ok"] = False

    if pr_files:
        reasons["has_tests"] = pr_files["has_tests"]
        reasons["python_count"] = len(pr_files["python_files"])
    else:
        reasons["has_tests"] = False
        reasons["python_count"] = 0

    reasons["comments"] = comments
    reasons["rich_discussion"] = comments >= MIN_COMMENTS
    reasons["asymmetry"] = len(body) / max(len(title), 1)
    reasons["high_asymmetry"] = reasons["asymmetry"] > 20

    # Compute score
    score = (
        (3.0 if reasons["has_pr"] else 0) +
        (2.0 if reasons["size_ok"] else 0) +
        (3.0 if reasons["has_tests"] else 0) +
        (1.0 if reasons["files_ok"] else 0) +
        (2.0 if reasons["rich_discussion"] else 0) +
        (1.5 if reasons["high_asymmetry"] else 0) +
        (1.0 if reasons["python_count"] >= 1 else 0)
    )

    if score >= 10:
        reasons["recommendation"] = "STRONG"
    elif score >= 7:
        reasons["recommendation"] = "GOOD"
    elif score >= 4:
        reasons["recommendation"] = "MAYBE"
    else:
        reasons["recommendation"] = "SKIP"

    return score, reasons


def search_all(max_per_repo: int = 15):
    """Search all target repos for candidate issues."""
    all_results = []

    for repo in TARGET_REPOS:
        print(f"\nSearching {repo}...")
        try:
            issues = search_issues(repo, max_per_repo)
        except Exception as e:
            print(f"  Error: {e}")
            continue

        # Filter to issues with enough comments
        issues = [i for i in issues if i.get("comments", 0) >= MIN_COMMENTS]
        print(f"  {len(issues)} issues with >={MIN_COMMENTS} comments")

        for issue in issues[:8]:  # Analyze top 8 per repo
            num = issue["number"]
            title = issue["title"][:60]
            comments = issue.get("comments", 0)
            print(f"  Analyzing #{num}: {title}... ({comments} comments)")

            pr = find_closing_pr(repo, num)
            pr_files = None
            if pr:
                pr_num = pr["number"]
                print(f"    Linked PR: #{pr_num} (+{pr.get('additions',0)}/-{pr.get('deletions',0)})")
                pr_files = analyze_pr_files(repo, pr_num)
            else:
                print(f"    No linked PR found")

            score, reasons = score_candidate(issue, pr, pr_files)

            all_results.append({
                "repo": repo,
                "issue_number": num,
                "title": issue["title"],
                "url": issue["html_url"],
                "comments": comments,
                "pr_number": pr["number"] if pr else None,
                "pr_url": pr["html_url"] if pr else None,
                "score": score,
                "reasons": reasons,
            })

            # Be nice to GitHub API
            time.sleep(0.5)

    # Sort by score
    all_results.sort(key=lambda x: x["score"], reverse=True)

    # Print top candidates
    print(f"\n{'='*80}")
    print(f"TOP CANDIDATES FOR TEAMBENCH (sorted by suitability)")
    print(f"{'='*80}")

    for r in all_results[:25]:
        rec = r["reasons"]["recommendation"]
        pr_info = f"PR#{r['pr_number']}" if r["pr_number"] else "no PR"
        tests = " +TESTS" if r["reasons"].get("has_tests") else ""
        size = f" ({r['reasons'].get('pr_size', '?')} lines)" if r["reasons"].get("has_pr") else ""

        marker = {"STRONG": "***", "GOOD": "**", "MAYBE": "*", "SKIP": ""}[rec]
        print(f"\n  [{r['score']:.1f}] {marker}{rec}{marker} {r['repo']}#{r['issue_number']}")
        print(f"        {r['title'][:70]}")
        print(f"        {r['comments']} comments | {pr_info}{size}{tests}")
        print(f"        {r['url']}")

    # Save results
    outpath = "shared/github_candidates.json"
    os.makedirs("shared", exist_ok=True)
    with open(outpath, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nResults saved to {outpath} ({len(all_results)} candidates)")

    return all_results


def analyze_issue(issue_url: str):
    """Deep-analyze a single GitHub issue."""
    match = re.match(r"https://github\.com/([^/]+/[^/]+)/issues/(\d+)", issue_url)
    if not match:
        print(f"Invalid URL: {issue_url}")
        return

    repo, num = match.group(1), int(match.group(2))
    print(f"Deep-analyzing {repo}#{num}...")

    issue = gh_get(f"/repos/{repo}/issues/{num}")
    comments = gh_get(f"/repos/{repo}/issues/{num}/comments")
    pr = find_closing_pr(repo, num)

    print(f"\n  Title: {issue['title']}")
    print(f"  Labels: {[l['name'] for l in issue.get('labels', [])]}")
    print(f"  Comments: {len(comments)}")
    print(f"  Body: {len(issue.get('body', '') or '')} chars")

    if pr:
        pr_num = pr["number"]
        pr_files = analyze_pr_files(repo, pr_num)
        print(f"\n  Linked PR: #{pr_num}")
        print(f"    +{pr.get('additions', 0)}/-{pr.get('deletions', 0)} across {pr.get('changed_files', 0)} files")
        print(f"    Python files: {pr_files['python_files']}")
        print(f"    Test files: {pr_files['test_files']}")
        print(f"    Has tests: {pr_files['has_tests']}")

        score, reasons = score_candidate(issue, pr, pr_files)
        print(f"\n  Suitability: {reasons['recommendation']} (score={score:.1f})")
        for k, v in reasons.items():
            if k != "recommendation":
                print(f"    {k}: {v}")
    else:
        print(f"\n  No linked PR found — cannot grade without ground truth")

    # Print discussion summary
    print(f"\n  Discussion highlights:")
    for i, c in enumerate(comments[:5], 1):
        author = c.get("user", {}).get("login", "?")
        body = (c.get("body", "") or "")[:150].replace("\n", " ")
        print(f"    [{i}] @{author}: {body}...")

    return {"issue": issue, "comments": comments, "pr": pr}


def scaffold_task(issue_url: str, task_id: str = None):
    """Create a task scaffold from a GitHub issue."""
    match = re.match(r"https://github\.com/([^/]+/[^/]+)/issues/(\d+)", issue_url)
    if not match:
        print(f"Invalid URL: {issue_url}")
        return

    repo, num = match.group(1), int(match.group(2))
    issue = gh_get(f"/repos/{repo}/issues/{num}")
    comments = gh_get(f"/repos/{repo}/issues/{num}/comments")
    pr = find_closing_pr(repo, num)

    if not pr:
        print("ERROR: No linked PR found. Need ground truth for grading.")
        return

    pr_num = pr["number"]
    pr_files = analyze_pr_files(repo, pr_num)

    if not task_id:
        repo_short = repo.split("/")[1].replace("-", "")[:10].upper()
        task_id = f"GH{num}_{repo_short}"

    task_dir = Path("tasks") / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "workspace").mkdir(exist_ok=True)

    # task.yaml
    import yaml
    yaml_data = {
        "task_id": task_id,
        "domain": "software",
        "category": "Software Engineering",
        "difficulty": "hard",
        "languages": ["python"],
        "description": issue["title"],
        "source_issue": f"https://github.com/{repo}/issues/{num}",
        "source_pr": f"https://github.com/{repo}/pull/{pr_num}",
        "parameterized": False,
        "seeds": [0],
        "network": False,
        "time_limit_sec": 900,
        "tags": ["github-sourced", "real-world"],
    }
    with open(task_dir / "task.yaml", "w") as f:
        yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

    # brief.md
    brief = f"""# {task_id}: {issue['title']} (Brief)

Fix the reported bug in the codebase.

Run the test suite to verify your fix passes all checks.

Files that may need changes:
{chr(10).join(f'- `{f}`' for f in pr_files.get('python_files', [])[:5])}

Do NOT modify test files.
"""
    with open(task_dir / "brief.md", "w") as f:
        f.write(brief)

    # spec.md
    body = issue.get("body", "") or ""
    spec = f"""# {task_id}: {issue['title']} — Full Specification (Planner Only)

## Source
- Issue: https://github.com/{repo}/issues/{num}
- Fixing PR: https://github.com/{repo}/pull/{pr_num}

## Issue Description
{body}

## Discussion Context
"""
    for i, c in enumerate(comments[:10], 1):
        author = c.get("user", {}).get("login", "unknown")
        cbody = c.get("body", "") or ""
        spec += f"\n### Comment {i} (@{author}):\n{cbody}\n"

    spec += """
## Key Technical Details
<!-- CURATE MANUALLY: Extract the critical details from the discussion that
     the executor cannot derive from the codebase alone. This creates the
     information asymmetry that makes teamwork valuable. -->

## What to Fix
<!-- CURATE MANUALLY: Specific bug description, root cause, and fix approach
     derived from the PR diff and discussion. -->

## Important Notes
<!-- CURATE MANUALLY: Note any false positives, intentional behaviors,
     edge cases, or things NOT to change. -->
"""
    with open(task_dir / "spec.md", "w") as f:
        f.write(spec)

    # grade.sh
    grade = f"""#!/usr/bin/env bash
# Grader for {task_id} (from {repo}#{num}, PR#{pr_num})
set -euo pipefail
WORKSPACE="${{1:?}}"
REPORTS="${{2:?}}"

source "$(dirname "$0")/../../harness/grader_helpers.sh"

init_grader 5  # TODO: set correct total checks
cd "$WORKSPACE"

# TODO: Implement grading checks from the PR's test changes
# Files changed in PR: {', '.join(pr_files.get('python_files', []))}
# Test files in PR: {', '.join(pr_files.get('test_files', []))}

finalize_grader
"""
    with open(task_dir / "grade.sh", "w") as f:
        f.write(grade)
    os.chmod(task_dir / "grade.sh", 0o755)

    # Save analysis for reference
    with open(task_dir / "curation_notes.json", "w") as f:
        json.dump({
            "repo": repo,
            "issue": num,
            "pr": pr_num,
            "pr_additions": pr.get("additions", 0),
            "pr_deletions": pr.get("deletions", 0),
            "pr_files": pr_files,
            "comments_count": len(comments),
        }, f, indent=2)

    print(f"\nTask scaffold created: {task_dir}/")
    print(f"  Next steps:")
    print(f"  1. git clone {repo} workspace/ at the pre-fix commit")
    print(f"  2. Curate spec.md (fill in Key Technical Details)")
    print(f"  3. Implement grade.sh checks")
    print(f"  4. Validate: grade.sh passes on fixed code, fails on buggy code")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--search", action="store_true", help="Search repos for candidates")
    ap.add_argument("--analyze", type=str, help="Deep-analyze an issue URL")
    ap.add_argument("--scaffold", type=str, help="Scaffold a task from issue URL")
    ap.add_argument("--task-id", type=str, help="Custom task ID for scaffold")
    args = ap.parse_args()

    if args.search:
        search_all()
    elif args.analyze:
        analyze_issue(args.analyze)
    elif args.scaffold:
        scaffold_task(args.scaffold, args.task_id)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
