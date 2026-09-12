#!/usr/bin/env python3
"""
Automated GitHub PR-to-TeamBench task conversion pipeline.

Converts a real GitHub PR into a TeamBench task with information asymmetry:
  - spec.md = issue body + root-cause comments (Planner sees this)
  - brief.md = PR title + one-line summary (Executor sees this)
  - workspace/ = pre-PR state of changed files (buggy version)
  - grade.sh = runs the PR's own test suite
  - generators/gen_{task_id}.py = parameterized generator

Usage:
    python scripts/convert_pr_to_task.py --pr https://github.com/pallets/click/pull/2956 --id GH17_click_envvar
    python scripts/convert_pr_to_task.py --batch shared/github_pr_candidates.json
    python scripts/convert_pr_to_task.py --pr URL --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
import textwrap
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent.resolve()

# Load token from env or .env file
def _load_token() -> str:
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        env_file = REPO_ROOT / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if line.startswith("GITHUB_TOKEN="):
                    token = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    return token

GITHUB_TOKEN = _load_token()
HEADERS = {"Accept": "application/vnd.github+json"}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"

# Limits
MAX_FILES_CHANGED = 15
MAX_LINES_CHANGED = 500

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class PRMetadata:
    repo: str               # e.g. "pallets/click"
    pr_number: int
    pr_title: str
    pr_body: str
    pr_url: str
    base_sha: str           # commit SHA before the PR (buggy state)
    head_sha: str           # commit SHA after the PR (fixed state)
    additions: int
    deletions: int
    merged_at: Optional[str]

    # Linked issue (may be None)
    issue_number: Optional[int] = None
    issue_title: Optional[str] = None
    issue_body: Optional[str] = None
    issue_comments: list[dict] = field(default_factory=list)

    # Files changed
    changed_files: list[dict] = field(default_factory=list)  # GitHub file objects
    review_comments: list[dict] = field(default_factory=list)

    @property
    def python_files(self) -> list[str]:
        return [f["filename"] for f in self.changed_files
                if f["filename"].endswith(".py")]

    @property
    def test_files(self) -> list[str]:
        return [f["filename"] for f in self.changed_files
                if "test" in f["filename"].lower() and f["filename"].endswith(".py")]

    @property
    def source_files(self) -> list[str]:
        """Non-test Python files changed."""
        return [f for f in self.python_files if f not in self.test_files]

    @property
    def total_lines(self) -> int:
        return self.additions + self.deletions


@dataclass
class ConversionResult:
    task_id: str
    task_dir: Path
    generator_path: Path
    files_created: list[str]
    workspace_files: list[str]
    test_files: list[str]
    warnings: list[str]


# ---------------------------------------------------------------------------
# GitHub API helpers
# ---------------------------------------------------------------------------

def gh_get(url: str, params: dict = None) -> dict | list:
    """GET from GitHub API with automatic rate-limit handling."""
    if not url.startswith("http"):
        url = f"https://api.github.com{url}"
    for attempt in range(3):
        r = requests.get(url, headers=HEADERS, params=params, timeout=20)
        if r.status_code == 403 and "rate limit" in r.text.lower():
            reset = int(r.headers.get("X-RateLimit-Reset", 0))
            wait = max(reset - int(time.time()), 10)
            wait = min(wait, 120)
            print(f"  [rate-limit] waiting {wait}s...")
            time.sleep(wait)
            continue
        if r.status_code == 404:
            raise FileNotFoundError(f"Not found: {url}")
        if r.status_code == 403:
            msg = r.json().get("message", r.text)
            if "private" in msg.lower() or "repository" in msg.lower():
                raise PermissionError(f"Private repo or insufficient token: {msg}")
            raise PermissionError(f"GitHub 403: {msg}")
        r.raise_for_status()
        return r.json()
    raise RuntimeError(f"GitHub API failed after retries: {url}")


def gh_get_raw(url: str) -> str:
    """Fetch raw file content from GitHub."""
    headers = dict(HEADERS)
    headers["Accept"] = "application/vnd.github.raw+json"
    for attempt in range(3):
        r = requests.get(url, headers=headers, timeout=20)
        if r.status_code == 404:
            return None
        if r.status_code == 403 and "rate limit" in r.text.lower():
            time.sleep(30)
            continue
        r.raise_for_status()
        return r.text
    return None


def parse_pr_url(url: str) -> tuple[str, int]:
    """Parse 'https://github.com/owner/repo/pull/NNN' -> ('owner/repo', NNN)."""
    m = re.match(r"https://github\.com/([^/]+/[^/]+)/pull/(\d+)", url.rstrip("/"))
    if not m:
        raise ValueError(
            f"Invalid PR URL: {url!r}\n"
            "Expected: https://github.com/owner/repo/pull/NNN"
        )
    return m.group(1), int(m.group(2))


def find_linked_issue_number(pr: dict, repo: str) -> Optional[int]:
    """
    Find the issue number linked to this PR.

    Checks:
    1. PR body for 'Fixes #NNN', 'Closes #NNN', 'Resolves #NNN'
    2. PR timeline events for cross-referenced issues
    """
    body = (pr.get("body") or "").lower()
    patterns = [
        r"(?:fixes|closes|resolves|fix|close|resolve)\s+#(\d+)",
        r"(?:fixes|closes|resolves|fix|close|resolve)\s+https://github\.com/[^/]+/[^/]+/issues/(\d+)",
    ]
    for pat in patterns:
        m = re.search(pat, body, re.IGNORECASE)
        if m:
            return int(m.group(1))

    # Try timeline
    try:
        events = gh_get(f"/repos/{repo}/issues/{pr['number']}/timeline",
                        params={"per_page": 100})
        for ev in events:
            if ev.get("event") == "cross-referenced":
                src = ev.get("source", {})
                issue = src.get("issue", {})
                if issue and "pull_request" not in issue:
                    return issue["number"]
    except Exception:
        pass

    return None


# ---------------------------------------------------------------------------
# Step 1: Extract PR metadata
# ---------------------------------------------------------------------------

def extract_pr_metadata(repo: str, pr_number: int) -> PRMetadata:
    """Fetch all relevant PR data from GitHub."""
    print(f"  Fetching PR {repo}#{pr_number}...")

    pr = gh_get(f"/repos/{repo}/pulls/{pr_number}")
    if not pr.get("merged_at"):
        print(f"  WARNING: PR #{pr_number} is not merged (state={pr.get('state')}). Proceeding anyway.")

    base_sha = pr["base"]["sha"]
    head_sha = pr["head"]["sha"]

    # Changed files (paginated)
    changed_files = []
    page = 1
    while True:
        page_files = gh_get(f"/repos/{repo}/pulls/{pr_number}/files",
                            params={"per_page": 100, "page": page})
        if not page_files:
            break
        changed_files.extend(page_files)
        if len(page_files) < 100:
            break
        page += 1

    # Validate size
    if len(changed_files) > MAX_FILES_CHANGED:
        raise ValueError(
            f"PR changes {len(changed_files)} files (max={MAX_FILES_CHANGED}). "
            "Too broad for a focused task."
        )
    total_lines = pr.get("additions", 0) + pr.get("deletions", 0)
    if total_lines > MAX_LINES_CHANGED:
        raise ValueError(
            f"PR changes {total_lines} lines (max={MAX_LINES_CHANGED}). "
            "Too large for automated conversion."
        )

    # PR review comments (top 20 most relevant)
    try:
        review_comments = gh_get(f"/repos/{repo}/pulls/{pr_number}/comments",
                                  params={"per_page": 20})
    except Exception:
        review_comments = []

    # Linked issue
    issue_number = find_linked_issue_number(pr, repo)
    issue_title = None
    issue_body = None
    issue_comments = []

    if issue_number:
        print(f"  Linked issue: #{issue_number}")
        try:
            issue = gh_get(f"/repos/{repo}/issues/{issue_number}")
            issue_title = issue.get("title", "")
            issue_body = issue.get("body") or ""
            raw_comments = gh_get(f"/repos/{repo}/issues/{issue_number}/comments",
                                   params={"per_page": 10})
            issue_comments = raw_comments[:10]
        except FileNotFoundError:
            print(f"  WARNING: Issue #{issue_number} not found (may be in different repo).")
    else:
        print(f"  No linked issue found — using PR description as spec source.")

    meta = PRMetadata(
        repo=repo,
        pr_number=pr_number,
        pr_title=pr.get("title", ""),
        pr_body=pr.get("body") or "",
        pr_url=pr.get("html_url", f"https://github.com/{repo}/pull/{pr_number}"),
        base_sha=base_sha,
        head_sha=head_sha,
        additions=pr.get("additions", 0),
        deletions=pr.get("deletions", 0),
        merged_at=pr.get("merged_at"),
        issue_number=issue_number,
        issue_title=issue_title,
        issue_body=issue_body,
        issue_comments=issue_comments,
        changed_files=changed_files,
        review_comments=review_comments,
    )
    return meta


# ---------------------------------------------------------------------------
# Step 2: Build information asymmetry docs
# ---------------------------------------------------------------------------

def build_spec_md(meta: PRMetadata, task_id: str) -> str:
    """
    spec.md = rich info for Planner: issue body + root-cause comments + solution.
    This is the 'full picture' that creates the information asymmetry.
    """
    issue_ref = (f"https://github.com/{meta.repo}/issues/{meta.issue_number}"
                 if meta.issue_number else "N/A")
    pr_ref = meta.pr_url

    lines = [
        f"# {task_id}: {meta.pr_title} — Full Specification (Planner Only)",
        "",
        "## Source",
        f"- PR: {pr_ref}",
        f"- Issue: {issue_ref}",
        f"- Repo: https://github.com/{meta.repo}",
        "",
    ]

    # Issue description (main spec signal)
    if meta.issue_body:
        lines += [
            "## Issue Description",
            "",
            meta.issue_body.strip(),
            "",
        ]
    elif meta.pr_body:
        lines += [
            "## PR Description",
            "",
            meta.pr_body.strip(),
            "",
        ]

    # Issue comments (discussion = asymmetry source)
    if meta.issue_comments:
        lines += ["## Issue Discussion (Root Cause Analysis)", ""]
        for i, c in enumerate(meta.issue_comments, 1):
            author = c.get("user", {}).get("login", "unknown")
            body = (c.get("body") or "").strip()
            if body:
                lines += [f"### Comment {i} (@{author}):", "", body, ""]

    # PR review comments (code-level discussion)
    relevant_reviews = [c for c in meta.review_comments
                        if (c.get("body") or "").strip()][:5]
    if relevant_reviews:
        lines += ["## PR Review Comments", ""]
        for c in relevant_reviews:
            author = c.get("user", {}).get("login", "unknown")
            path = c.get("path", "")
            body = (c.get("body") or "").strip()
            lines += [f"**@{author}** on `{path}`:", "", body, ""]

    # Files involved
    lines += [
        "## Files Changed in Fix",
        "",
    ]
    for f in meta.changed_files:
        fname = f["filename"]
        adds = f.get("additions", 0)
        dels = f.get("deletions", 0)
        status = f.get("status", "modified")
        lines.append(f"- `{fname}` ({status}, +{adds}/-{dels})")

    # Patch summary for source files
    source_patches = [(f["filename"], f.get("patch", ""))
                      for f in meta.changed_files
                      if f["filename"] in meta.source_files and f.get("patch")]
    if source_patches:
        lines += ["", "## Diff Summary (What the Fix Changes)", ""]
        for fname, patch in source_patches[:5]:
            lines += [
                f"### `{fname}`",
                "```diff",
                patch[:2000],  # truncate very large patches
                "```",
                "",
            ]

    lines += [
        "## Acceptance Criteria",
        "",
        "1. All tests in the test suite pass: `pytest -x -q`",
        "2. No regressions in unchanged functionality",
        "3. Fix matches the approach described in the issue/PR discussion above",
        "",
        "## Important Notes",
        "",
        "- Only modify the source files listed above (not test files)",
        "- The test files already encode the correct expected behaviour",
        "- Run `pytest -x -q` to verify your fix",
        "",
    ]

    return "\n".join(lines)


def build_brief_md(meta: PRMetadata, task_id: str) -> str:
    """
    brief.md = intentionally vague — just PR title + one-liner.
    The Executor gets this; the gap vs spec.md IS the teamwork signal.
    """
    # Derive a one-line summary from the PR title
    title = meta.pr_title.strip()

    # What files to look at
    src_files = meta.source_files[:5]
    file_list = "\n".join(f"- `{f}`" for f in src_files) if src_files else "- (see workspace)"

    test_files = meta.test_files[:3]
    test_cmd = "pytest -x -q"
    if test_files:
        test_cmd = f"pytest {' '.join(test_files)} -x -q"

    return textwrap.dedent(f"""\
        # {task_id}: {title} (Brief)

        Fix the bug described by the Planner's guidance in the workspace.

        ## Files That May Need Changes

        {file_list}

        ## Verification

        Run the test suite to confirm your fix:

        ```
        {test_cmd}
        ```

        Do NOT modify test files.

        Follow the Planner's guidance precisely.
    """)


# ---------------------------------------------------------------------------
# Step 3: Extract workspace (pre-PR buggy state)
# ---------------------------------------------------------------------------

def fetch_file_at_sha(repo: str, path: str, sha: str) -> Optional[str]:
    """Fetch a file's content at a specific git commit SHA."""
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    content = gh_get_raw(url + f"?ref={sha}")
    if content is None:
        # Try via git blob
        try:
            tree_data = gh_get(f"/repos/{repo}/git/trees/{sha}",
                               params={"recursive": "1"})
            for item in tree_data.get("tree", []):
                if item.get("path") == path and item.get("type") == "blob":
                    blob = gh_get(f"/repos/{repo}/git/blobs/{item['sha']}")
                    import base64
                    if blob.get("encoding") == "base64":
                        return base64.b64decode(blob["content"]).decode("utf-8", errors="replace")
        except Exception:
            pass
    return content


