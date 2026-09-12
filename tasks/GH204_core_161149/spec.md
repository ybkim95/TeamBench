# GH204_core_161149: Fix Reolink camera updates persisting in UI — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/home-assistant/core/issues/156779
- Repo: https://github.com/home-assistant/core

## Issue Description

### The problem

Since 2025.11.1 or 2 The reolink integration is showing a firmware upgrade available for RLN36

Installed version: v3.6.0.415_25062842
Latest version : New firmware available
Hardware: N5MB01 

The update does not work, and following the release announcement link to Reolink shows that v3.6.0.415_25062842 is the latest version available.

I can of course skip the update, but it pops up every reboot or HA update. This is a new behavior.

### What version of Home Assistant Core has the issue?

2025.11.2

### What was the last working version of Home Assistant Core?

2025.10.X

### What type of installation are you running?

Home Assistant OS

### Integration causing the issue

Reolink

### Link to integration documentation on our website

https://www.home-assistant.io/integrations/reolink/

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

Hey there [user], mind taking a look at this issue as it has been labeled with an integration (`reolink`) you are listed as a [code owner](https://github.com/home-assistant/core/blob/dev/CODEOWNERS#L1320) for? Thanks!

<details>
<summary>Code owner commands</summary>

Code owners of `reolink` can trigger bot actions by commenting:

- `@home-assistant close` Closes the issue.
- `@home-assistant rename Awesome new title` Renames the issue.
- `@home-assistant reopen` Reopen the issue.
- `@home-assistant unassign reolink` Removes the current integration label and assignees on the issue, add the integration domain after the command.
- `@home-assistant add-label needs-more-information` Add a label (needs-more-information, problem in dependency, problem in custom component) to the issue.
- `@home-assistant remove-label needs-more-information` Remove a label (needs-more-information, problem in dependency, problem in custom component) on the issue.

</details>

<sub><sup>(message by CodeOwnersMention)</sup></sub>

---

[reolink documentation](https://www.home-assistant.io/integrations/reolink)
[reolink source](https://github.com/home-assistant/core/tree/dev/homeassistant/components/reolink)
<sub><sup>(message by IssueLinks)</sup></sub>

### Comment 2 ([user]):

Actually seems there is a new version when I go through the REOLINK app itself, it is just not listed on their website and not coming through on the Home Assistant integration: 
Note: v3.6.3.437_25110427 pops up when I check via the reolink desktop app.

### Comment 3 ([user]):

If HomeAssistant shows "New firmware available" the camera itself is reporting that a new firmware is available.
In that case it should indeed be visable in the Reolink app.

If HA shows a firmware version as new version, HA found a new version on the Reolink Download Center.

If you click install in HA, in this case the API command is sent to the camera to install this new version, why that does not suceed I do not know.

Did you already try installing the new firmware through the Reolink app?
Does it also give a error then?

I expect Reolink to upload this new version v3.6.3.437_25110427 to the Reolink Download Center in the coming weeks (most of the time they do that within about a week). Once on the Reolink Download Center, HA should not have issues uploading it to the NVR.

### Comment 4 ([user]):

What is the error in HomeAssistant when you try to install?

### Comment 5 ([user]):

Yes the app installed correctly.
Your explanation makes perfect sense (and is what I figured must be the case after investigating further).
Unfortunately I can’t remember the error, and now that it is updated I cannot repeat it.
No doubt it is because the update is not on their public server as you said.
I will come back here and post the error if it happens again.

### Comment 6 ([user]):

I have the same issue. There is no update available in the Reolink app.

This appears to stem from the release date (or the like) of the firmware file:
```
Installed Version: v3.1.0.951_22041567
Newest Version: v3.1.0.951_24022167
```

### Comment 7 ([user]):

[user] can you share your diagnostic info file?
https://www.home-assistant.io/docs/configuration/troubleshooting/#download-diagnostics

I need to know the model and hardware version

### Comment 8 ([user]):

[user] Of course.
On every HA restart, without fail, it will notify me of a new software version, even when I've skipped it before.

[config_entry-reolink-01KBW4ZDTGD0D43XSV2RV0GX0E.json](https://github.com/user-attachments/files/24161500/config_entry-reolink-01KBW4ZDTGD0D43XSV2RV0GX0E.json)

### Comment 9 ([user]):

[user] there actually is a updated firmware available for your camera in the reolink download center: https://reolink.com/nl/download-center/

Please use HomeAssistant to update the camera, or download it from the reolink download center and use the reolink desktop client to update the camera.

## PR Review Comments

**[user]** on `homeassistant/components/reolink/update.py`:

do we really need an update here, or would a `self.async_write_ha_state()` suffice - we already know the current version?

**[user]** on `homeassistant/components/reolink/update.py`:

what I don't love about this change is that now this entity is listening to two coordinators, which is unusual and also we now notify it about updates which in 99% of the updates are irrelevant. Can we only notify the entity if we know the versions mismatch?

**[user]** on `homeassistant/components/reolink/update.py`:

Maybe signal from the update function of the coordinator?

**[user]** on `homeassistant/components/reolink/update.py`:

I agree, i dont like polling the cloud servers when not needed.

I want as little trafic to the cloud servers as possible.

**[user]** on `homeassistant/components/reolink/update.py`:

done

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
