# GH325_core_157208: Fix elkm1 connection cleanup on setup failure — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/home-assistant/core/issues/156892
- Repo: https://github.com/home-assistant/core

## Issue Description

### The problem

My alarm and the device connected stopped working in HA and showed Unavailable. On the integrations page it showed as Initializing and never changed (multiple days). I tried choosing to reconfigure it, entered my Username and Password, confirmed the IP address, and selected TLS1.2 since my ELK network module is on the newest firmware. It says it successfully connected, but the integration page still shows Initializing. The log shows the following:

```
Logger: elkm1_lib.connection
Source: components/elkm1/config_flow.py:95
First occurred: 9:33:46 AM (1 occurrence)
Last logged: 9:33:46 AM

ElkM1 at elksv1_2://192.168.1.50 disconnecting
```

I removed the integration, rebooted the machine, and tried to re-install the integration, but it stays on initialization and I get the above error followed by several others.

```
Logger: homeassistant.config_entries
Source: config_entries.py:761
First occurred: 9:35:44 AM (1 occurrence)
Last logged: 9:35:44 AM

Error setting up entry ElkM1 badbad for elkm1
Traceback (most recent call last):
  File "/usr/src/homeassistant/homeassistant/config_entries.py", line 761, in __async_setup_with_context
    result = await component.async_setup_entry(hass, self)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/elkm1/__init__.py", line 282, in async_setup_entry
    if not await async_wait_for_elk_to_sync(elk, LOGIN_TIMEOUT, SYNC_TIMEOUT):
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/elkm1/__init__.py", line 361, in async_wait_for_elk_to_sync
    await event.wait()
  File "/usr/local/lib/python3.13/asyncio/locks.py", line 213, in wait
    await fut
asyncio.exceptions.CancelledError
```

and 

```
Logger: asyncio
Source: runner.py:289
First occurred: 9:39:09 AM (3 occurrences)
Last logged: 9:39:19 AM

SSL connection is closed
```

and 

```
> Logger: elkm1_lib.connection
> Source: runner.py:289
> First occurred: 9:35:54 AM (3 occurrences)
> Last logged: 9:40:14 AM
> 
> ElkM1 at elksv1_2://192.168.1.50 disconnecting (heartbeat timeout)
```

### What version of Home Assistant Core has the issue?

2025.11.2

### What was the last working version of Home Assistant Core?

2025.10.x

### What type of installation are you running?

Home Assistant OS

### Integration causing the issue

ElkM1

### Link to integration documentation on our website

https://www.home-assistant.io/integrations/elkm1

### Diagnostics information

_No response_

### Example YAML snippet

```yaml

```

### Anything in the logs that might be useful for us?

```txt
Logger: elkm1_lib.connection
Source: components/elkm1/config_flow.py:95
First occurred: 9:33:46 AM (1 occurrence)
Last logged: 9:33:46 AM

ElkM1 at elksv1_2://192.168.1.50 disconnecting

Logger: homeassistant.config_entries
Source: config_entries.py:761
First occurred: 9:35:44 AM (1 occurrence)
Last logged: 9:35:44 AM

Error setting up entry ElkM1 badbad for elkm1
Traceback (most recent call last):
  File "/usr/src/homeassistant/homeassistant/config_entries.py", line 761, in __async_setup_with_context
    result = await component.async_setup_entry(hass, self)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/elkm1/__init__.py", line 282, in async_setup_entry
    if not await async_wait_for_elk_to_sync(elk, LOGIN_TIMEOUT, SYNC_TIMEOUT):
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/elkm1/__init__.py", line 361, in async_wait_for_elk_to_sync
    await event.wait()
  File "/usr/local/lib/python3.13/asyncio/locks.py", line 213, in wait
    await fut
asyncio.exceptions.CancelledError

Logger: asyncio
Source: runner.py:289
First occurred: 9:39:09 AM (3 occurrences)
Last logged: 9:39:19 AM

SSL connection is closed

> Logger: elkm1_lib.connection
> Source: runner.py:289
> First occurred: 9:35:54 AM (3 occurrences)
> Last logged: 9:40:14 AM
> 
> ElkM1 at elksv1_2://192.168.1.50 disconnecting (heartbeat timeout)
```

### Additional information

