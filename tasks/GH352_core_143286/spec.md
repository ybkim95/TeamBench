# GH352_core_143286: Fix: surepetcare sensor error — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/home-assistant/core/issues/143149
- Repo: https://github.com/home-assistant/core

## Issue Description

### The problem

UPDATE:
I've downgraded back to OS 15.1 and the issue still exists. Maybe the API changed?

Hello,
I just noticed that the Sure Petcare integration does not work any more after updating the operating system to 15.2

Core 2025.4.2
Supervisor 2025.04.0
Operating System 15.2
Frontend 20250411.0

Everytime I want to perform an action, an error is thrown in the protocol.

I already tried to resetup the integration, but with no success.

### What version of Home Assistant Core has the issue?

core-2025.4.2

### What was the last working version of Home Assistant Core?

core-2025.4.2

### What type of installation are you running?

Home Assistant OS

### Integration causing the issue

Sure Petcare

### Link to integration documentation on our website

https://www.home-assistant.io/integrations/surepetcare/

### Diagnostics information

_No response_

### Example YAML snippet

```yaml

```

### Anything in the logs that might be useful for us?

```txt
Logger: homeassistant.helpers.entity
Quelle: helpers/entity.py:960
Erstmals aufgetreten: 09:38:21 (3 Vorkommnisse)
Zuletzt protokolliert: 09:49:22

Update for binary_sensor.tacoma fails
Traceback (most recent call last):
  File "/usr/src/homeassistant/homeassistant/helpers/entity.py", line 960, in async_update_ha_state
    await self.async_device_update()
  File "/usr/src/homeassistant/homeassistant/helpers/entity.py", line 1318, in async_device_update
    await self.async_update()
  File "/usr/src/homeassistant/homeassistant/helpers/update_coordinator.py", line 601, in async_update
    await self.coordinator.async_request_refresh()
  File "/usr/src/homeassistant/homeassistant/helpers/update_coordinator.py", line 275, in async_request_refresh
    await self._debounced_refresh.async_call()
  File "/usr/src/homeassistant/homeassistant/helpers/debounce.py", line 114, in async_call
    await task
  File "/usr/src/homeassistant/homeassistant/helpers/update_coordinator.py", line 356, in async_refresh
    await self._async_refresh(log_failures=True)
  File "/usr/src/homeassistant/homeassistant/helpers/update_coordinator.py", line 479, in _async_refresh
    self.async_update_listeners()
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/usr/src/homeassistant/homeassistant/helpers/update_coordinator.py", line 178, in async_update_listeners
    update_callback()
    ~~~~~~~~~~~~~~~^^
  File "/usr/src/homeassistant/homeassistant/components/surepetcare/entity.py", line 55, in _handle_coordinator_update
    self._update_attr(self.coordinator.data[self._id])
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/surepetcare/binary_sensor.py", line 141, in _update_attr
    "hub_rssi": f"{state['signal']['hub_rssi']:.2f}",
                   ~~~~~~~~~~~~~~~^^^^^^^^^^^^
KeyError: 'hub_rssi'
```

### Additional information