def extract_workspace(meta: PRMetadata) -> dict[str, str]:
    """
    Download the pre-PR (base_sha) state of changed files.
    These are the buggy versions the agent must fix.
    """
    workspace: dict[str, str] = {}
    warnings: list[str] = []

    for file_info in meta.changed_files:
        fname = file_info["filename"]
        status = file_info.get("status", "modified")

        # Skip deleted files — they didn't exist before
        if status == "removed":
            continue

        # For added files: the pre-PR state doesn't have them, skip
        # (they are new files the PR introduces; the agent would add them)
        if status == "added":
            # If it's a test file added by the PR, we DO want it in workspace
            # (the test defines what passes). Otherwise skip.
            if "test" in fname.lower():
                content = fetch_file_at_sha(meta.repo, fname, meta.head_sha)
                if content:
                    workspace[fname] = content
            continue

        # For modified files: fetch the base (buggy) version
        content = fetch_file_at_sha(meta.repo, fname, meta.base_sha)
        if content is None:
            print(f"    WARNING: could not fetch pre-PR state of {fname}, skipping")
            continue

        workspace[fname] = content
        time.sleep(0.3)  # be polite to GitHub

    return workspace


# ---------------------------------------------------------------------------
# Step 4: Generate grade.sh
# ---------------------------------------------------------------------------

