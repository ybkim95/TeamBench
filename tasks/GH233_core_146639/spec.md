# GH233_core_146639: Add backward compatibility with older versions of Traccar server — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/home-assistant/core/issues/110098
- Repo: https://github.com/home-assistant/core

## Issue Description

### The problem

After the latest update in Home Assistant where Traccar Server has been moved to the UI, traccar is not working anymore

### What version of Home Assistant Core has the issue?

core-2024.2.0

### What was the last working version of Home Assistant Core?

core-2024.1.6

### What type of installation are you running?

Home Assistant OS

### Integration causing the issue

traccar_server

### Link to integration documentation on our website

https://www.home-assistant.io/integrations/traccar_server/

### Diagnostics information

_No response_

### Example YAML snippet

_No response_

### Anything in the logs that might be useful for us?

```txt
Logger: homeassistant.components.traccar_server
Source: helpers/update_coordinator.py:313
Integration: Traccar Server (documentation, issues)
First occurred: 8 February 2024 at 13:56:39 (1011 occurrences)
Last logged: 12:12:29

Unexpected error fetching traccar_server data: 'geofenceIds'
Traceback (most recent call last):
  File "/usr/src/homeassistant/homeassistant/helpers/update_coordinator.py", line 313, in _async_refresh
    self.data = await self._async_update_data()
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/homeassistant/homeassistant/components/traccar_server/coordinator.py", line 120, in _async_update_data
    position["geofenceIds"] or [],
    ~~~~~~~~^^^^^^^^^^^^^^^
KeyError: 'geofenceIds'
```

### Additional information

_No response_

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hey there [user], mind taking a look at this issue as it has been labeled with an integration (`traccar_server`) you are listed as a [code owner](https://github.com/home-assistant/core/blob/dev/CODEOWNERS#L1398) for? Thanks!

<details>
<summary>Code owner commands</summary>

Code owners of `traccar_server` can trigger bot actions by commenting:

- `@home-assistant close` Closes the issue.
- `@home-assistant rename Awesome new title` Renames the issue.
- `@home-assistant reopen` Reopen the issue.
- `@home-assistant unassign traccar_server` Removes the current integration label and assignees on the issue, add the integration domain after the command.
- `@home-assistant add-label needs-more-information` Add a label (needs-more-information, problem in dependency, problem in custom component) to the issue.
- `@home-assistant remove-label needs-more-information` Remove a label (needs-more-information, problem in dependency, problem in custom component) on the issue.

</details>

<sub><sup>(message by CodeOwnersMention)</sup></sub>

---

[traccar_server documentation](https://www.home-assistant.io/integrations/traccar_server)
[traccar_server source](https://github.com/home-assistant/core/tree/dev/homeassistant/components/traccar_server)
<sub><sup>(message by IssueLinks)</sup></sub>

### Comment 2 ([user]):

Looks like you are using a old traccar version.
Update your server.
I believer it was in 5.4 they moved that from device to position

### Comment 3 ([user]):

[user] you are right. For anyone having the same issue, updating traccar to v5.10 solves the issue.

Note: I tried to update traccar to v5.12 which is the latest version, and the position of my car is correctly displayed in Home Assistant but it dissapeared from the traccar UI, so I will stay in v5.10 for now

## PR Review Comments

**[user]** on `homeassistant/components/traccar_server/coordinator.py`:

This will work around the current problem with old servers.
But Im not sure that is what is wanted.
Why can't you update?

**[user]** on `homeassistant/components/traccar_server/coordinator.py`:

I'm affected by this Docker issue w/ newer versions of Traccar:
```
[0.006s][warning][os,thread] Failed to start thread "GC Thread#0" - pthread_create failed (EPERM) for attributes: stacksize: 1024k, guardsize: 4k, detached.
#
# There is insufficient memory for the Java Runtime Environment to continue.
# Cannot create worker GC thread. Out of system resources.
# An error report file with more information is saved as:
# /opt/traccar/hs_err_pid1.log
```
Basically, the host OS is too old. I'm in the process of upgrading, but it's taking me time since i can't just upgrade in place.

I understand you point of view, and fully agree w/ it. This change would just help for the migration period.

**[user]** on `homeassistant/components/traccar_server/coordinator.py`:

That does not seem like a docker issue to me.
Cant you just tell it to use more with JAVA_OPTS?

**[user]** on `homeassistant/components/traccar_server/coordinator.py`:

Have a look at this SO answer: https://stackoverflow.com/a/72841934/2626244

**[user]** on `homeassistant/components/traccar_server/coordinator.py`:

And the replies for that do not work?

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
