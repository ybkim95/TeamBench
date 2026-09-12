# GH461_splinepy_482: Retain interfaces when adding fields — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/tataratat/splinepy

## PR Description

# Overview
When adding fields, the interfaces the list of patches where saved as an _empty_ Multipatch, meaning, they had no information about the connectivity of their underlying geometry. 

## Addressed issues
- #478 

## Checklists
* [x] Documentations are up-to-date.
* [ ] Added example(s)
* [ ] Added test(s)

<!-- This is an auto-generated comment: release notes by coderabbit.ai -->
## Summary by CodeRabbit

* **New Features**
  * Added a Python-accessible API to manually set interface orientations.

* **Bug Fixes**
  * Clearer, stricter validation of interface dimensionality with improved mismatch errors.
  * Ensured newly created fields inherit existing interface data so interface settings propagate consistently.
  * Returned cached interface orientations when available to avoid redundant recomputation.

* **Documentation**
  * Updated PR template with a formatted showcase example and minor formatting improvements.
<!-- end of auto-generated comment: release notes by coderabbit.ai -->

## PR Review Comments

**[user]** on `.github/pull_request_template.md`:

_⚠️ Potential issue_ | _🟡 Minor_

**Replace the placeholder example with a concrete usage demonstration.**

The Showcase section contains placeholder pseudo-code (`splinepy.tataratat()`) that does not demonstrate the actual feature this PR introduces (retaining interfaces when adding fields). Replace this with a meaningful example showing how the fix works in practice.

<details>
<summary>🤖 Prompt for AI Agents</summary>

```
In .github/pull_request_template.md around lines 13 to 17, the Showcase example
uses placeholder pseudo-code (splinepy.tataratat()) instead of a real usage
showing the PR's behavior (retaining interfaces when adding fields). Replace the
placeholder with a concise, concrete example that demonstrates creating an
object/struct, adding fields while preserving existing interfaces, and showing
before/after or expected output; ensure the snippet uses real library/API names
and minimal realistic code that readers can copy to validate the fix.
```

</details>

<!-- This is an auto-generated comment by CodeRabbit -->

**[user]** on `.github/pull_request_template.md`:

_⚠️ Potential issue_ | _🔴 Critical_

<details>
<summary>🧩 Analysis chain</summary>

**Clarify or correct the target branch checklist item.**

The new checklist item references "develop" as the target branch, but this PR's target branch is "main" (per the PR metadata). Either update the item to match the actual target branch used in this repository, or clarify if this is a general instruction that applies conditionally.

---

I'll verify the review comment by examining the repository structure and branch conventions.

</thinking>

---

🏁 Script executed:

```shell
#!/bin/bash
# Check the pull request template content
echo "=== Pull request template content ==="
cat .github/pull_request_template.md

echo -e "\n=== Repository root files and structure ==="
ls -la | head -20

echo -e "\n=== Check for branch configuration in common files ==="
if [ -f README.md ]; then
  echo "=== README.md (checking for branch info) ==="
  grep -i "branch\|develop\|main" README.md | head -20
fi

echo -e "\n=== Check CONTRIBUTING or similar ==="
for file in CONTRIBUTING.md CONTRIBUTING docs/CONTRIBUTING.md; do
  if [ -f "$file" ]; then
    echo "=== $file (checking for branch info) ==="
    grep -i "branch\|develop\|main" "$file" | head -20
  fi
done

echo -e "\n=== Check git configuration ==="
git config --get init.defaultBranch 2>/dev/null || echo "Default branch not explicitly set in git config"
git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "Current branch unknown"
```

Length of output: 3362

---

🏁 Script executed:

```shell
#!/bin/bash
# Examine the pull request template and repository branch conventions

echo "=== Pull request template content ==="
cat .github/pull_request_template.md

echo -e "\n=== Check README for branch guidance ==="
if [ -f README.md ]; then
  grep -i "branch\|develop\|main" README.md | head -20
fi

echo -e "\n=== Check for CONTRIBUTING documentation ==="
for file in CONTRIBUTING.md docs/CONTRIBUTING.md; do
  if [ -f "$file" ]; then
    echo "=== $file ==="
    cat "$file"
  fi
done

echo -e "\n=== Search codebase for branch references ==="
grep -r "target.*branch" . --include="*.md" 2>/dev/null | grep -v ".git" | head -10
```

Length of output: 3978

---

</details>

**Update the pull request template to reflect the correct target branch.**

The repository uses "main" as its primary branch (evident from README links, CI workflows, and documentation), but the checklist item in the template still references "develop". Update line 21 from `* [ ] Set target branch to develop` to `* [ ] Set target branch to main` to align with the repository's actual branching strategy.

<details>
<summary>🤖 Prompt for AI Agents</summary>

```
.github/pull_request_template.md around line 21: the checklist item incorrectly
asks to "Set target branch to develop"; change that line to read "* [ ] Set
target branch to main" so the PR template matches the repository's actual
primary branch.
```

</details>

<!-- This is an auto-generated comment by CodeRabbit -->

**[user]** on `splinepy/multipatch.py`:

Should one introduce code to enforce this, e.g., a call to the interfaces property, which would complain in case the interfaces are not already set? This would better document the requirement and one could remove the check in `py_multipatch.cpp`.

**[user]** on `src/py/py_multipatch.cpp`:

What should the actual error message look like? I think this currently does not form a proper statement. And if `para_dim > 1` or `dim > 1` are also possible, maybe "one-dimensional" could be replaced by something like "curve" (`para_dim` is 1) or "scalar" (`dim` is 1) 🤔

**[user]** on `src/py/py_multipatch.cpp`:

Also add some punctuation here?

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