def generate_grade_sh(meta: PRMetadata, task_id: str) -> str:
    """
    Generate a grade.sh that runs the PR's test suite.
    Uses grader_helpers.sh pattern consistent with other TeamBench tasks.
    """
    test_files = meta.test_files
    source_files = meta.source_files[:5]

    # Build pip install line based on repo
    repo_name = meta.repo.split("/")[1]
    pip_install = _guess_pip_install(meta.repo, meta.changed_files)

    if test_files:
        test_invocation = f"pytest {' '.join(test_files)} -x -q --tb=short 2>&1"
        grade_strategy = "pytest"
    else:
        # No test files in the PR — use a basic import check
        test_invocation = "python -m pytest -x -q --tb=short 2>&1 || true"
        grade_strategy = "generic"

    script = textwrap.dedent(f"""\
        #!/usr/bin/env bash
        # Grader for {task_id}
        # Source: {meta.pr_url}
        # Repo:   https://github.com/{meta.repo}
        set -euo pipefail

        WORKSPACE="${{1:-${{WORKSPACE_DIR:-/workspace}}}}"
        REPORTS="${{2:-${{REPORTS_DIR:-/reports}}}}"

        source "$(dirname "$0")/../../harness/grader_helpers.sh"

        init_grader 5
        cd "${{WORKSPACE}}"

        # ── Install dependencies ──────────────────────────────────────────────
        {pip_install}

        # ── C1: Test suite passes ─────────────────────────────────────────────
        pytest_out=$({test_invocation})
        pytest_exit=$?
        if [ $pytest_exit -eq 0 ]; then
            check "C1" "test suite passes" "pass"
        else
            check "C1" "test suite passes" "fail"
        fi

        # ── C2: Source files are syntactically valid Python ───────────────────
        syntax_ok=true
        for src in {" ".join(source_files) if source_files else "*.py"}; do
            if [ -f "$src" ]; then
                python3 -c "import ast; ast.parse(open('$src').read())" 2>/dev/null || {{
                    syntax_ok=false
                    break
                }}
            fi
        done
        check "C2" "source files are valid Python" "$([ $syntax_ok = true ] && echo pass || echo fail)"

        # ── C3: No test files modified ────────────────────────────────────────
        # (Agents must not cheat by patching tests)
        tests_unmodified=true
        for tfile in {" ".join(test_files) if test_files else "tests/"}; do
            if [ -f "$tfile" ]; then
                # Check file exists and has test functions (basic sanity)
                python3 -c "
        import ast, sys
        src = open('$tfile').read()
        tree = ast.parse(src)
        fns = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name.startswith('test_')]
        sys.exit(0 if fns else 1)
        " 2>/dev/null || tests_unmodified=false
            fi
        done
        check "C3" "test files present and intact" "$([ $tests_unmodified = true ] && echo pass || echo fail)"

        # C4 ("no test failures (0 FAILED)") was removed 2026-09-04. It counted
        # lines matching ^FAILED, but a pytest COLLECTION error prints ERROR, so
        # the check free-passed exactly when the suite was most broken; measured
        # 40/40 free passes on pristine workspaces. It also duplicated C1.

        # ── C5: Import of fixed modules succeeds ──────────────────────────────
        import_ok=true
        for src in {" ".join(source_files) if source_files else "*.py"}; do
            if [ -f "$src" ]; then
                python3 - "$src" <<'PYEOF' 2>/dev/null || import_ok=false
import importlib.util, sys
src_path = sys.argv[1]
spec = importlib.util.spec_from_file_location('mod', src_path)
mod = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(mod)
except Exception:
    sys.exit(1)
PYEOF
            fi
        done
        check "C5" "source modules import without error" "$([ $import_ok = true ] && echo pass || echo fail)"

        finalize_grader
    """)

    return script


