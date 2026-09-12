# GH447_quart_283: Fix program not closing on Ctrl+C in Windows — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/pallets/quart

## PR Description

The _windows_signal_support() loops forever. Using asyncio.gather make that trying to use Ctrl+C to end the program on Windows was just soft-blocking it after closing every other part of the program. The only choice was then to close the terminal window.

_windows_signal_support() was introduced on commit (withheld: the upstream fix is not part of the task) to fix an issue on python 3.7. The function was removed since Quart doesn't support 3.7 since 0.19.0.

Closes: https://github.com/pallets/quart/issues/282

Checklist:

- [ ] Add tests that demonstrate the correct behavior of the change. Tests should fail without the change.
- Add or update relevant docs, in the docs folder and in code : No change in docs
- [ ] Add an entry in `CHANGES.rst` summarizing the change and linking to the issue.
- [ ] Add `.. versionchanged::` entries in any relevant code docs.
- [x] Run `pre-commit` hooks and fix any issues.
- Run `pytest` and `tox`, no tests failed : No test failed on tox, get an error with pytest on Windows

Co-authored-by: Julien Castiaux <[email redacted]>

## PR Review Comments

**[user]** on `src/quart/app.py`:

Why this change?

**[user]** on `src/quart/app.py`:

I made a commit just for this, it was because flake8 was failing (on Windows at least), so I just couldn't commit otherwise :

flake8...................................................................Failed
- hook id: flake8
- exit code: 1

src/quart/app.py:775:13: B028 No explicit stacklevel argument found. The warn method from the warnings module uses a stacklevel of 1 by default. This will only show a stack trace for the line on which the warn method is called. It is therefore recommended to use a stacklevel of 2 or greater to provide more information to the user.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
