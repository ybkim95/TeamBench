# GH227_core_162439: fix(snapcast): do not crash when stream is not found — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/home-assistant/core/issues/157636
- Repo: https://github.com/home-assistant/core

## Issue Description

### The problem

The snapcast integration is crashing as soon as I pause the music in music assistant.
Snapcast Version: [Snapcast v0.34.0](https://github.com/badaix/snapcast/releases/tag/v0.34.0)

Steps to reproduce:
 1. connect HA to snapcast server
 2. connect MA to snapcast server
 3. start to play music to a group via MA
 4. stop music via MA
 5. look in to HA logs / see Unavailable snapcast entities 

It looks like that `music assistant` is fast in removing its own stream resulting in a not found stream with missing error handling in the snapcast integration.

may need some more error handling here for STREAM_STATUS.get:

https://github.com/home-assistant/core/blob/060ad35ddc7e90095d0a12d20c351efee02fc913/homeassistant/components/snapcast/media_player.py#L383

https://github.com/home-assistant/core/blob/060ad35ddc7e90095d0a12d20c351efee02fc913/homeassistant/components/snapcast/media_player.py#L475

### What version of Home Assistant Core has the issue?

2025.11.3

### What was the last working version of Home Assistant Core?

_No response_

### What type of installation are you running?

Home Assistant Container

### Integration causing the issue

snapcast

### Link to integration documentation on our website

https://www.home-assistant.io/integrations/snapcast/

### Diagnostics information

_No response_

### Example YAML snippet

```yaml

```

### Anything in the logs that might be useful for us?

```txt
2025-12-01 16:15:03.663 ERROR (MainThread) [homeassistant] Error doing job: Fatal error: protocol.data_received() call failed. (None)
Traceback (most recent call last):
  File "/usr/local/lib/python3.13/asyncio/selector_events.py", line 1019, in _read_ready__data_received
    self._protocol.data_received(data)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^
  File "/usr/local/lib/python3.13/site-packages/snapcast/control/protocol.py", line 54, in data_received
    self.handle_data(item)
    ~~~~~~~~~~~~~~~~^^^^^^
  File "/usr/local/lib/python3.13/site-packages/snapcast/control/protocol.py", line 61, in handle_data
    self.handle_notification(data)
    ~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^
  File "/usr/local/lib/python3.13/site-packages/snapcast/control/protocol.py", line 73, in handle_notification
    self._callbacks.get(data.get('method'))(data.get('params'))
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.13/site-packages/snapcast/control/server.py", line 357, in _on_server_update
    self._on_update_callback_func()
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/usr/src/homeassistant/homeassistant/components/snapcast/coordinator.py", line 48, in _on_update
    self.async_update_listeners()
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/usr/src/homeassistant/homeassistant/helpers/update_coordinator.py", line 190, in async_update_listeners
    update_callback()
    ~~~~~~~~~~~~~~~^^
  File "/usr/src/homeassistant/homeassistant/helpers/update_coordinator.py", line 582, in _handle_coordinator_update
    self.async_write_ha_state()
    ~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/usr/src/homeassistant/homeassistant/helpers/entity.py", line 1026, in async_write_ha_state
    self._async_write_ha_state()
    ~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/usr/src/homeassistant/homeassistant/helpers/entity.py", line 1151, in _async_write_ha_state
    self.__async_calculate_state()
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/usr/src/homeassistant/homeassistant/helpers/entity.py", line 1088, in __async_calculate_state
    state = self._stringify_state(available)
  File "/usr/src/homeassistant/homeassistant/helpers/entity.py", line 1032, in _stringify_state
    if (state := self.state) is None:
                 ^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/snapcast/media_player.py", line 383, in state
    return STREAM_STATUS.get(self._device.stream_status)
                             ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.13/site-packages/snapcast/control/group.py", line 54, in stream_status
    return self._server.stream(self.stream).status
           ~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "/usr/local/lib/python3.13/site-packages/snapcast/control/server.py", line 272, in stream
    return self._streams[stream_identifier]
           ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^
KeyError: 'Music Assistant - radio'
2025-12-01 16:15:03.679 ERROR (MainThread) [homeassistant.components.snapcast.coordinator] Error requesting snapcast.audio:1705 data: 'Music Assistant - radio'
2025-12-01 16:15:03.703 ERROR (MainThread) [homeassistant] Error doing job: Exception in callback _SelectorSocketTransport._call_connection_lost() (None)
Traceback (most recent call last):
  File "/usr/local/lib/python3.13/asyncio/events.py", line 89, in _run
    self._context.run(self._callback, *self._args)
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.13/asyncio/selector_events.py", line 1185, in _call_connection_lost
    super()._call_connection_lost(exc)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^
  File "/usr/local/lib/python3.13/asyncio/selector_events.py", line 903, in _call_connection_lost
    self._protocol.connection_lost(exc)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^
  File "/usr/local/lib/python3.13/site-packages/snapcast/control/protocol.py", line 40, in connection_lost
    self._callbacks.get(SERVER_ONDISCONNECT)(exc)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^
  File "/usr/local/lib/python3.13/site-packages/snapcast/control/server.py", line 347, in _on_server_disconnect
    self._on_disconnect_callback_func(exception)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/snapcast/coordinator.py", line 57, in _on_disconnect
    self.async_set_update_error(ex)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^
  File "/usr/src/homeassistant/homeassistant/helpers/update_coordinator.py", line 520, in async_set_update_error
    self.async_update_listeners()
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/usr/src/homeassistant/homeassistant/helpers/update_coordinator.py", line 190, in async_update_listeners
    update_callback()
    ~~~~~~~~~~~~~~~^^
  File "/usr/src/homeassistant/homeassistant/helpers/update_coordinator.py", line 582, in _handle_coordinator_update
    self.async_write_ha_state()
    ~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/usr/src/homeassistant/homeassistant/helpers/entity.py", line 1026, in async_write_ha_state
    self._async_write_ha_state()
    ~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/usr/src/homeassistant/homeassistant/helpers/entity.py", line 1151, in _async_write_ha_state
    self.__async_calculate_state()
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/usr/src/homeassistant/homeassistant/helpers/entity.py", line 1110, in __async_calculate_state
    if (entity_picture := self.entity_picture) is not None:
                          ^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/media_player/__init__.py", line 1086, in entity_picture
    if self.state == MediaPlayerState.OFF:
       ^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/snapcast/media_player.py", line 383, in state
    return STREAM_STATUS.get(self._device.stream_status)
                             ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.13/site-packages/snapcast/control/group.py", line 54, in stream_status
    return self._server.stream(self.stream).status
           ~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "/usr/local/lib/python3.13/site-packages/snapcast/control/server.py", line 272, in stream
    return self._streams[stream_identifier]
           ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^
KeyError: 'Music Assistant - radio'
```

### Additional information

_No response_

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hey there [user], mind taking a look at this issue as it has been labeled with an integration (`snapcast`) you are listed as a [code owner](https://github.com/home-assistant/core/blob/dev/CODEOWNERS#L1502) for? Thanks!

<details>
<summary>Code owner commands</summary>

Code owners of `snapcast` can trigger bot actions by commenting:

- `@home-assistant close` Closes the issue.
- `@home-assistant rename Awesome new title` Renames the issue.
- `@home-assistant reopen` Reopen the issue.
- `@home-assistant unassign snapcast` Removes the current integration label and assignees on the issue, add the integration domain after the command.
- `@home-assistant add-label needs-more-information` Add a label (needs-more-information, problem in dependency, problem in custom component) to the issue.
- `@home-assistant remove-label needs-more-information` Remove a label (needs-more-information, problem in dependency, problem in custom component) on the issue.

</details>

<sub><sup>(message by CodeOwnersMention)</sup></sub>

---

[snapcast documentation](https://www.home-assistant.io/integrations/snapcast)
[snapcast source](https://github.com/home-assistant/core/tree/dev/homeassistant/components/snapcast)
<sub><sup>(message by IssueLinks)</sup></sub>

### Comment 2 ([user]):

Any more info needed?

## PR Review Comments

**[user]** on `homeassistant/components/snapcast/media_player.py`:

Add test coverage for the new `KeyError` handling when the current stream disappears (e.g., `Snapgroup.stream_status`/`server.stream(...)` raising `KeyError`). Without a test that simulates a missing stream, this regression fix could be accidentally removed later and reintroduce the crash.

**[user]** on `homeassistant/components/snapcast/media_player.py`:

Grammar: "does not exists" should be "does not exist".

**[user]** on `homeassistant/components/snapcast/media_player.py`:

Grammar: "does not exists" should be "does not exist".
```suggestion
        ):  # the stream function raises KeyError if the stream does not exist
```

**[user]** on `homeassistant/components/snapcast/media_player.py`:

This isn't related to the crash right?

**[user]** on `homeassistant/components/snapcast/media_player.py`:

This can't raise a keyerror right? Because if the stream status is not in the list it would just return `None`

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