def _guess_pip_install(repo: str, changed_files: list[dict]) -> str:
    """Guess pip install command based on repo conventions."""
    has_requirements = any(
        f["filename"] in ("requirements.txt", "requirements-dev.txt", "requirements/test.txt")
        for f in changed_files
    )
    if has_requirements:
        return "pip install -r requirements.txt -q 2>/dev/null || true"

    # Common well-known repos
    known = {
        "pallets/flask": "pip install flask pytest -q 2>/dev/null || true",
        "pallets/click": "pip install click pytest -q 2>/dev/null || true",
        "psf/requests": "pip install requests pytest -q 2>/dev/null || true",
        "encode/httpx": "pip install httpx pytest anyio -q 2>/dev/null || true",
        "pydantic/pydantic": "pip install pydantic pytest -q 2>/dev/null || true",
        "encode/starlette": "pip install starlette pytest anyio httpx -q 2>/dev/null || true",
        "aio-libs/aiohttp": "pip install aiohttp pytest -q 2>/dev/null || true",
    }
    if repo in known:
        return known[repo]

    return ("pip install pytest -q 2>/dev/null || true\n"
            "# TODO(blocking): add this repo's runtime dependencies here, then\n"
            "# delete the guard below. Without them pytest cannot collect and C1\n"
            "# is unreachable for every agent, which is how 600 graders shipped.\n"
            'if [ -z "${TB_ALLOW_UNPINNED_DEPS:-}" ]; then\n'
            '    echo "grader not curated: dependencies unfilled" >&2\n'
            '    check "C0" "grader dependencies declared" "fail"\n'
            "fi")


