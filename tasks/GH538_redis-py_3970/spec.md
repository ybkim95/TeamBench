# GH538_redis-py_3970: Added streaming lag metric export — Full Specification (Planner Only)

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

**[user]** on `redis/commands/core.py`:

Importing the async recorder inside the function could have performance implications since this function may be called frequently. Consider importing it at the module level similar to the sync version, or use a conditional import at the top of the file to avoid repeated imports on each function call.

**[user]** on `redis/commands/core.py`:

Importing the async recorder inside the function could have performance implications since this function may be called frequently. Consider importing it at the module level similar to the sync version, or use a conditional import at the top of the file to avoid repeated imports on each function call.

**[user]** on `tests/test_asyncio/test_commands.py`:

While async tests have been added for xread and xreadgroup metric export, there are no corresponding sync tests in tests/test_commands.py. Although the sync path is tested indirectly through recorder unit tests, adding explicit sync command-level tests would provide better coverage and confidence that the metric export works correctly for both sync and async clients.

**[user]** on `redis/commands/core.py`:

The asyncio import is unused and should be removed. The inspect module is used for checking coroutines, but asyncio is not directly used in this file.
```suggestion

```

**[user]** on `tests/test_asyncio/test_commands.py`:

`AsyncMock.assert_called_once()` doesn’t verify the mock was actually awaited; if the production code accidentally drops the `await`, these tests would still pass. Consider using `assert_awaited_once()` (and similar) so the tests guarantee the recorder coroutine is awaited.

**Severity: low**

<details open>
<summary>Other Locations</summary>

- `tests/test_asyncio/test_commands.py:5479`
- `tests/test_asyncio/test_commands.py:5508`
</details>

[![Fix This in Augment](https://public.augment-assets.com/code-review/fix-in-augment.svg "Fix This in Augment")](https://app.augmentcode.com/open-chat?mode=agent&prompt=%23%23%20Review%20Comment%20Fix%20Request%0A%0APlease%20help%20me%20address%20this%20specific%20review%20comment%20from%20PR%3A%20https%3A%2F%2Fgithub.com%2Fredis%2Fredis-py%2Fpull%2F3970%0A%0A%23%23%23%20Review%20Comment%20Details%3A%0A-%20%2A%2AFile%20Location%2A%2A%3A%20tests%2Ftest_asyncio%2Ftest_commands.py%0A-%20%2A%2ALocation%2A%2A%3A%20Line%205440%0A-%20%2A%2AComment%2A%2A%3A%20%22%60AsyncMock.assert_called_once%28%29%60%20doesn%E2%80%99t%20verify%20the%20mock%20was%20actually%20awaited%3B%20if%20the%20production%20code%20accidentally%20drops%20the%20%60await%60%2C%20these%20tests%20would%20still%20pass.%20Consider%20using%20%60assert_awaited_once%28%29%60%20%28and%20similar%29%20so%20the%20tests%20guarantee%20the%20recorder%20coroutine%20is%20awaited.%22%0A%0A%23%23%23%20Steps%20to%20Follow%3A%0A%0A1.%20%2A%2ADetermine%20Github%20Branch%2A%2A%3A%20Use%20%60git%20branch%20--show-current%60%20to%20get%20the%20current%20branch%2C%20then%20fetch%20PR%20details%20from%20the%20Github%20API%20to%20determine%20the%20correct%20branch%20for%20this%20PR%0A2.%20%2A%2ABranch%20Verification%2A%2A%3A%20Ask%20the%20user%20to%20switch%20branches%20if%20they%20are%20not%20on%20the%20correct%20branch%0A3.%20%2A%2AAddress%20Comment%2A%2A%3A%20Help%20me%20fix%20the%20issue%20described%20in%20the%20review%20comment%20above%0A%0APlease%20start%20by%20checking%20the%20current%20branch%20and%20PR%20details.)

<h2></h2>

<sub>🤖 Was this useful? React with 👍 or 👎, or 🚀 if it prevented an incident/outage.</sub>

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
