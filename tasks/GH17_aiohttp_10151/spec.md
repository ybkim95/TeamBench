# GH17_aiohttp_10151: Fix infinite callback loop when time is not moving forward — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/aio-libs/aiohttp/issues/123
- Repo: https://github.com/aio-libs/aiohttp

## Issue Description

Hi,

I added final_url to HttpResponse so one can know the final url after redirect that the response came from.

Hope you'll merge it..

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

I'll take a look a bit later, but proposed change needs some test cases.

### Comment 2 ([user]):

right now ClientResponse.url reflects latest url's path, but it should be save to replace self.path with self.url in ClientRequest.send() method.

### Comment 3 ([user]):

ok i'll change it

### Comment 4 ([user]):

This thread has been automatically locked since there has not been
any recent activity after it was closed. Please open a [new issue] for
related bugs.

If you feel like there's important points made in this discussion,
please include those exceprts into that [new issue].

[new issue]: https://github.com/aio-libs/aiohttp/issues/new

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