# ---------------------------------------------------------------------------
# Step 5: Parameterize (seed-based variable renaming)
# ---------------------------------------------------------------------------

def generate_parameterization_pools(meta: PRMetadata) -> dict:
    """
    Build seed-based parameterization pools.

    For GH tasks the parameterization is light: we rename string literals
    (e.g., function names, variable names, module names) across seeds to
    prevent direct memorization while keeping the bug structure identical.
    """
    repo_short = meta.repo.split("/")[1]

    # Extract identifiers from source patches to create rename pools
    all_identifiers = set()
    for f in meta.changed_files:
        patch = f.get("patch", "") or ""
        # Find Python identifiers that look like user-defined names
        found = re.findall(r'\b([a-z][a-z0-9_]{3,20})\b', patch)
        all_identifiers.update(found)

    # Filter out common keywords and builtins
    _SKIP = {
        "self", "cls", "args", "kwargs", "return", "import", "from", "class",
        "def", "if", "else", "elif", "for", "while", "with", "pass", "none",
        "true", "false", "raise", "except", "finally", "yield", "async", "await",
        "print", "open", "list", "dict", "set", "tuple", "str", "int", "bool",
        "type", "isinstance", "hasattr", "getattr", "setattr", "super", "object",
        "property", "staticmethod", "classmethod", "lambda", "assert",
    }
    candidates = sorted(all_identifiers - _SKIP)[:10]

    return {
        "repo": meta.repo,
        "repo_short": repo_short,
        "parameterized_identifiers": candidates,
        "seed_variants": [
            {"seed": 0, "suffix": ""},
            {"seed": 1, "suffix": "_v2"},
            {"seed": 2, "suffix": "_v3"},
        ],
    }


# ---------------------------------------------------------------------------
# Step 6: Create task structure
# ---------------------------------------------------------------------------

def slugify(task_id: str) -> str:
    return task_id.lower().replace("-", "_")


def create_task_yaml(task_dir: Path, meta: PRMetadata, task_id: str) -> None:
    repo_name = meta.repo.split("/")[1]
    content = textwrap.dedent(f"""\
        task_id: {task_id}
        category: Real-World GitHub
        difficulty: medium
        languages: [python]
        description: "{meta.pr_title.replace('"', "'")}"
        tni_pattern: A
        parameterized: true
        seeds: [0, 1, 2]
        source_pr: "{meta.pr_url}"
        source_issue: "{f'https://github.com/{meta.repo}/issues/{meta.issue_number}' if meta.issue_number else 'N/A'}"
        network: false
        time_limit_sec: 900
        tags: [github-sourced, real-world, automated-conversion]
    """)
    path = task_dir / "task.yaml"
    path.write_text(content)