This integration was working fine on the 2025.10.x build, but stopped at one point. I did the reconfigure and it came back online. It happened again a few weeks later and when trying to reconfigure it would error as if the username and password were incorrect. I updated everything to the latest and tried to reconfigure the integration again which succeeded in the reconfigure, but still wouldn't come back online, which is where I am at now.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hey there [user], [user], mind taking a look at this issue as it has been labeled with an integration (`elkm1`) you are listed as a [code owner](https://github.com/home-assistant/core/blob/dev/CODEOWNERS#L427) for? Thanks!

<details>
<summary>Code owner commands</summary>

Code owners of `elkm1` can trigger bot actions by commenting:

- `@home-assistant close` Closes the issue.
- `@home-assistant rename Awesome new title` Renames the issue.
- `@home-assistant reopen` Reopen the issue.
- `@home-assistant unassign elkm1` Removes the current integration label and assignees on the issue, add the integration domain after the command.
- `@home-assistant add-label needs-more-information` Add a label (needs-more-information, problem in dependency, problem in custom component) to the issue.
- `@home-assistant remove-label needs-more-information` Remove a label (needs-more-information, problem in dependency, problem in custom component) on the issue.

</details>

<sub><sup>(message by CodeOwnersMention)</sup></sub>

---

[elkm1 documentation](https://www.home-assistant.io/integrations/elkm1)
[elkm1 source](https://github.com/home-assistant/core/tree/dev/homeassistant/components/elkm1)
<sub><sup>(message by IssueLinks)</sup></sub>

### Comment 2 ([user]):

Is ElkRP connected? If so disconnect it.

### Comment 3 ([user]):

Elk RP is not connected. I also depowered and repowered the Elk Ethernet module to make sure it didn't have a phantom connection that didn't close properly, if that even could happen.

### Comment 4 ([user]):

Try backing off to an older version of HA. 

Nothing has changed in the integration so first avenue of exploration is your setup and system.

### Comment 5 ([user]):

The fact the it was working in .10 and would intermittently fail points strongly to your setup. Things you can try:

Reboot the panel. Reboot, again, the Ethernet. 

Try eliminating network gear. Is the a pretty direct connection to the panel?

Back off a version of HA. Honestly don’t think that is the root cause.

### Comment 6 ([user]):

Nothing has changed in my system for over a year, but I will try a reboot of the panel itself and the Ethernet again when I get home tonight. The HA machine and the Elk are connected at the same network switch, so nothing special there. When I deleted the integration and rebooted, HA auto discovers the Elk as an available integration so they see each other properly. I only ever saw the one hiccup before this one and I can't remember if it was correlated to updating to an incremental version of 10 or if it was just random. I have UPB lighting tied through the Elk and that is how I noticed the issue, my automations stopped working and I have to walk up to a dark house at night. I'll try rebooting both elk panel and Ethernet tonight and update.

### Comment 7 ([user]):

The next thing after the prior list is to provide debug logs.

### Comment 8 ([user]):

I power cycled the panel and the Ethernet, then went back and clicked add on the auto-discovered Elk integration. I entered the username and password followed by TLS1.2. it took a few minutes and said connection successful. Then on the integration page it shows 1 entity for the Elk called sensor.elkm1_elkm1 with status Paused. log shows 

``
Logger: elkm1_lib.connection
Source: runner.py:289
First occurred: 9:35:54 AM (1022 occurrences)
Last logged: 6:38:12 PM

Error connecting to ElkM1 ([Errno 111] Connect call failed ('192.168.1.50', 2601)). Retrying in 1 seconds
Error connecting to ElkM1 ([SSL: TLSV1_ALERT_PROTOCOL_VERSION] tlsv1 alert protocol version (_ssl.c:1032)). Retrying in 60 seconds
ElkM1 at elksv1_2://192.168.1.50 disconnecting (heartbeat timeout)
Error connecting to ElkM1 ([Errno 111] Connect call failed ('192.168.1.50', 2601)). Retrying in 2 seconds
Error connecting to ElkM1 (). Retrying in 60 seconds
``

### Comment 9 ([user]):

Logs please

### Comment 10 ([user]):

[home-assistant_elkm1_2025-11-20T03-19-42.972Z.log](https://github.com/user-attachments/files/23641649/home-assistant_elkm1_2025-11-20T03-19-42.972Z.log)

## PR Review Comments

**[user]** on `homeassistant/components/elkm1/__init__.py`:

Event handlers are registered but never removed. The handlers registered at lines 366-367 (`_login_status` and `_sync_complete`) are added to the elk instance but never cleaned up after `async_wait()` completes.

If the elk instance is reused or if these handlers are called after the waiter completes, this could lead to callbacks being invoked on a completed/garbage-collected `ElkSyncWaiter` instance, potentially causing unexpected behavior or errors.

Recommendation: Remove the handlers in a finally block:

```python
async def async_wait(self) -> bool:
    """Wait for login and sync to complete."""
    self._elk.add_handler("login", self._login_status)
    self._elk.add_handler("sync_complete", self._sync_complete)
    
    try:
        for name, future, timeout in (...):
            # ... existing loop code ...
        return self._login_succeeded
    finally:
        # Clean up handlers
        self._elk.remove_handler("login", self._login_status)
        self._elk.remove_handler("sync_complete", self._sync_complete)
```

Note: This assumes the elk library provides a `remove_handler` method. If not, verify that keeping these handlers attached won't cause issues.
```suggestion
        try:
            for name, future, timeout in (
                ("login", self._login_future, self._login_timeout),
                ("sync_complete", self._sync_future, self._sync_timeout),
            ):
                _LOGGER.debug("Waiting for %s event for %s seconds", name, timeout)
                handle = self._loop.call_later(timeout, self._async_on_timeout, future)
                step_succeeded = False
                try:
                    await future
                    step_succeeded = True
                except TimeoutError:
                    _LOGGER.debug("Timed out waiting for %s event", name)
                    raise
                finally:
                    handle.cancel()
                    if not step_succeeded:
                        self._elk.disconnect()

                _LOGGER.debug("Received %s event", name)

            return self._login_succeeded
        finally:
            self._elk.remove_handler("login", self._login_status)
            self._elk.remove_handler("sync_complete", self._sync_complete)
```

**[user]** on `homeassistant/components/elkm1/__init__.py`:

Missing disconnect when login fails. When the login fails, `_login_status` is called with `succeeded=False`, which sets both futures to done (lines 350-351), causing both loop iterations to complete with `step_succeeded=True`. This means the finally block at line 384 never calls `disconnect()`.

The method returns `False` at line 389, which causes `async_setup_entry` to return `False` at line 283, but the elk connection remains open, leading to the connection leak issue described in the PR.

Flow when login fails:
1. `_login_status(succeeded=False)` sets both futures to done
2. Both loop iterations complete successfully (`step_succeeded=True`)  
3. No disconnect is called (line 385 condition is false)
4. Returns `False` to indicate login failure
5. Elk connection remains open

Recommendation: Call disconnect when returning False, or check `_login_succeeded` in addition to `step_succeeded`:

```python
async def async_wait(self) -> bool:
    """Wait for login and sync to complete."""
    self._elk.add_handler("login", self._login_status)
    self._elk.add_handler("sync_complete", self._sync_complete)
    
    try:
        for name, future, timeout in (...):
            # ... existing loop code ...
        
        # Disconnect if login failed
        if not self._login_succeeded:
            self._elk.disconnect()
            
        return self._login_succeeded
    finally:
        # Clean up handlers
        ...
```
```suggestion

        if not self._login_succeeded:
            self._elk.disconnect()
```

**[user]** on `homeassistant/components/elkm1/__init__.py`:

[nitpick] Potentially incorrect default for `_login_succeeded`. Initializing `_login_succeeded = True` means that if the login callback is never invoked (e.g., due to a bug in the elk library or an unusual connection type), the method would return `True` even though login never actually succeeded.

This could lead to false positives where the system thinks login succeeded when it didn't. A safer default would be `False`, requiring an explicit success callback:

```python
def __init__(self, elk: Elk, login_timeout: int, sync_timeout: int) -> None:
    """Initialize the sync waiter."""
    # ...
    self._login_succeeded = False  # Default to failure, require explicit success
```

With this change, only an actual `_login_status(succeeded=True)` callback would mark login as successful.

However, if there are valid scenarios where no login callback is sent (e.g., certain connection types), the current default might be intentional. Please verify the expected behavior.
```suggestion
        self._login_succeeded = False
```

**[user]** on `homeassistant/components/elkm1/__init__.py`:

68ee46f56d3578c142475e42dc891260b400a5ef

**[user]** on `homeassistant/components/elkm1/__init__.py`:

2ea5d7370e1

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
