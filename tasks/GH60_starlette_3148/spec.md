# GH60_starlette_3148: Enable `autoescape` by default in `Jinja2Templates` — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/Kludex/starlette/issues/3146
- Repo: https://github.com/Kludex/starlette

## Issue Description

# Summary

Noticed that `Jinja2Templates` currently defaults to having `autoescape` disabled. It puts the burden on the developer to remember to enable it, which I've seen lead to XSS vulnerabilities in applications that render user-provided content.

While investigating, I also discovered that `Jinja2Templates` was missing support for `**env_options` in its constructor, making it difficult to customize the environment even though the documentation suggested it was supported.

Updated the implementation to:
- Use `jinja2.select_autoescape()` by default for HTML/XML files to ensure a secure baseline.
- Add support for `**env_options` in the `Jinja2Templates` constructor, allowing full customization of the Jinja2 environment.

### Changes
- Modified `Jinja2Templates.__init__` to accept and use `**env_options`.
- Enabled `autoescape` by default using `select_autoescape()` if not explicitly provided.
- Added test cases in `tests/test_templates.py` to verify both the secure default and the ability to override it.

# Checklist

- [x] Understood that this PR may be closed in case there was no previous discussion. (This doesn't apply to typos!)
- [x] Added a test for each change that was introduced, while I tried as much as possible to make a single atomic change.
- [x] Updated the documentation accordingly.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

[user], noticed #3148 covers the autoescape change. Moving forward with that is cool, though I'm happy to sync this PR with the new docs refactor if keeping the `**env_options` support makes sense.

Missing implementation for `**env_options` was something I spotted while checking the docs, so I've included it here.

### Comment 2 ([user]):

> **env_options support makes sense.

We just dropped that.

### Comment 3 ([user]):

[user] got it. Since #3148 handles the autoescape and env_options is out, I'll close this. Thanks!

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
