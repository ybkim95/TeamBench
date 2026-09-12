# GH218_core_160825: Add back support for coolmaster speeds that don't have a direct HA equivalent — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/home-assistant/core/issues/160818
- Repo: https://github.com/home-assistant/core

## Issue Description

### The problem

It appears that 2026.1 does not like to use vlow as a fan speed as it throws the following error and the entity becomes unavailable

```
Logger: homeassistant.components.automation.daily_thermostat
Source: helpers/script.py:524
integration: Automation (documentation, issues)
First occurred: 11:45:00 AM (1 occurrence)
Last logged: 11:45:00 AM

Daily Thermostat by Noon: Error executing script. Unexpected error for call_service at pos 11: 'vlow'
Traceback (most recent call last):
  File "/usr/src/homeassistant/homeassistant/helpers/script.py", line 524, in _async_step
    await getattr(self, handler)()
  File "/usr/src/homeassistant/homeassistant/helpers/script.py", line 1011, in _async_step_call_service
    response_data = await self._async_run_long_action(
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ...<9 lines>...
    )
    ^
  File "/usr/src/homeassistant/homeassistant/helpers/script.py", line 624, in _async_run_long_action
    return await long_task
           ^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/core.py", line 2819, in async_call
    response_data = await coro
                    ^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/core.py", line 2862, in _execute_service
    return await target(service_call)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/helpers/service.py", line 832, in entity_service_call
    single_response = await _handle_entity_call(
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^
        hass, entity, func, data, call.context
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/usr/src/homeassistant/homeassistant/helpers/service.py", line 904, in _handle_entity_call
    result = await task
             ^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/climate/__init__.py", line 828, in async_service_temperature_set
    await entity.async_set_temperature(**kwargs)
  File "/usr/src/homeassistant/homeassistant/components/coolmaster/climate.py", line 149, in async_set_temperature
    self.async_write_ha_state()
    ~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/usr/src/homeassistant/homeassistant/helpers/entity.py", line 1024, in async_write_ha_state
    self._async_write_ha_state()
    ~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/usr/src/homeassistant/homeassistant/helpers/entity.py", line 1149, in _async_write_ha_state
    self.__async_calculate_state()
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/usr/src/homeassistant/homeassistant/helpers/entity.py", line 1088, in __async_calculate_state
    if state_attributes := self.state_attributes:
                           ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/climate/__init__.py", line 378, in state_attributes
    data[ATTR_FAN_MODE] = self.fan_mode
                          ^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/coolmaster/climate.py", line 127, in fan_mode
    return CM_TO_HA_FAN[self._unit.fan_speed]
           ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
KeyError: 'vlow'
```

### What version of Home Assistant Core has the issue?

2026.1

### What was the last working version of Home Assistant Core?

2025.12

### What type of installation are you running?

Home Assistant OS

### Integration causing the issue

CoolmasterNET

### Link to integration documentation on our website

https://www.home-assistant.io/integrations/coolmaster/

### Diagnostics information

_No response_

### Example YAML snippet

```yaml

```

### Anything in the logs that might be useful for us?

```txt

```

### Additional information

