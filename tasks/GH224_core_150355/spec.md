# GH224_core_150355: Fix for deCONZ issue - Detected that integration 'deconz' calls device_registry.async_get_or_create referencing a non existing via_device - #134539 — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/home-assistant/core/issues/134539
- Repo: https://github.com/home-assistant/core

## Issue Description

### The problem

Hi,

Since Home Assistant 2025.1.0b1, Deconz throws errors when starting Home Assistant. 

- This has been documented in this issue:  [47](https://github.com/home-assistant/core/issues/133947)](https://github.com/home-assistant/core/issues/133947)
- This has been partially fixed by this pr: (withheld: the upstream fix is not part of the task)

When upgrading to 2025.1.0b8, the errors are partially gone: the error regaring [deCONZ color temp 0 is never used when calculating kelvin CT] does not show up anymore.

Another part of the warning is still there:
Detected that integration 'deconz' calls `device_registry.async_get_or_create` referencing a non existing `via_device`

I've enabled debug logging, rebooted home assistant and captured the logs. You can find them here: https://pastebin.com/SL4UHQ2N

### What version of Home Assistant Core has the issue?

core-2025.1.0b8

### What was the last working version of Home Assistant Core?

core-2024.12.5

### What type of installation are you running?

Home Assistant OS

### Integration causing the issue

deCONZ

### Link to integration documentation on our website

https://www.home-assistant.io/integrations/deconz/

### Diagnostics information

_No response_

### Example YAML snippet

_No response_

### Anything in the logs that might be useful for us?

```txt
Detected that integration 'deconz' calls `device_registry.async_get_or_create` referencing a non existing `via_device` ('mac', '02:42:ac:11:00:05'), with device info: {'configuration_url': 'http://192.168.178.90:8081', 'entry_type': <DeviceEntryType.SERVICE: 'service'>, 'identifiers': {('deconz', '00212E05FBAA')}, 'manufacturer': 'Dresden Elektronik', 'model': 'deCONZ', 'name': 'Phoscon-GW', 'sw_version': '2.29.0', 'via_device': ('mac', '02:42:ac:11:00:05')} at homeassistant/components/deconz/hub/hub.py, line 197: device_registry.async_get_or_create(. This will stop working in Home Assistant 2025.12.0, please create a bug report at https://github.com/home-assistant/core/issues?q=is%3Aopen+is%3Aissue+label%3A%22integration%3A+deconz%22
```

### Additional information

_No response_

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hey there [user], mind taking a look at this issue as it has been labeled with an integration (`deconz`) you are listed as a [code owner](https://github.com/home-assistant/core/blob/dev/CODEOWNERS#L310) for? Thanks!

<details>
<summary>Code owner commands</summary>

Code owners of `deconz` can trigger bot actions by commenting:

- `@home-assistant close` Closes the issue.
- `@home-assistant rename Awesome new title` Renames the issue.
- `@home-assistant reopen` Reopen the issue.
- `@home-assistant unassign deconz` Removes the current integration label and assignees on the issue, add the integration domain after the command.
- `@home-assistant add-label needs-more-information` Add a label (needs-more-information, problem in dependency, problem in custom component) to the issue.
- `@home-assistant remove-label needs-more-information` Remove a label (needs-more-information, problem in dependency, problem in custom component) on the issue.

</details>

<sub><sup>(message by CodeOwnersMention)</sup></sub>

---

[deconz documentation](https://www.home-assistant.io/integrations/deconz)
[deconz source](https://github.com/home-assistant/core/tree/dev/homeassistant/components/deconz)
<sub><sup>(message by IssueLinks)</sup></sub>

### Comment 2 ([user]):

Same error in 2025.1.2:
`2025-01-16 03:00:47.301 WARNING (MainThread) [homeassistant.helpers.frame] Detected that integration 'deconz' calls `device_registry.async_get_or_create` referencing a non existing `via_device` ('mac', '02:42:ac:1e:21:01'), with device info: {'configuration_url': 'homeassistant://hassio/ingress/core_deconz', 'entry_type': <DeviceEntryType.SERVICE: 'service'>, 'identifiers': {('deconz', '00212E079C7A')}, 'manufacturer': 'Dresden Elektronik', 'model': 'deCONZ', 'name': 'Phoscon-GW', 'sw_version': '2.28.1', 'via_device': ('mac', '02:42:ac:1e:21:01')} at homeassistant/components/deconz/hub/hub.py, line 197: device_registry.async_get_or_create(. This will stop working in Home Assistant 2025.12.0, please create a bug report at https://github.com/home-assistant/core/issues?q=is%3Aopen+is%3Aissue+label%3A%22integration%3A+deconz%22`

### Comment 3 ([user]):

The error keeps occurring for me too `[2025.1.2]`.

Logger: homeassistant.helpers.frame
Quelle: helpers/frame.py:324
Erstmals aufgetreten: 14:08:22 (1 Vorkommnisse)
Zuletzt protokolliert: 14:08:22

Detected that integration 'deconz' calls `device_registry.async_get_or_create` referencing a non existing `via_device` ('mac', '02:42:ac:1e:21:01'), with device info: {'configuration_url': 'http://192.168.XXX.XX:80', 'entry_type': <DeviceEntryType.SERVICE: 'service'>, 'identifiers': {('deconz', '0021XXXXXXXX')}, 'manufacturer': 'Dresden Elektronik', 'model': 'deCONZ', 'name': 'XXXXXXX-Gateway', 'sw_version': '2.28.1', 'via_device': ('mac', '02:42:ac:1e:21:01')} at homeassistant/components/deconz/hub/hub.py, line 197: device_registry.async_get_or_create(. This will stop working in Home Assistant 2025.12.0, please create a bug report at https://github.com/home-assistant/core/issues?q=is%3Aopen+is%3Aissue+label%3A%22integration%3A+deconz%22

### Comment 4 ([user]):

Its not a dangerous message. If you read it it is only about making awareness about deprecated functionality. I will fix this

### Comment 5 ([user]):

same warning here 

it happens when i  updated to 2025.2.3 and 2025.2.4

Logger: homeassistant.helpers.frame
Bron: helpers/frame.py:324
Eerst voorgekomen: 19:55:38 (1 gebeurtenissen)
Laatst gelogd: 19:55:38

Detected that integration 'deconz' calls `device_registry.async_get_or_create` referencing a non existing `via_device` ('mac', '02:42:ac:1e:21:03'), with device info: {'configuration_url': 'http://172.30.33.3:40850', 'entry_type': <DeviceEntryType.SERVICE: 'service'>, 'identifiers': {('deconz', '00212E05A03B')}, 'manufacturer': 'Dresden Elektronik', 'model': 'deCONZ', 'name': 'DogConz', 'sw_version': '2.28.1', 'via_device': ('mac', '02:42:ac:1e:21:03')} at homeassistant/components/deconz/hub/hub.py, line 192: device_registry.async_get_or_create(. This will stop working in Home Assistant 2025.12.0, please create a bug report at https://github.com/home-assistant/core/issues?q=is%3Aopen+is%3Aissue+label%3A%22integration%3A+deconz%22

### Comment 6 ([user]):

[user] 
The log reads that `This will stop working in Home Assistant 2025.12.0`. What exactly is meant by this version? The Core version?

As of today, I have:
```
Core: 2025.2.5
Supervisor: 2025.02.1
Operating System: 14.2
Frontend: 20250221.0
```

### Comment 7 ([user]):

> [user] The log reads that `This will stop working in Home Assistant 2025.12.0`. What exactly is meant by this version? The Core version?
> 
> As of today, I have:
> 
> ```
> Core: 2025.2.5
> Supervisor: 2025.02.1
> Operating System: 14.2
> Frontend: 20250221.0
> ```

The issue is with the integration so it should be the core version yes.

### Comment 8 ([user]):

Meanwhile it is Core 2025.4.1. So what's the mileage till this will no longer work?

### Comment 9 ([user]):

It's mentioned in the logs:
_This will stop working in Home Assistant 2025.12.0_

### Comment 10 ([user]):

Hello, you do not need to worry, as stated it is referencing something "non existing" there will be no obvious change for users of the integration except that the log will disappear.

## PR Review Comments

**[user]** on `homeassistant/components/deconz/hub/hub.py`:

```suggestion
```
This is an unnecessary change

**[user]** on `homeassistant/components/deconz/hub/hub.py`:

```suggestion
```
I think we should just remove that registered device instead, its not used for any critical thing and I did it to have a traceable hierarchy from host to services on a host, but no-one is doing that.

**[user]** on `homeassistant/components/deconz/hub/hub.py`:

```suggestion
```
Not needed now that the host is removed

**[user]** on `tests/components/deconz/test_services.py`:

Why are these needed?

**[user]** on `tests/components/deconz/test_services.py`:

Why are you changing type to Dimmable light?

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
