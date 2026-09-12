# GH232_core_123085: Fix RecursionError in Husqvarna Automower coordinator — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/home-assistant/core/issues/123008
- Repo: https://github.com/home-assistant/core

## Issue Description

### The problem

### Problem

If there's an error when connecting the websocket the coordinator will retry after sleeping a bit. The retry is done in a recursive fashion in the same task by calling `client_listen` again. If the integration isn't reloaded for a long time the risk increases that eventually the coordinator will hit maximum recursion limit since the same task is recursing more and more on every connection problem even if there are successful connections in between.

### Solution

Instead of recursing in the same task the coordinator should create a new background task for the call to `client_listen` on retry.

### Problem code

https://github.com/home-assistant/core/blob/d16a2fac80b5e3e897442bef786d89e4aa393a94/homeassistant/components/husqvarna_automower/coordinator.py#L62-L87

### What version of Home Assistant Core has the issue?

core-2024.7.3

### What was the last working version of Home Assistant Core?

_No response_

### What type of installation are you running?

Home Assistant Container

### Integration causing the issue

Husqvarna Automower

### Link to integration documentation on our website

https://www.home-assistant.io/integrations/husqvarna_automower/

### Diagnostics information

_No response_

### Example YAML snippet

_No response_

### Anything in the logs that might be useful for us?

```txt
Logger: homeassistant
Source: components/husqvarna_automower/coordinator.py:71
First occurred: July 30, 2024 at 17:55:16 (1 occurrences)
Last logged: July 30, 2024 at 17:55:16

Error doing job: Task exception was never retrieved (None)
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/asyncio/selector_events.py", line 649, in _sock_connect
    sock.connect(address)
BlockingIOError: [Errno 115] Operation in progress

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/usr/src/homeassistant/homeassistant/components/husqvarna_automower/coordinator.py", line 82, in client_listen
    await self.client_listen(
  File "/usr/src/homeassistant/homeassistant/components/husqvarna_automower/coordinator.py", line 82, in client_listen
    await self.client_listen(
  File "/usr/src/homeassistant/homeassistant/components/husqvarna_automower/coordinator.py", line 82, in client_listen
    await self.client_listen(
  [Previous line repeated 972 more times]
  File "/usr/src/homeassistant/homeassistant/components/husqvarna_automower/coordinator.py", line 71, in client_listen
    await automower_client.auth.websocket_connect()
  File "/usr/local/lib/python3.12/site-packages/aioautomower/auth.py", line 191, in websocket_connect
    self.ws = await self._websession.ws_connect(
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/aiohttp/client.py", line 835, in _ws_connect
    resp = await self.request(
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/aiohttp/client.py", line 581, in _request
    conn = await self._connector.connect(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/aiohttp/connector.py", line 544, in connect
    proto = await self._create_connection(req, traces, timeout)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/aiohttp/connector.py", line 944, in _create_connection
    _, proto = await self._create_direct_connection(req, traces, timeout)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/aiohttp/connector.py", line 1226, in _create_direct_connection
    transp, proto = await self._wrap_create_connection(
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/aiohttp/connector.py", line 1025, in _wrap_create_connection
    return await self._loop.create_connection(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/asyncio/base_events.py", line 1104, in create_connection
    sock = await self._connect_sock(
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/asyncio/base_events.py", line 1007, in _connect_sock
    await self.sock_connect(sock, address)
  File "/usr/local/lib/python3.12/asyncio/selector_events.py", line 639, in sock_connect
    self._sock_connect(fut, sock, address)
  File "/usr/local/lib/python3.12/asyncio/selector_events.py", line 656, in _sock_connect
    handle = self._add_writer(
             ^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/asyncio/selector_events.py", line 313, in _add_writer
    self._selector.register(fd, selectors.EVENT_WRITE,
  File "/usr/local/lib/python3.12/selectors.py", line 343, in register
    key = super().register(fileobj, events, data)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/selectors.py", line 242, in register
    key = SelectorKey(fileobj, self._fileobj_lookup(fileobj), events, data)
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/selectors.py", line 229, in _fileobj_lookup
    return _fileobj_to_fd(fileobj)
           ^^^^^^^^^^^^^^^^^^^^^^^
RecursionError: maximum recursion depth exceeded
```

### Additional information

_No response_

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hey there [user], mind taking a look at this issue as it has been labeled with an integration (`husqvarna_automower`) you are listed as a [code owner](https://github.com/home-assistant/core/blob/dev/CODEOWNERS#L639) for? Thanks!

<details>
<summary>Code owner commands</summary>

Code owners of `husqvarna_automower` can trigger bot actions by commenting:

- `@home-assistant close` Closes the issue.
- `@home-assistant rename Awesome new title` Renames the issue.
- `@home-assistant reopen` Reopen the issue.
- `@home-assistant unassign husqvarna_automower` Removes the current integration label and assignees on the issue, add the integration domain after the command.
- `@home-assistant add-label needs-more-information` Add a label (needs-more-information, problem in dependency, problem in custom component) to the issue.
- `@home-assistant remove-label needs-more-information` Remove a label (needs-more-information, problem in dependency, problem in custom component) on the issue.

</details>

<sub><sup>(message by CodeOwnersMention)</sup></sub>

---

[husqvarna_automower documentation](https://www.home-assistant.io/integrations/husqvarna_automower)
[husqvarna_automower source](https://github.com/home-assistant/core/tree/dev/homeassistant/components/husqvarna_automower)
<sub><sup>(message by IssueLinks)</sup></sub>

### Comment 2 ([user]):

There hasn't been any activity on this issue recently. Due to the high number of incoming GitHub notifications, we have to clean some of the old issues, as many of them have already been resolved with the latest updates.
Please make sure to update to the latest Home Assistant version and check if that solves the issue. Let us know if that works for you by adding a comment 👍
This issue has now been marked as stale and will be closed if no further activity occurs. Thank you for your contributions.

### Comment 3 ([user]):

Not fixed yet.

## PR Review Comments

**[user]** on `homeassistant/components/husqvarna_automower/coordinator.py`:

```suggestion
                    self.client_listen(hass, entry, automower_client, reconnect_time),
```

**[user]** on `homeassistant/components/husqvarna_automower/coordinator.py`:

```suggestion
```

**[user]** on `homeassistant/components/husqvarna_automower/coordinator.py`:

We may need to store the `reconnect_time` in an instance variable so we can reset it after a successful connection. Although, we will never retry now if the connection is successful even if the listening call fails. We should probably retry again in that case too. Otherwise the websocket connection will never recover until the config entry is reloaded, if the listening fails.

**[user]** on `tests/components/husqvarna_automower/test_init.py`:

We can't test it like this since we don't want to sleep for any time in tests. We could make the default reconnect time a constant in the integration to make it easier to patch, then patch that to zero with the `new=0` parameter, and then test that we don't hit the recursion limit.

**[user]** on `homeassistant/components/husqvarna_automower/coordinator.py`:

If there's an unexpected exception, ie `Exception`, we want to log that as an error with the stack trace.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