_No response_

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hey there [user], mind taking a look at this issue as it has been labeled with an integration (`coolmaster`) you are listed as a [code owner](https://github.com/home-assistant/core/blob/dev/CODEOWNERS#L317) for? Thanks!

<details>
<summary>Code owner commands</summary>

Code owners of `coolmaster` can trigger bot actions by commenting:

- `@home-assistant close` Closes the issue.
- `@home-assistant rename Awesome new title` Renames the issue.
- `@home-assistant reopen` Reopen the issue.
- `@home-assistant unassign coolmaster` Removes the current integration label and assignees on the issue, add the integration domain after the command.
- `@home-assistant add-label needs-more-information` Add a label (needs-more-information, problem in dependency, problem in custom component) to the issue.
- `@home-assistant remove-label needs-more-information` Remove a label (needs-more-information, problem in dependency, problem in custom component) on the issue.

</details>

<sub><sup>(message by CodeOwnersMention)</sup></sub>

---

[coolmaster documentation](https://www.home-assistant.io/integrations/coolmaster)
[coolmaster source](https://github.com/home-assistant/core/tree/dev/homeassistant/components/coolmaster)
<sub><sup>(message by IssueLinks)</sup></sub>

### Comment 2 ([user]):

[user] looks like this is related to your change

### Comment 3 ([user]):

I'll take a look!

### Comment 4 ([user]):

I created a PR that I think should address this - (withheld: the upstream fix is not part of the task). Unfortunately, I don't have a system that uses either `vlow` or `top`, so I can't test this change directly. i verified that the included pytest tests every supported speed mode.

### Comment 5 ([user]):

[user] i think i have those (i know abosultly nothing about this stuff but i use the integration and have the same issue as listed above) if there is a way to update to your version to test i can let you know

### Comment 6 ([user]):

ahhh, wondered what caused this

### Comment 7 ([user]):

Installation method Home Assistant OS
Core 2026.1.2
Supervisor 2026.01.1
Operating System 17.0
Frontend 20260107.2

2 Erros:

Logger: homeassistant.components.websocket_api.http.connection
Source: components/websocket_api/commands.py:278
integration: Home Assistant WebSocket API (documentation, issues)
First occurred: 7:07:42 PM (4 occurrences)
Last logged: 7:08:27 PM

[140194389471168] Unexpected exception
Traceback (most recent call last):
  File "/usr/src/homeassistant/homeassistant/components/websocket_api/commands.py", line 278, in handle_call_service
    response = await hass.services.async_call(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ...<7 lines>...
    )
    ^
  File "/usr/src/homeassistant/homeassistant/core.py", line 2819, in async_call
    response_data = await coro
                    ^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/core.py", line 2862, in _execute_service
    return await target(service_call)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/helpers/service.py", line 832, in entity_service_call
    single_response = await _handle_entity_call(
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^
        hass, entity, func, data, call.context
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/usr/src/homeassistant/homeassistant/helpers/service.py", line 904, in _handle_entity_call
    result = await task
             ^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/climate/__init__.py", line 828, in async_service_temperature_set
    await entity.async_set_temperature(**kwargs)
  File "/usr/src/homeassistant/homeassistant/components/coolmaster/climate.py", line 149, in async_set_temperature
    self.async_write_ha_state()
    ~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/usr/src/homeassistant/homeassistant/helpers/entity.py", line 1024, in async_write_ha_state
    self._async_write_ha_state()
    ~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/usr/src/homeassistant/homeassistant/helpers/entity.py", line 1149, in _async_write_ha_state
    self.__async_calculate_state()
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/usr/src/homeassistant/homeassistant/helpers/entity.py", line 1088, in __async_calculate_state
    if state_attributes := self.state_attributes:
                           ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/climate/__init__.py", line 378, in state_attributes
    data[ATTR_FAN_MODE] = self.fan_mode
                          ^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/coolmaster/climate.py", line 127, in fan_mode
    return CM_TO_HA_FAN[self._unit.fan_speed]
           ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
KeyError: 'vlow'

-----------------------------------------------------------------------------------------------------------

Logger: homeassistant.components.climate
Source: helpers/entity_platform.py:684
integration: Climate (documentation, issues)
First occurred: January 21, 2026 at 8:10:10 PM (6 occurrences)
Last logged: January 21, 2026 at 8:10:10 PM

Error adding entity climate.l6_102 for domain climate with platform coolmaster
Error adding entity climate.l6_103 for domain climate with platform coolmaster
Error adding entity climate.l6_201 for domain climate with platform coolmaster
Error adding entity climate.l6_203 for domain climate with platform coolmaster
Error adding entity climate.l6_206 for domain climate with platform coolmaster
Traceback (most recent call last):
  File "/usr/src/homeassistant/homeassistant/helpers/entity_platform.py", line 684, in _async_add_entities
    await self._async_add_entity(
        entity, False, entity_registry, config_subentry_id
    )
  File "/usr/src/homeassistant/homeassistant/helpers/entity_platform.py", line 1010, in _async_add_entity
    await entity.add_to_platform_finish()
  File "/usr/src/homeassistant/homeassistant/helpers/entity.py", line 1380, in add_to_platform_finish
    self.async_write_ha_state()
    ~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/usr/src/homeassistant/homeassistant/helpers/entity.py", line 1024, in async_write_ha_state
    self._async_write_ha_state()
    ~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/usr/src/homeassistant/homeassistant/helpers/entity.py", line 1149, in _async_write_ha_state
    self.__async_calculate_state()
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/usr/src/homeassistant/homeassistant/helpers/entity.py", line 1088, in __async_calculate_state
    if state_attributes := self.state_attributes:
                           ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/climate/__init__.py", line 378, in state_attributes
    data[ATTR_FAN_MODE] = self.fan_mode
                          ^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/coolmaster/climate.py", line 127, in fan_mode
    return CM_TO_HA_FAN[self._unit.fan_speed]
           ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
KeyError: 'top'

### Comment 8 ([user]):

Another user here with the same issue showing for some AC units that have a fan speed "top" available...

`Logger: homeassistant.components.climate
Source: helpers/entity_platform.py:684
integration: Climate (documentation, issues)
First occurred: 19:38:07 (4 occurrences)
Last logged: 20:29:27

Error adding entity climate.master_bedroom_hvac for domain climate with platform coolmaster
Error adding entity climate.lacie_bedroom_hvac for domain climate with platform coolmaster
Traceback (most recent call last):
  File "/usr/src/homeassistant/homeassistant/helpers/entity_platform.py", line 684, in _async_add_entities
    await self._async_add_entity(
        entity, False, entity_registry, config_subentry_id
    )
  File "/usr/src/homeassistant/homeassistant/helpers/entity_platform.py", line 1010, in _async_add_entity
    await entity.add_to_platform_finish()
  File "/usr/src/homeassistant/homeassistant/helpers/entity.py", line 1380, in add_to_platform_finish
    self.async_write_ha_state()
    ~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/usr/src/homeassistant/homeassistant/helpers/entity.py", line 1024, in async_write_ha_state
    self._async_write_ha_state()
    ~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/usr/src/homeassistant/homeassistant/helpers/entity.py", line 1149, in _async_write_ha_state
    self.__async_calculate_state()
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/usr/src/homeassistant/homeassistant/helpers/entity.py", line 1088, in __async_calculate_state
    if state_attributes := self.state_attributes:
                           ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/climate/__init__.py", line 378, in state_attributes
    data[ATTR_FAN_MODE] = self.fan_mode
                          ^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/coolmaster/climate.py", line 127, in fan_mode
    return CM_TO_HA_FAN[self._unit.fan_speed]
           ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
KeyError: 'top'
`

## PR Review Comments

**[user]** on `tests/components/coolmaster/test_climate.py`:

I think refactoring the HVAC modes test should be in a separate PR, shouldn't it?

**[user]** on `tests/components/coolmaster/test_climate.py`:

this is fixed

**[user]** on `homeassistant/components/coolmaster/climate.py`:

On 2nd thought, I think we should just fall back to the coolmaster mode if it's not in `CM_TO_HA_FAN`. While `vlow` and `top` seem to be the only states today, we don't know what's going to happen in the future (or if there were any others in past models).
Something like
```python
CM_TO_HA_FAN.get(self._unit.fan_speed, self._unit.fan_speed)
```

**[user]** on `homeassistant/components/coolmaster/climate.py`:

And based on https://github.com/home-assistant/core/issues/160655#issuecomment-3748131655, there might also be a casing problem

**[user]** on `homeassistant/components/coolmaster/climate.py`:

i added both case insensitivity and handling for unknown fan speeds (and added tests for both).

i left the enumeration of known coolmaster-only speeds in, so that `FAN_MODES` and the `fan_modes` property would return them - let me know what you think. thanks!

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
