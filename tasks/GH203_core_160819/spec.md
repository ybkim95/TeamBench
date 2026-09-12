# GH203_core_160819: Google Cast: detect state and attributes when device is doing active non-media casting — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/home-assistant/core/issues/160814
- Repo: https://github.com/home-assistant/core

## Issue Description

## The problem

The Google Cast integration does not populate state information and attributes for custom receiver applications like DashCast that don't implement the standard media playback interface. The device info is present via pychromecast which can be verified with [catt](https://github.com/skorokithakis/catt) using `catt -d "<device ip>" info`

## What version of Home Assistant Core has the issue?

version-2026.1.1

## What was the last working version of Home Assistant Core?

none that I'm aware of

## What type of installation are you running?

 Core

## Integration causing the issue

Google Cast

## Steps to reproduce

1. Install catt (https://github.com/skorokithakis/catt)  
2. Cast a URL `catt -d "<device IP>" cast_site "<url>"`
3. Verify current cast device info with `catt -d "<device IP>" info` - this shows useful state info in "app_id", "namespaces" and "display_name"
4. Observe that state in HomeAssistant for Google Cast integration device is "off" and no useful attributes are present. 

## Expected behavior

When there is an active cast displayed on the device, the state of the Google Cast device should be "playing" (or something other than "off") with useful attributes from pychomecast present:

```
app_id: 84912283
display_name: DashCast
namespaces: com.madmod.dashcast
 ````

## Actual behavior

The device shows as "off" with no useful attributes present to detect the actual state of whether the display is being cast to or not. 

## Impact

This breaks automations that rely on detecting when specific apps are running on Cast devices, particularly for dashboard casting use cases.

## Suggested fix

The Cast integration should populate state and attributes regardless of whether the app implements media playback functionality. Non-media apps are still valid Cast receivers and should have their identity tracked.

## What type of installation are you running?

Home Assistant Container

## Integration causing the issue

Google Cast

## Link to integration documentation on our website

https://www.home-assistant.io/integrations/cast/

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hey there [user], mind taking a look at this issue as it has been labeled with an integration (`cast`) you are listed as a [code owner](https://github.com/home-assistant/core/blob/dev/CODEOWNERS#L274) for? Thanks!

<details>
<summary>Code owner commands</summary>

Code owners of `cast` can trigger bot actions by commenting:

- `@home-assistant close` Closes the issue.
- `@home-assistant rename Awesome new title` Renames the issue.
- `@home-assistant reopen` Reopen the issue.
- `@home-assistant unassign cast` Removes the current integration label and assignees on the issue, add the integration domain after the command.
- `@home-assistant add-label needs-more-information` Add a label (needs-more-information, problem in dependency, problem in custom component) to the issue.
- `@home-assistant remove-label needs-more-information` Remove a label (needs-more-information, problem in dependency, problem in custom component) on the issue.

</details>

<sub><sup>(message by CodeOwnersMention)</sup></sub>

---

[cast documentation](https://www.home-assistant.io/integrations/cast)
[cast source](https://github.com/home-assistant/core/tree/dev/homeassistant/components/cast)
<sub><sup>(message by IssueLinks)</sup></sub>

### Comment 2 ([user]):

Thanks [user] I think we have duplicate [(https://github.com/home-assistant/core/issues/156199)] I am unsure if it is in fact the same but i am guessing it is and can close the other issue? It appears you have reported and Fixed the issue also so many thanks for that last part ... I was still stuck on an older version of HA and was getting nervous things would be breaking

### Comment 3 ([user]):

> Thanks [user] I think we have duplicate [(https://github.com/[/issues/156199](https://github.com/home-assistant/core/issues/156199))] I am unsure if it is in fact the same but i am guessing it is and can close the other issue? It appears you have reported and Fixed the issue also so many thanks for that last part ... I was still stuck on an older version of HA and was getting nervous things would be breaking

Looks like the same thing. If you want to test the PR before it gets merged into a new Home Assistant version, you can copy the [core directory](https://github.com/nopoz/core/tree/google_cast/homeassistant/components/cast) from my PR fork and put it in the [<config_dir>/custom_components](https://developers.home-assistant.io/docs/creating_component_index/) directory which will override the default cast integration. 

You'll also need to modify the cast manifest.json file to contain an arbitrary version like `"version": "1.0.0"` to get Home Assistant to load it:

manifest.json example:

```
{
  "domain": "cast",
  "name": "Google Cast",
  "after_dependencies": [
    "cloud",
    "http",
    "media_source",
    "plex",
    "tts",
    "zeroconf"
  ],
  "codeowners": ["[user]"],
  "config_flow": true,
  "documentation": "https://www.home-assistant.io/integrations/cast",
  "integration_type": "hub",
  "iot_class": "local_polling",
  "loggers": ["casttube", "pychromecast"],
  "requirements": ["PyChromecast==14.0.9"],
  "single_config_entry": true,
  "zeroconf": ["_googlecast._tcp.local."],
  "version": "1.0.0"
}
```

### Comment 4 ([user]):

I tested the PR and it works

### Comment 5 ([user]):

Same here, works

## PR Review Comments

**[user]** on `homeassistant/components/cast/media_player.py`:

By moving the HDMI check below the app_id check, a Cast device that has an app registered but has its HDMI physically disconnected would now report IDLE
  instead of OFF. Is this the intended behavior?

**[user]** on `homeassistant/components/cast/media_player.py`:

Probably just styling consistency and not functional, but is there a reference to use APP_BACKDROP via pychromecast.config when you are already importing it on line 13?

**[user]** on `tests/components/cast/test_media_player.py`:

I'd suggest a similar test that has app_id=None + is_idle=True.  This should still be off.

**[user]** on `tests/components/cast/test_media_player.py`:

Suggestion on an additional test:

app_id set to 84912283 + is_idle=False + no media status = should be idle

**[user]** on `homeassistant/components/cast/media_player.py`:

Yes, this is intentional. The goal is to ensure that if an app is actively running (like DashCast), the entity remains visible and controllable in Home Assistant - even if pychromecast reports the device as idle due to HDMI status or missing media namespace support. Reporting OFF would hide the app_id attribute and prevent users from stopping the application.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
