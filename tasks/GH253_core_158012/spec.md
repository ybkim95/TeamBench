# GH253_core_158012: Fix Ring integration log flooding for accounts without subscription — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/home-assistant/core/issues/134095
- Repo: https://github.com/home-assistant/core

## Issue Description

### The problem

Every three or four minutes, a message is logged that says, "Your Ring account does not have an active subscription."  

This message isn't necessary at all.  Logging this once at boot would be reasonable.  Logging it 480 times each day is completely unreasonable.  

At least one other person is seeing this:
https://community.home-assistant.io/t/turn-off-ring-subscription-warning/813722

Can this message be removed, or modified to happen only on boot?  Or can it be controlled with a toggle in UI?  

### What version of Home Assistant Core has the issue?

core-2024.12.5

### What was the last working version of Home Assistant Core?

_No response_

### What type of installation are you running?

Home Assistant OS

### Integration causing the issue

Ring

### Link to integration documentation on our website

https://www.home-assistant.io/integrations/ring/

### Diagnostics information

[home-assistant_ring_2024-12-27T15-59-35.341Z.log](https://github.com/user-attachments/files/18261966/home-assistant_ring_2024-12-27T15-59-35.341Z.log)

### Example YAML snippet

_No response_

### Anything in the logs that might be useful for us?

```txt
2024-12-27 10:24:38.762 WARNING (MainThread) [ring_doorbell.doorbot] Your Ring account does not have an active subscription.
2024-12-27 10:27:38.763 WARNING (MainThread) [ring_doorbell.doorbot] Your Ring account does not have an active subscription.
2024-12-27 10:30:38.841 WARNING (MainThread) [ring_doorbell.doorbot] Your Ring account does not have an active subscription.
2024-12-27 10:34:38.787 WARNING (MainThread) [ring_doorbell.doorbot] Your Ring account does not have an active subscription.
2024-12-27 10:38:38.882 WARNING (MainThread) [ring_doorbell.doorbot] Your Ring account does not have an active subscription.
2024-12-27 10:41:38.918 WARNING (MainThread) [ring_doorbell.doorbot] Your Ring account does not have an active subscription.
2024-12-27 10:45:38.797 WARNING (MainThread) [ring_doorbell.doorbot] Your Ring account does not have an active subscription.
2024-12-27 10:48:38.831 WARNING (MainThread) [ring_doorbell.doorbot] Your Ring account does not have an active subscription.
2024-12-27 10:51:38.942 WARNING (MainThread) [ring_doorbell.doorbot] Your Ring account does not have an active subscription.
2024-12-27 10:55:38.822 WARNING (MainThread) [ring_doorbell.doorbot] Your Ring account does not have an active subscription.
2024-12-27 10:57:38.388 DEBUG (MainThread) [ring_doorbell.ring] url: /clients_api/ring_devices
method: GET
json: None
data: None
 extra_params: None
2024-12-27 10:57:38.589 DEBUG (MainThread) [ring_doorbell.ring] url: /clients_api/doorbots/27437855/history
method: GET
json: None
data: None
 extra_params: {'limit': 10}
2024-12-27 10:57:38.590 DEBUG (MainThread) [ring_doorbell.ring] url: /clients_api/doorbots/27437855/health
method: GET
json: None
data: None
 extra_params: None
2024-12-27 10:57:38.754 DEBUG (MainThread) [homeassistant.components.ring.coordinator] Finished fetching devices data in 0.366 seconds (success: True)
2024-12-27 10:58:38.388 DEBUG (MainThread) [ring_doorbell.ring] url: /clients_api/ring_devices
method: GET
json: None
data: None
 extra_params: None
2024-12-27 10:58:38.597 DEBUG (MainThread) [ring_doorbell.ring] url: /clients_api/doorbots/27437855/history
method: GET
json: None
data: None
 extra_params: {'limit': 10}
2024-12-27 10:58:38.598 DEBUG (MainThread) [ring_doorbell.ring] url: /clients_api/doorbots/27437855/health
method: GET
json: None
data: None
 extra_params: None
2024-12-27 10:58:38.831 DEBUG (MainThread) [homeassistant.components.ring.coordinator] Finished fetching devices data in 0.443 seconds (success: True)
2024-12-27 10:58:38.832 WARNING (MainThread) [ring_doorbell.doorbot] Your Ring account does not have an active subscription.
```

### Additional information

_No response_

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hey there [user], mind taking a look at this issue as it has been labeled with an integration (`ring`) you are listed as a [code owner](https://github.com/home-assistant/core/blob/dev/CODEOWNERS#L1253) for? Thanks!

<details>
<summary>Code owner commands</summary>

Code owners of `ring` can trigger bot actions by commenting:

- `@home-assistant close` Closes the issue.
- `@home-assistant rename Awesome new title` Renames the issue.
- `@home-assistant reopen` Reopen the issue.
- `@home-assistant unassign ring` Removes the current integration label and assignees on the issue, add the integration domain after the command.
- `@home-assistant add-label needs-more-information` Add a label (needs-more-information, problem in dependency, problem in custom component) to the issue.
- `@home-assistant remove-label needs-more-information` Remove a label (needs-more-information, problem in dependency, problem in custom component) on the issue.

</details>

<sub><sup>(message by CodeOwnersMention)</sup></sub>

---

[ring documentation](https://www.home-assistant.io/integrations/ring)
[ring source](https://github.com/home-assistant/core/tree/dev/homeassistant/components/ring)
<sub><sup>(message by IssueLinks)</sup></sub>

### Comment 2 ([user]):

I am seeing this issue as well...

### Comment 3 ([user]):

The issue is caused by the new Live View entities.
Until this is fixed, disabling the Live View entities prevents the messages from being logged.

### Comment 4 ([user]):

Check out this work around by suppressing the error message. 

https://community.home-assistant.io/t/turn-off-ring-subscription-warning/813722/5?u=dflash

Add this to your configuration file.

logger:
  default: warning
  logs:
    ring_doorbell.doorbot: error 

Its working on my instance of HA OS 2025.6.1

### Comment 5 ([user]):

Affecting me too.  If I add that to suppress would that also suppress other warning messages that might indicate an actual problem?

### Comment 6 ([user]):

> Affecting me too. If I add that to suppress would that also suppress other warning messages that might indicate an actual problem?

default: warning
Sets the default log level for all Home Assistant components to warning. This means only warnings, errors, and critical messages will be logged — info and debug messages will be suppressed.

ring_doorbell.doorbot: error
This sets a specific log level for the ring_doorbell.doorbot integration (typically used with Ring cameras/doorbells) to error. That means only errors and critical issues from this integration will be logged — not even warnings.

### Comment 7 ([user]):

Another workaround is to suppress this warning with a [log filter](https://www.home-assistant.io/integrations/logger/#log-filters):
```yaml
logger:
  filters:
    ring_doorbell.doorbot:
      - "Your Ring account does not have an active subscription"
```
This way you still get all other messages without changing the log level.

### Comment 8 ([user]):

There hasn't been any activity on this issue recently. Due to the high number of incoming GitHub notifications, we have to clean some of the old issues, as many of them have already been resolved with the latest updates.
Please make sure to update to the latest Home Assistant version and check if that solves the issue. Let us know if that works for you by adding a comment 👍
This issue has now been marked as stale and will be closed if no further activity occurs. Thank you for your contributions.

### Comment 9 ([user]):

Don't believe this has been solved.

## PR Review Comments

**[user]** on `homeassistant/components/ring/camera.py`:

what I don't quite understand: We are still making the call through the library, we are just not writing to the state machine, so how does this fix the problem? What parts exactly do not work without the subscription, should this entity rather be `Unavailable` if we don't have that?

**[user]** on `homeassistant/components/ring/camera.py`:

Thanks for the review! Let me clarify the code flow:

The warning comes from `async_recording_url()` in the ring_doorbell library. Here's the call chain that triggers it:

```
_handle_coordinator_update()
  └─> async_schedule_update_ha_state(True)  [line 145]
        └─> async_update()  [line 247]
              └─> _async_get_video()  [line 270]
                    └─> self._device.async_recording_url()  [line 282] ← warning logged here
```

My fix returns early at line 138, before `async_schedule_update_ha_state(True)` is called. This means `async_update()` is never triggered for live_view entities without subscription, so the library call that logs the warning never happens.

The test I added `(test_camera_live_view_no_subscription`) verifies this by asserting that `async_recording_url` is never called when `has_subscription` is False.

**[user]** on `homeassistant/components/ring/camera.py`:

Sorry I didn't reply to this:

> What parts exactly do not work without the subscription

As per the attached issue, my logs are flooding with warning messages 1000 times a day

<img width="449" height="199" alt="Image" src="https://github.com/user-attachments/assets/1de56a4c-40bd-467e-ab1a-cfaf0f6d9dc8" />

**[user]** on `homeassistant/components/ring/camera.py`:

Yes, the log part is clear. Right now you are basically disabling updates. What I'm trying to understand is, if we should rather disable this entity entirely. Now, `self._video_url = await self._async_get_video()` is never called, I'm not sure which parts of the entity this will break, but it sounds like it might not be able to do what it is intended to (showing a video feed)

**[user]** on `homeassistant/components/ring/camera.py`:

I should say the integration works great for a live view without a subscription, just it doesn't have history (as expected)

<img width="566" height="444" alt="Image" src="https://github.com/user-attachments/assets/ff004815-a53a-4774-8377-fd0dd33854b6" />

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
