# GH540_redis-py_3968: Added connection advanced metrics export — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/redis/redis-py

## PR Description

### Description of change

_Please provide a description of the change here._

### Pull Request check-list

_Please make sure to review and check all of these items:_

- [ ] Do tests and lints pass with this change?
- [ ] Do the CI tests pass with this change (enable it first in your forked repo and wait for the github action build to finish)?
- [ ] Is the new or changed code fully tested?
- [ ] Is a documentation update included (if this change modifies existing APIs, or introduces new ones)?
- [ ] Is there an example added to the examples folder (if applicable)?

_NOTE: these things are not required to open a PR and can be done
afterwards / while the PR is open._

## PR Review Comments

**[user]** on `tests/test_asyncio/test_connection_pool.py`:

The imports from unittest.mock are split across two lines (line 4 and line 15). These should be combined into a single import statement for consistency and cleaner code organization.

**[user]** on `redis/asyncio/connection.py`:

Now that `disconnect()` always records `CloseReason.APPLICATION_CLOSE` when `error` is falsy, internal error paths that call `disconnect(nowait=True)` without passing the exception (e.g., read/write timeouts) will be reported as an application-initiated close. Is it expected that those call sites always supply `error` to avoid skewing the new close-reason metric?

**Severity: medium**

[![Fix This in Augment](https://public.augment-assets.com/code-review/fix-in-augment.svg "Fix This in Augment")](https://app.augmentcode.com/open-chat?mode=agent&prompt=%23%23%20Review%20Comment%20Fix%20Request%0A%0APlease%20help%20me%20address%20this%20specific%20review%20comment%20from%20PR%3A%20https%3A%2F%2Fgithub.com%2Fredis%2Fredis-py%2Fpull%2F3968%0A%0A%23%23%23%20Review%20Comment%20Details%3A%0A-%20%2A%2AFile%20Location%2A%2A%3A%20redis%2Fasyncio%2Fconnection.py%0A-%20%2A%2ALocation%2A%2A%3A%20Line%20620%0A-%20%2A%2AComment%2A%2A%3A%20%22Now%20that%20%60disconnect%28%29%60%20always%20records%20%60CloseReason.APPLICATION_CLOSE%60%20when%20%60error%60%20is%20falsy%2C%20internal%20error%20paths%20that%20call%20%60disconnect%28nowait%3DTrue%29%60%20without%20passing%20the%20exception%20%28e.g.%2C%20read%2Fwrite%20timeouts%29%20will%20be%20reported%20as%20an%20application-initiated%20close.%20Is%20it%20expected%20that%20those%20call%20sites%20always%20supply%20%60error%60%20to%20avoid%20skewing%20the%20new%20close-reason%20metric%3F%22%0A%0A%23%23%23%20Steps%20to%20Follow%3A%0A%0A1.%20%2A%2ADetermine%20Github%20Branch%2A%2A%3A%20Use%20%60git%20branch%20--show-current%60%20to%20get%20the%20current%20branch%2C%20then%20fetch%20PR%20details%20from%20the%20Github%20API%20to%20determine%20the%20correct%20branch%20for%20this%20PR%0A2.%20%2A%2ABranch%20Verification%2A%2A%3A%20Ask%20the%20user%20to%20switch%20branches%20if%20they%20are%20not%20on%20the%20correct%20branch%0A3.%20%2A%2AAddress%20Comment%2A%2A%3A%20Help%20me%20fix%20the%20issue%20described%20in%20the%20review%20comment%20above%0A%0APlease%20start%20by%20checking%20the%20current%20branch%20and%20PR%20details.)

<h2></h2>

<sub>🤖 Was this useful? React with 👍 or 👎, or 🚀 if it prevented an incident/outage.</sub>

**[user]** on `tests/test_asyncio/test_connection_pool.py`:

These new tests create errors via the built-in `ConnectionError`, whereas the asyncio client typically raises `redis.exceptions.ConnectionError`/`TimeoutError` subclasses. Using the redis exception types here would better match production behavior (including any extra attributes used by observability).

**Severity: low**

[![Fix This in Augment](https://public.augment-assets.com/code-review/fix-in-augment.svg "Fix This in Augment")](https://app.augmentcode.com/open-chat?mode=agent&prompt=%23%23%20Review%20Comment%20Fix%20Request%0A%0APlease%20help%20me%20address%20this%20specific%20review%20comment%20from%20PR%3A%20https%3A%2F%2Fgithub.com%2Fredis%2Fredis-py%2Fpull%2F3968%0A%0A%23%23%23%20Review%20Comment%20Details%3A%0A-%20%2A%2AFile%20Location%2A%2A%3A%20tests%2Ftest_asyncio%2Ftest_connection_pool.py%0A-%20%2A%2ALocation%2A%2A%3A%20Line%201149%0A-%20%2A%2AComment%2A%2A%3A%20%22These%20new%20tests%20create%20errors%20via%20the%20built-in%20%60ConnectionError%60%2C%20whereas%20the%20asyncio%20client%20typically%20raises%20%60redis.exceptions.ConnectionError%60%2F%60TimeoutError%60%20subclasses.%20Using%20the%20redis%20exception%20types%20here%20would%20better%20match%20production%20behavior%20%28including%20any%20extra%20attributes%20used%20by%20observability%29.%22%0A%0A%23%23%23%20Steps%20to%20Follow%3A%0A%0A1.%20%2A%2ADetermine%20Github%20Branch%2A%2A%3A%20Use%20%60git%20branch%20--show-current%60%20to%20get%20the%20current%20branch%2C%20then%20fetch%20PR%20details%20from%20the%20Github%20API%20to%20determine%20the%20correct%20branch%20for%20this%20PR%0A2.%20%2A%2ABranch%20Verification%2A%2A%3A%20Ask%20the%20user%20to%20switch%20branches%20if%20they%20are%20not%20on%20the%20correct%20branch%0A3.%20%2A%2AAddress%20Comment%2A%2A%3A%20Help%20me%20fix%20the%20issue%20described%20in%20the%20review%20comment%20above%0A%0APlease%20start%20by%20checking%20the%20current%20branch%20and%20PR%20details.)

<h2></h2>

<sub>🤖 Was this useful? React with 👍 or 👎, or 🚀 if it prevented an incident/outage.</sub>

**[user]** on `redis/asyncio/connection.py`:

Yes

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