_No response_

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hey there [user], [user], mind taking a look at this issue as it has been labeled with an integration (`surepetcare`) you are listed as a [code owner](https://github.com/home-assistant/core/blob/dev/CODEOWNERS#L1487) for? Thanks!

<details>
<summary>Code owner commands</summary>

Code owners of `surepetcare` can trigger bot actions by commenting:

- `@home-assistant close` Closes the issue.
- `@home-assistant rename Awesome new title` Renames the issue.
- `@home-assistant reopen` Reopen the issue.
- `@home-assistant unassign surepetcare` Removes the current integration label and assignees on the issue, add the integration domain after the command.
- `@home-assistant add-label needs-more-information` Add a label (needs-more-information, problem in dependency, problem in custom component) to the issue.
- `@home-assistant remove-label needs-more-information` Remove a label (needs-more-information, problem in dependency, problem in custom component) on the issue.

</details>

<sub><sup>(message by CodeOwnersMention)</sup></sub>

---

[surepetcare documentation](https://www.home-assistant.io/integrations/surepetcare)
[surepetcare source](https://github.com/home-assistant/core/tree/dev/homeassistant/components/surepetcare)
<sub><sup>(message by IssueLinks)</sup></sub>

### Comment 2 ([user]):

Additional info:
I tried to resetup the integration again and not - after entering the credentials - only the flap is found. Hub and cat are not found.

### Comment 3 ([user]):

Hi guys,
Have the same problem.
Log entries from Home Assistant:

Logger: homeassistant.components.binary_sensor
Quelle: helpers/entity_platform.py:382
Integration: Binärsensor (Dokumentation, Probleme)
Erstmals aufgetreten: 16. April 2025 um 22:41:31 (9 Vorkommnisse)
Zuletzt protokolliert: 12:12:30

Error while setting up surepetcare platform for binary_sensor: 'hub_rssi'
Traceback (most recent call last):
  File "/usr/src/homeassistant/homeassistant/helpers/entity_platform.py", line 382, in _async_setup_platform
    await asyncio.shield(awaitable)
  File "/usr/src/homeassistant/homeassistant/components/surepetcare/binary_sensor.py", line 44, in async_setup_entry
    entities.append(DeviceConnectivity(surepy_entity.id, coordinator))
                    ~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/surepetcare/binary_sensor.py", line 130, in __init__
    super().__init__(surepetcare_id, coordinator)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/surepetcare/binary_sensor.py", line 62, in __init__
    super().__init__(surepetcare_id, coordinator)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/surepetcare/entity.py", line 45, in __init__
    self._update_attr(coordinator.data[surepetcare_id])
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/surepetcare/binary_sensor.py", line 141, in _update_attr
    "hub_rssi": f"{state['signal']['hub_rssi']:.2f}",
                   ~~~~~~~~~~~~~~~^^^^^^^^^^^^
KeyError: 'hub_rssi'

or:

Logger: homeassistant.components.surepetcare.coordinator
Quelle: helpers/debounce.py:137
Integration: Sure Petcare (Dokumentation, Probleme)
Erstmals aufgetreten: 16. April 2025 um 22:22:22 (1958 Vorkommnisse)
Zuletzt protokolliert: 11:09:41

Unexpected exception from <bound method DataUpdateCoordinator.async_refresh of <homeassistant.components.surepetcare.coordinator.SurePetcareDataCoordinator object at 0x7ff3f07d0590>>
Unexpected exception from <bound method DataUpdateCoordinator.async_refresh of <homeassistant.components.surepetcare.coordinator.SurePetcareDataCoordinator object at 0x7ff3d584f950>>
Unexpected exception from <bound method DataUpdateCoordinator.async_refresh of <homeassistant.components.surepetcare.coordinator.SurePetcareDataCoordinator object at 0x7ff3e0eb3350>>
Traceback (most recent call last):
  File "/usr/src/homeassistant/homeassistant/helpers/debounce.py", line 137, in _handle_timer_finish
    await task
  File "/usr/src/homeassistant/homeassistant/helpers/update_coordinator.py", line 356, in async_refresh
    await self._async_refresh(log_failures=True)
  File "/usr/src/homeassistant/homeassistant/helpers/update_coordinator.py", line 479, in _async_refresh
    self.async_update_listeners()
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/usr/src/homeassistant/homeassistant/helpers/update_coordinator.py", line 178, in async_update_listeners
    update_callback()
    ~~~~~~~~~~~~~~~^^
  File "/usr/src/homeassistant/homeassistant/components/surepetcare/entity.py", line 55, in _handle_coordinator_update
    self._update_attr(self.coordinator.data[self._id])
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/surepetcare/binary_sensor.py", line 141, in _update_attr
    "hub_rssi": f"{state['signal']['hub_rssi']:.2f}",
                   ~~~~~~~~~~~~~~~^^^^^^^^^^^^
KeyError: 'hub_rssi'

Thank you in advance!

### Comment 4 ([user]):

I'm facing the same issue.
Following the upgrade, the HUB & Cats entities disappeared from the integration. I re-initialised the integration & recreate it but no cats nor HUB found

### Comment 5 ([user]):

Also having the same issue, Boris my cat is no longer a thing in Home assistant! :-(

### Comment 6 ([user]):

I have the same problem. Integration is broken. My automation for the cat door no longer works (my cats are not so happy ;))

debug log without relevant credentials:

```
2025-04-17 08:30:22.880 DEBUG (MainThread) [surepy.client] initialization completed | vars(): {'self': <surepy.client.SureAPIClient object at 0x7f4da0cdd0>, 'email': 'vvv', 'password': 'vvvv', 'auth_token': 'vvv', 'api_timeout': 60, 'session': <aiohttp.client.ClientSession object at 0x7f99dc7620>, 'surepy_version': '0.9.0', 'token': None}
2025-04-17 08:30:22.880 DEBUG (MainThread) [surepy] initialization completed | vars(): {'self': <surepy.Surepy object at 0x7f4da0d910>, 'email': 'vvv', 'password': 'vvvn', 'auth_token': 'vvv', 'api_timeout': 60, 'session': <aiohttp.client.ClientSession object at 0x7f99dc7620>}
2025-04-17 08:30:23.691 DEBUG (MainThread) [surepy.client] 🐾 [38;2;0;255;0m·[0m GET app.api.surehub.io/api/me/start | 6
2025-04-17 08:30:23.915 INFO (MainThread) [surepy.client] 🐾 [38;2;255;0;255m·[0m GET app.api.surehub.io/api/report/household/111111: 404 | <ClientResponse(https://app.api.surehub.io/api/report/household/111111) [404 Not Found]>
<CIMultiDictProxy('Date': 'Thu, 17 Apr 2025 06:30:23 GMT', 'Content-Length': '0', 'Connection': 'keep-alive', 'Server': 'nginx', 'Access-Control-Allow-Origin': '*', 'Strict-Transport-Security': 'max-age=31536000; includeSubdomains; preload', 'X-Frame-Options': 'DENY', 'X-Content-Type-Options': 'nosniff', 'X-XSS-Protection': '1; mode=block')>

2025-04-17 08:30:23.915 DEBUG (MainThread) [surepy.client] 🐾 [38;2;0;255;0m·[0m GET app.api.surehub.io/api/report/household/11111 | 0
2025-04-17 08:30:23.915 DEBUG (MainThread) [homeassistant.components.surepetcare.coordinator] Finished fetching surepetcare data in 1.035 seconds (success: True)
2025-04-17 08:30:23.916 ERROR (MainThread) [homeassistant.components.binary_sensor] Error while setting up surepetcare platform for binary_sensor: 'hub_rssi'
Traceback (most recent call last):
  File "/usr/src/homeassistant/homeassistant/helpers/entity_platform.py", line 382, in _async_setup_platform
    await asyncio.shield(awaitable)
  File "/usr/src/homeassistant/homeassistant/components/surepetcare/binary_sensor.py", line 44, in async_setup_entry
    entities.append(DeviceConnectivity(surepy_entity.id, coordinator))
                    ~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/surepetcare/binary_sensor.py", line 130, in __init__
    super().__init__(surepetcare_id, coordinator)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/surepetcare/binary_sensor.py", line 62, in __init__
    super().__init__(surepetcare_id, coordinator)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/surepetcare/entity.py", line 45, in __init__
    self._update_attr(coordinator.data[surepetcare_id])
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/surepetcare/binary_sensor.py", line 141, in _update_attr
    "hub_rssi": f"{state['signal']['hub_rssi']:.2f}",
                   ~~~~~~~~~~~~~~~^^^^^^^^^^^^
KeyError: 'hub_rssi'```

### Comment 7 ([user]):

Might be related: https://fabieu.github.io/sureflap-api/#/Pet 

![Image](https://github.com/user-attachments/assets/b79acb2a-42cb-474b-8e80-3810c820d1c7)

### Comment 8 ([user]):

Explains the 404 then... New API endpoints!

### Comment 9 ([user]):

Same problem for me.
Had same issue as others after removing the integration that only flap and feeders showed up. But after restart everything came back. but still no updates when cats go in and out, and not able to to lock the flap.
hub_rssi error same as everyone.

Error doing job: Task exception was never retrieved (None)
Traceback (most recent call last):
  File "/usr/src/homeassistant/homeassistant/helpers/update_coordinator.py", line 268, in _handle_refresh_interval
    await self._async_refresh(log_failures=True, scheduled=True)
  File "/usr/src/homeassistant/homeassistant/helpers/update_coordinator.py", line 479, in _async_refresh
    self.async_update_listeners()
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/usr/src/homeassistant/homeassistant/helpers/update_coordinator.py", line 178, in async_update_listeners
    update_callback()
    ~~~~~~~~~~~~~~~^^
  File "/usr/src/homeassistant/homeassistant/components/surepetcare/entity.py", line 55, in _handle_coordinator_update
    self._update_attr(self.coordinator.data[self._id])
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/surepetcare/binary_sensor.py", line 141, in _update_attr
    "hub_rssi": f"{state['signal']['hub_rssi']:.2f}",
                   ~~~~~~~~~~~~~~~^^^^^^^^^^^^
KeyError: 'hub_rssi'

### Comment 10 ([user]):

I have the same problem.

## PR Review Comments

**[user]** on `homeassistant/components/surepetcare/binary_sensor.py`:

There should be two blank lines before a class definition.

**[user]** on `homeassistant/components/surepetcare/binary_sensor.py`:

If you get a KeyError above, `state` will not exists?

**[user]** on `homeassistant/components/surepetcare/binary_sensor.py`:

Indeed, but `online` will be `False` so it is never accessed. I could add a dummy dictionary for `state` if that's safer?

**[user]** on `homeassistant/components/surepetcare/binary_sensor.py`:

If the raw data always contains "status" and you're not expecting that to cause the KeyError, you could write it without the try block as:

```
state = surepy_entity.raw_data()["status"]
online = state.get("online", False)
```

I don't think it alters anything about your new logic though. Might just be clearer what your intent is with the try block.

**[user]** on `homeassistant/components/surepetcare/binary_sensor.py`:

I see. I added a suggestion, that I think is cleaner and you do not need the `online` variable

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