def create_generator(gen_dir: Path, meta: PRMetadata, task_id: str,
                     workspace_files: dict[str, str],
                     param_pools: dict) -> Path:
    """
    Generate generators/gen_{task_id}.py.

    The generator embeds the workspace files inline and applies light
    seed-based parameterization (variable/function name suffix renaming).
    """
    slug = slugify(task_id)
    repo = meta.repo
    pr_num = meta.pr_number
    issue_num = meta.issue_number or "N/A"

    # Embed workspace files as a Python dict literal (8-space indent inside method)
    ws_repr_lines = []
    for rel_path, content in workspace_files.items():
        # Use repr() for the value — safe, handles all escapes, no triple-quote issues
        ws_repr_lines.append(f"            {repr(rel_path)}: {repr(content)},")
    ws_repr = "\n".join(ws_repr_lines)

    # Seed-variant parameterization: rename a chosen identifier across seeds
    param_ids = param_pools.get("parameterized_identifiers", [])
    rename_target = param_ids[0] if param_ids else None

    if rename_target:
        # 8-space indent: inside generate() method body (class at 0, method at 4, body at 8)
        rename_logic = (
            "        # Apply seed-based renaming to prevent direct memorization\n"
            "        suffixes = [\"\", \"_alt\", \"_impl\"]\n"
            "        suffix = suffixes[seed % len(suffixes)]\n"
            "        if suffix:\n"
            "            for fpath in list(files.keys()):\n"
            f"                files[fpath] = files[fpath].replace({repr(rename_target)}, {repr(rename_target)} + suffix)\n"
        )
        rename_desc = f"Seed varies: renames {repr(rename_target)} identifier with suffix across seeds."
    else:
        rename_logic = "        # No parameterization applied (no suitable identifiers found)\n"
        rename_desc = "Seed varies: no significant parameterization applied."

    source_issue_url = (f"https://github.com/{repo}/issues/{issue_num}"
                        if issue_num != "N/A" else "N/A")

    # Build code at column 0 — no textwrap.dedent needed
    code = (
        f'"""\n'
        f'Parameterized generator for {task_id}.\n'
        f'\n'
        f'Source PR:    https://github.com/{repo}/pull/{pr_num}\n'
        f'Source Issue: {source_issue_url}\n'
        f'\n'
        f'{rename_desc}\n'
        f'\n'
        f'Bug: pre-PR state of workspace files contains the bug the PR fixes.\n'
        f'Fix: agent must replicate the PR\'s changes guided by spec.md.\n'
        f'"""\n'
        f'from __future__ import annotations\n'
        f'\n'
        f'import os\n'
        f'from generators.base import TaskGenerator, GeneratedTask\n'
        f'\n'
        f'\n'
        f'class Generator(TaskGenerator):\n'
        f'    task_id = {repr(task_id)}\n'
        f'    domain = "Real-World GitHub"\n'
        f'    difficulty = "medium"\n'
        f'    languages = ["python"]\n'
        f'\n'
        f'    def generate(self, seed: int) -> GeneratedTask:\n'
        f'        tasks_dir = os.path.join(\n'
        f'            os.path.dirname(__file__), "..", "tasks", {repr(task_id)}\n'
        f'        )\n'
        f'        with open(os.path.join(tasks_dir, "spec.md")) as f:\n'
        f'            spec_md = f.read()\n'
        f'        with open(os.path.join(tasks_dir, "brief.md")) as f:\n'
        f'            brief_md = f.read()\n'
        f'\n'
        f'        files = self._base_workspace()\n'
        f'{rename_logic}'
        f'        return GeneratedTask(\n'
        f'            task_id={repr(task_id)},\n'
        f'            seed=seed,\n'
        f'            spec_md=spec_md,\n'
        f'            brief_md=brief_md,\n'
        f'            expected={{\n'
        f'                "seed": seed,\n'
        f'                "repo": {repr(repo)},\n'
        f'                "pr_number": {pr_num},\n'
        f'                "bug_fixed": True,\n'
        f'            }},\n'
        f'            workspace_files=files,\n'
        f'            metadata={{\n'
        f'                "difficulty": "medium",\n'
        f'                "category": "Real-World GitHub",\n'
        f'                "source_pr": "https://github.com/{repo}/pull/{pr_num}",\n'
        f'            }},\n'
        f'        )\n'
        f'\n'
        f'    def _base_workspace(self) -> dict[str, str]:\n'
        f'        """Return the pre-PR (buggy) workspace files."""\n'
        f'        return {{\n'
        f'{ws_repr}\n'
        f'        }}\n'
    )

    gen_path = gen_dir / f"gen_{slug}.py"
    gen_path.write_text(code)
    return gen_path


# ---------------------------------------------------------------------------
# Main conversion orchestrator
# ---------------------------------------------------------------------------

