# GH436_sqlalchemy_13063: docs: fixups in PostgreSQL dialect rST docstrings — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/sqlalchemy/sqlalchemy

## PR Description

### Description
A few nitpicky edits/fixups in the reStructuredText docstrings for the PostgreSQL dialect; all of these are related to feature versioning.

:warning: Removing the forward-reference from v1.4 to v2.0.41 about the addition of `.UniqueConstraint` might be unnecessary or controversial.

### Checklist
This pull request is:

- [x] A documentation / typographical / small typing error fix
	- Good to go, no issue or tests are needed
- [ ] A short code fix
	- please include the issue number, and create an issue if none exists, which
	  must include a complete example of the issue.  one line code fixes without an
	  issue and demonstration will not be accepted.
	- Please include: `Fixes: #<issue number>` in the commit message
	- please include tests.   one line code fixes without tests will not be accepted.
- [ ] A new feature implementation
	- please include the issue number, and create an issue if none exists, which must
	  include a complete example of how the feature would look.
	- Please include: `Fixes: #<issue number>` in the commit message
	- please include tests.

**Have a nice day!** (you too)

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
