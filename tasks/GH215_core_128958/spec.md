# GH215_core_128958: Fix nfandroidtv service notify disappears when restarting home assistant — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/home-assistant/core/issues/108296
- Repo: https://github.com/home-assistant/core

## Issue Description

### The problem

Upon restarting HA, the service `notify.my_android_tv` disappears
Resulting in an error and a repair notification:
```
The automation "Ring Motion Detected Notify on TV" (automation.ring_motion_detected_notify_on_tv) has an action that calls an unknown service: notify.lounge_tv.
```
Only 'fix' is to uninstall the integration, and reinstall 

### What version of Home Assistant Core has the issue?

2024.1.3

### What was the last working version of Home Assistant Core?

_No response_

### What type of installation are you running?

Home Assistant OS

### Integration causing the issue

Notifications for Android TV / Fire TV

### Link to integration documentation on our website

https://www.home-assistant.io/integrations/nfandroidtv

### Diagnostics information

_No response_

### Example YAML snippet

_No response_

### Anything in the logs that might be useful for us?

```txt
Not sure this is the relevant log dump, but the only thing showing immediately after a restart

2024-01-18 13:43:06.320 ERROR (MainThread) [homeassistant] Error doing job: Task exception was never retrieved
Traceback (most recent call last):
File "/usr/src/homeassistant/homeassistant/helpers/discovery_flow.py", line 96, in _async_start
await gather_with_limited_concurrency(
File "/usr/src/homeassistant/homeassistant/util/async_.py", line 188, in gather_with_limited_concurrency
return await gather(
^^^^^^^^^^^^^
File "/usr/src/homeassistant/homeassistant/util/async_.py", line 186, in sem_task
return await task
^^^^^^^^^^
File "/usr/src/homeassistant/homeassistant/config_entries.py", line 888, in async_init
flow, result = await task
^^^^^^^^^^
File "/usr/src/homeassistant/homeassistant/config_entries.py", line 916, in _async_init
result = await self._async_handle_step(flow, flow.init_step, data)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/usr/src/homeassistant/homeassistant/data_entry_flow.py", line 423, in _async_handle_step
if result.get("preview") is not None:
^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'get'
```
```

### Additional information

_No response_

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hey there [user], mind taking a look at this issue as it has been labeled with an integration (`nfandroidtv`) you are listed as a [code owner](https://github.com/home-assistant/core/blob/dev/CODEOWNERS#L869) for? Thanks!

<details>
<summary>Code owner commands</summary>

Code owners of `nfandroidtv` can trigger bot actions by commenting:

- `@home-assistant close` Closes the issue.
- `@home-assistant rename Awesome new title` Renames the issue.
- `@home-assistant reopen` Reopen the issue.
- `@home-assistant unassign nfandroidtv` Removes the current integration label and assignees on the issue, add the integration domain after the command.
- `@home-assistant add-label needs-more-information` Add a label (needs-more-information, problem in dependency, problem in custom component) to the issue.
- `@home-assistant remove-label needs-more-information` Remove a label (needs-more-information, problem in dependency, problem in custom component) on the issue.

</details>

<sub><sup>(message by CodeOwnersMention)</sup></sub>

---

[nfandroidtv documentation](https://www.home-assistant.io/integrations/nfandroidtv)
[nfandroidtv source](https://github.com/home-assistant/core/tree/dev/homeassistant/components/nfandroidtv)
<sub><sup>(message by IssueLinks)</sup></sub>

### Comment 2 ([user]):

I'm having the same issue, but opening the app on my Chromecast with google tv before reloading the integration makes it work again.

Very annoying, as all automations using this to send notifications will fail when the integration isn't loaded.

### Comment 3 ([user]):

I am seeing the same behavior, the integration fails to load unless I first launch the app (on Nvidia Shield in my case)

### Comment 4 ([user]):

Doesn't look like like this integration is being actively maintained unfortunately, so I doubt we will see a fix

### Comment 5 ([user]):

I receive the same error, every time I reboot Home Assistant. But the service is working fine on my Philips Android TV.

### Comment 6 ([user]):

I am seeing the same behavior and HA sent me repair notices because the automations I have which consume the service are now broken.

### Comment 7 ([user]):

I have the same error....

"The automation "Doorbell Snapshot" (automation.doorbell_snapshot) has an action that calls an unknown service: notify.android_tv_fire_tv."

I hope the creator will see these messages and fix the error.  :(

### Comment 8 ([user]):

Note:  I was able to get it working again. I removed the entry in Notifications for Android TV/Fire Stick integration, restarted HAss, and then re-added the entry. Then restarted HAss and it works again.  I didn't remove the integration, just the entry - just to clarify. So now it's working again for me!

Edit: Simply disconnecting the WiFi on my Firestick and reconnecting to my WFi allows me to reload the integration successfully, so no need to remove the integration. Just disconnect and reconnect to your wifi and reload the integration fixes it until next reboot of HAss.

### Comment 9 ([user]):

Same here. Upon restarting HA, the service `notify.android_tv` becomes State `missing` until the TV is switched on.

### Comment 10 ([user]):

[user] would you like to take a look at this?

## PR Review Comments

**[user]** on `homeassistant/components/nfandroidtv/notify.py`:

Instead, let's raise a `HomeAssistantError` instead of silently failing

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