def convert_pr(pr_url: str, task_id: str, dry_run: bool = False) -> ConversionResult:
    """
    Full pipeline: PR URL -> complete TeamBench task.
    """
    warnings: list[str] = []

    repo, pr_number = parse_pr_url(pr_url)
    print(f"\n{'='*60}")
    print(f"Converting PR: {pr_url}")
    print(f"Task ID:       {task_id}")
    print(f"{'='*60}")

    # Validate token
    if not GITHUB_TOKEN:
        print("WARNING: GITHUB_TOKEN not set. API rate limits will be very low (60/hr).")
        warnings.append("GITHUB_TOKEN not set — using unauthenticated API (60 req/hr limit)")

    # Step 1: Extract metadata
    print("\nStep 1: Extracting PR metadata...")
    meta = extract_pr_metadata(repo, pr_number)
    print(f"  PR:      {meta.pr_title!r}")
    print(f"  Changes: +{meta.additions}/-{meta.deletions} across {len(meta.changed_files)} files")
    print(f"  Python:  {meta.python_files}")
    print(f"  Tests:   {meta.test_files}")
    if not meta.issue_number:
        warnings.append("No linked issue found — spec.md uses PR description only")
    if not meta.test_files:
        warnings.append("No test files in PR — grade.sh uses generic pytest invocation")

    # Step 2: Build spec/brief
    print("\nStep 2: Building information asymmetry docs...")
    spec_md = build_spec_md(meta, task_id)
    brief_md = build_brief_md(meta, task_id)

    # Step 3: Extract workspace
    print("\nStep 3: Extracting pre-PR workspace (buggy state)...")
    workspace_files = extract_workspace(meta)
    print(f"  Fetched {len(workspace_files)} files")
    for fname in workspace_files:
        size = len(workspace_files[fname])
        print(f"    {fname} ({size} bytes)")

    if not workspace_files:
        raise ValueError(
            "No workspace files could be fetched. "
            "The PR may only add new files, or the base commit is not accessible."
        )

    # Step 4: Generate grader
    print("\nStep 4: Generating grade.sh...")
    grade_sh = generate_grade_sh(meta, task_id)

    # Step 5: Parameterize
    print("\nStep 5: Building parameterization pools...")
    param_pools = generate_parameterization_pools(meta)
    if param_pools["parameterized_identifiers"]:
        print(f"  Rename target: {param_pools['parameterized_identifiers'][0]!r}")
    else:
        print("  No suitable identifiers found — seeds will produce identical workspaces")
        warnings.append("No identifier parameterization applied — seeds produce identical workspaces")

    # Step 6: Create task structure
    task_dir = REPO_ROOT / "tasks" / task_id
    gen_dir = REPO_ROOT / "generators"
    slug = slugify(task_id)
    gen_path = gen_dir / f"gen_{slug}.py"

    if not dry_run:
        if task_dir.exists():
            raise FileExistsError(f"Task directory already exists: {task_dir}")
        if gen_path.exists():
            raise FileExistsError(f"Generator already exists: {gen_path}")

    print(f"\nStep 6: Creating task structure at tasks/{task_id}/...")

    files_created = []

    if dry_run:
        print("  [DRY RUN] Would create:")
        print(f"    tasks/{task_id}/task.yaml")
        print(f"    tasks/{task_id}/spec.md ({len(spec_md)} bytes)")
        print(f"    tasks/{task_id}/brief.md ({len(brief_md)} bytes)")
        print(f"    tasks/{task_id}/grade.sh")
        print(f"    tasks/{task_id}/workspace/ ({len(workspace_files)} files)")
        print(f"    generators/gen_{slug}.py")
        print("\n  [DRY RUN] spec.md preview (first 800 chars):")
        print("  " + spec_md[:800].replace("\n", "\n  "))
        print("\n  [DRY RUN] brief.md:")
        print("  " + brief_md.replace("\n", "\n  "))
    else:
        task_dir.mkdir(parents=True, exist_ok=False)
        (task_dir / "workspace").mkdir(exist_ok=True)

        # task.yaml
        create_task_yaml(task_dir, meta, task_id)
        files_created.append(str(task_dir / "task.yaml"))

        # spec.md
        (task_dir / "spec.md").write_text(spec_md)
        files_created.append(str(task_dir / "spec.md"))

        # brief.md
        (task_dir / "brief.md").write_text(brief_md)
        files_created.append(str(task_dir / "brief.md"))

        # grade.sh
        grade_path = task_dir / "grade.sh"
        grade_path.write_text(grade_sh)
        grade_path.chmod(grade_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        files_created.append(str(grade_path))

        # workspace files
        for rel_path, content in workspace_files.items():
            dest = task_dir / "workspace" / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content)
            files_created.append(str(dest))

        # curation_notes.json (for manual review)
        notes = {
            "repo": repo,
            "pr_number": pr_number,
            "pr_url": pr_url,
            "issue_number": meta.issue_number,
            "base_sha": meta.base_sha,
            "head_sha": meta.head_sha,
            "additions": meta.additions,
            "deletions": meta.deletions,
            "changed_files": [f["filename"] for f in meta.changed_files],
            "test_files": meta.test_files,
            "source_files": meta.source_files,
            "parameterization": param_pools,
            "warnings": warnings,
            "conversion_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        notes_path = task_dir / "curation_notes.json"
        notes_path.write_text(json.dumps(notes, indent=2))
        files_created.append(str(notes_path))

        # generator
        gen_path = create_generator(gen_dir, meta, task_id, workspace_files, param_pools)
        files_created.append(str(gen_path))

    return ConversionResult(
        task_id=task_id,
        task_dir=task_dir,
        generator_path=gen_path,
        files_created=files_created,
        workspace_files=list(workspace_files.keys()),
        test_files=meta.test_files,
        warnings=warnings,
    )


def print_summary(result: ConversionResult, dry_run: bool) -> None:
    mode = "[DRY RUN] " if dry_run else ""
    print(f"\n{'='*60}")
    print(f"{mode}CONVERSION COMPLETE: {result.task_id}")
    print(f"{'='*60}")
    if not dry_run:
        print(f"Task directory:  tasks/{result.task_id}/")
        print(f"Generator:       generators/gen_{slugify(result.task_id)}.py")
        print(f"Workspace files: {len(result.workspace_files)}")
        for f in result.workspace_files:
            print(f"  - {f}")
        print(f"Test files:      {result.test_files}")
        print(f"Files created:   {len(result.files_created)}")
    if result.warnings:
        print(f"\nWARNINGS ({len(result.warnings)}):")
        for w in result.warnings:
            print(f"  ! {w}")
    print(f"\nNext steps:")
    print(f"  1. Review tasks/{result.task_id}/spec.md — curate 'Key Technical Details'")
    print(f"  2. Review tasks/{result.task_id}/brief.md — confirm intentional vagueness")
    print(f"  3. Test grader: bash tasks/{result.task_id}/grade.sh tasks/{result.task_id}/workspace/ /tmp/reports/")
    print(f"  4. Validate generator: python -c \"")
    print(f"       from generators.registry import get_generator")
    print(f"       g = get_generator('{result.task_id}')")
    print(f"       t = g.generate(0); print(len(t.workspace_files), 'files')\"")
    print(f"  5. Cross-seed check: python -c \"")
    print(f"       from generators.registry import get_generator")
    print(f"       g = get_generator('{result.task_id}')")
    print(f"       print(g.validate_cross_seed(0, 1))\"")


# ---------------------------------------------------------------------------
# Batch conversion
# ---------------------------------------------------------------------------

def convert_batch(candidates_file: str, dry_run: bool = False,
                  start_id: int = 17, prefix: str = "GH") -> None:
    """
    Batch convert PRs from a candidates JSON file.

    Expected format: list of dicts with keys: url, id (optional), repo, pr.
    Falls back to shared/github_pr_candidates.json format.
    """
    candidates_path = Path(candidates_file)
    if not candidates_path.exists():
        raise FileNotFoundError(f"Candidates file not found: {candidates_file}")

    with open(candidates_path) as f:
        candidates = json.load(f)

    print(f"Loaded {len(candidates)} candidates from {candidates_file}")

    results = []
    current_id = start_id

    for i, cand in enumerate(candidates):
        # Support multiple formats
        if "url" in cand:
            pr_url = cand["url"]
        elif "pr" in cand:
            pr_val = str(cand["pr"])
            if pr_val.startswith("https://"):
                pr_url = pr_val
            elif "repo" in cand:
                pr_url = f"https://github.com/{cand['repo']}/pull/{pr_val}"
            else:
                print(f"  Skipping candidate {i}: 'pr' field is not a URL and no 'repo' to construct one")
                continue
        else:
            print(f"  Skipping candidate {i}: no 'url' or 'pr' fields")
            continue

        # Derive task_id
        if "id" in cand:
            task_id = cand["id"]
        else:
            repo_short = cand.get("repo", "unknown/repo").split("/")[1]
            # Make a slug from repo name
            slug = re.sub(r"[^a-z0-9]", "_", repo_short.lower())[:12]
            task_id = f"{prefix}{current_id}_{slug}"
            current_id += 1

        task_dir = REPO_ROOT / "tasks" / task_id
        if task_dir.exists() and not dry_run:
            print(f"\nSkipping {task_id} — task directory already exists")
            continue

        try:
            result = convert_pr(pr_url, task_id, dry_run=dry_run)
            results.append({"task_id": task_id, "status": "ok", "warnings": result.warnings})
            print_summary(result, dry_run)
        except FileExistsError as e:
            print(f"\nSkipping {task_id}: {e}")
            results.append({"task_id": task_id, "status": "skip", "reason": str(e)})
        except (ValueError, PermissionError, FileNotFoundError) as e:
            print(f"\nFailed to convert {pr_url}: {e}")
            results.append({"task_id": task_id, "status": "error", "reason": str(e)})
        except Exception as e:
            print(f"\nUnexpected error converting {pr_url}: {e}")
            results.append({"task_id": task_id, "status": "error", "reason": str(e)})

        # Pause between conversions to respect rate limits
        if not dry_run and i < len(candidates) - 1:
            time.sleep(1.0)

    print(f"\n{'='*60}")
    print("BATCH SUMMARY")
    print(f"{'='*60}")
    ok = sum(1 for r in results if r["status"] == "ok")
    skip = sum(1 for r in results if r["status"] == "skip")
    err = sum(1 for r in results if r["status"] == "error")
    print(f"  OK:      {ok}")
    print(f"  Skipped: {skip}")
    print(f"  Errors:  {err}")
    for r in results:
        marker = {"ok": "OK", "skip": "SKIP", "error": "ERR"}[r["status"]]
        print(f"  [{marker}] {r['task_id']}")
        if r.get("reason"):
            print(f"        {r['reason']}")
        if r.get("warnings"):
            for w in r["warnings"]:
                print(f"        ! {w}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Convert a GitHub PR into a TeamBench task with information asymmetry.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              # Convert a single PR
              python scripts/convert_pr_to_task.py \\
                --pr https://github.com/pallets/click/pull/2956 \\
                --id GH17_click_envvar

              # Dry run (preview without writing files)
              python scripts/convert_pr_to_task.py \\
                --pr https://github.com/pallets/click/pull/2956 \\
                --id GH17_click_envvar --dry-run

              # Batch convert from candidates file
              python scripts/convert_pr_to_task.py \\
                --batch shared/github_pr_candidates.json

              # Batch with custom starting ID
              python scripts/convert_pr_to_task.py \\
                --batch shared/github_pr_candidates.json --start-id 20
        """)
    )
    parser.add_argument("--pr", type=str, help="GitHub PR URL to convert")
    parser.add_argument("--id", type=str, help="Task ID (e.g., GH17_click_envvar)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview what would be created without writing files")
    parser.add_argument("--batch", type=str,
                        help="JSON file with list of PR candidates to batch-convert")
    parser.add_argument("--start-id", type=int, default=17,
                        help="Starting number for auto-generated task IDs in batch mode (default: 17)")
    parser.add_argument("--prefix", type=str, default="GH",
                        help="Task ID prefix for batch mode (default: GH)")

    args = parser.parse_args()

    if args.batch:
        convert_batch(args.batch, dry_run=args.dry_run,
                      start_id=args.start_id, prefix=args.prefix)
    elif args.pr:
        if not args.id:
            # Auto-derive task ID from PR URL
            repo, pr_num = parse_pr_url(args.pr)
            repo_slug = re.sub(r"[^a-z0-9]", "_", repo.split("/")[1].lower())[:12]
            args.id = f"GH{args.start_id}_{repo_slug}"
            print(f"Auto-derived task ID: {args.id}")

        result = convert_pr(args.pr, args.id, dry_run=args.dry_run)
        print_summary(result, args.dry_run)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
