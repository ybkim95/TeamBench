# GH539_redis-py_3969: Added pubsub metrics export — Full Specification (Planner Only)

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

**[user]** on `redis/asyncio/client.py`:

`handle_message` hard-codes `["message", "pmessage"]` even though `self.PUBLISH_MESSAGE_TYPES` already defines the publish message types. Reusing the existing constant avoids duplicated knowledge and reduces the chance of metrics getting out of sync if message type sets change later.

**[user]** on `tests/test_asyncio/test_pubsub.py`:

Since `record_pubsub_message` is patched with `AsyncMock` and the production code `await`s it, `assert_called_once()` doesn’t verify that it was actually awaited. Using `assert_awaited_once()` / `assert_awaited_once_with(...)` would make the test stricter and prevent false positives if the implementation changes to call it without awaiting.

**[user]** on `tests/test_asyncio/test_pubsub.py`:

Same as above: `record_pubsub_message` is an `AsyncMock` that should be awaited by `handle_message`, but the test only asserts it was called. Prefer `assert_awaited_once()` / `assert_awaited_once_with(...)` to ensure the coroutine was awaited and the expected kwargs were passed.

**[user]** on `tests/test_asyncio/test_pubsub.py`:

`mock_pubsub` being a plain `MagicMock()` can mask missing/renamed attributes if `handle_message()` starts using additional `PubSub` state. Consider using a small stub object or `MagicMock(spec=PubSub)` so the test fails on unexpected attribute access.

**Severity: low**

[![Fix This in Augment](https://public.augment-assets.com/code-review/fix-in-augment.svg "Fix This in Augment")](https://app.augmentcode.com/open-chat?mode=agent&prompt=%23%23%20Review%20Comment%20Fix%20Request%0A%0APlease%20help%20me%20address%20this%20specific%20review%20comment%20from%20PR%3A%20https%3A%2F%2Fgithub.com%2Fredis%2Fredis-py%2Fpull%2F3969%0A%0A%23%23%23%20Review%20Comment%20Details%3A%0A-%20%2A%2AFile%20Location%2A%2A%3A%20tests%2Ftest_asyncio%2Ftest_pubsub.py%0A-%20%2A%2ALocation%2A%2A%3A%20Line%201135%0A-%20%2A%2AComment%2A%2A%3A%20%22%60mock_pubsub%60%20being%20a%20plain%20%60MagicMock%28%29%60%20can%20mask%20missing%2Frenamed%20attributes%20if%20%60handle_message%28%29%60%20starts%20using%20additional%20%60PubSub%60%20state.%20Consider%20using%20a%20small%20stub%20object%20or%20%60MagicMock%28spec%3DPubSub%29%60%20so%20the%20test%20fails%20on%20unexpected%20attribute%20access.%22%0A%0A%23%23%23%20Steps%20to%20Follow%3A%0A%0A1.%20%2A%2ADetermine%20Github%20Branch%2A%2A%3A%20Use%20%60git%20branch%20--show-current%60%20to%20get%20the%20current%20branch%2C%20then%20fetch%20PR%20details%20from%20the%20Github%20API%20to%20determine%20the%20correct%20branch%20for%20this%20PR%0A2.%20%2A%2ABranch%20Verification%2A%2A%3A%20Ask%20the%20user%20to%20switch%20branches%20if%20they%20are%20not%20on%20the%20correct%20branch%0A3.%20%2A%2AAddress%20Comment%2A%2A%3A%20Help%20me%20fix%20the%20issue%20described%20in%20the%20review%20comment%20above%0A%0APlease%20start%20by%20checking%20the%20current%20branch%20and%20PR%20details.)

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
