# GH75_flask_5899: deprecate `should_ignore_error` — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pallets/flask/issues/5816
- Repo: https://github.com/pallets/flask

## Issue Description

This was added in f1918093ac70d589a4d67af0d77140734c06c13d as part of the original code to keep the context around for use in the debugger, tests, etc. It was not part of a PR, and there's no linked issue or explanation on why it was added.

The intention seems to be to allow ignoring certain errors during debugging, so that cleanup is still run immediately. That's not how context preservation works anymore.  It also causes the exception to not be passed to teardown handlers, but there doesn't seem to be any reason to hide that, and handlers can already choose what to do if they're passed an error.

The method is only documented in the API, not in any other pages. There's no test for it. I have a feeling this isn't used. It results in an extra function call every single request, only to always return false. This can be deprecated then removed.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

[user] Would you assign this to me?
I am interested in contributing to this.

### Comment 2 ([user]):

Thanks, however this type of task is not something for new contributors.

### Comment 3 ([user]):

Hi [user],
I’ve been going through the context preservation and teardown logic in Flask and would love to contribute to this issue.
I understand this task was marked as not suitable for new contributors, but I have experience with Python internals and would like to work carefully under your guidance.

I’ve already explored how should_ignore_error interacts with teardown handlers and can open a draft PR showing a safe deprecation path (with tests).

Would you be open to me working on this?

### Comment 4 ([user]):

Hey, I can try and handle this issue. New to contribution, not software development lol. This issue has been open for over a month, I can definitely try and figure this one out. Currently unemployed with nothing better to do, and this one seems like it'll be a doozy and extremely fun for my brain to figure out.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
