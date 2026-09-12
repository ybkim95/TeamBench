# GH241_core_141667: Better throttling handling for the Renault API — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/home-assistant/core/issues/106777
- Repo: https://github.com/home-assistant/core

## Issue Description

### The problem

Since a week I'm continously hitting the API rate limits with the default refresh rate (even when not sending any commands from HA)
Seems like Renault has reduced again their rate-limits in recent times from what I'm seeing, has anyone noticed similar behaviour?
Is there any available information on what the rate limit is and what the window is? (e.g. 500 requests in a 24h window) or is it entirely guesswork?

### What version of Home Assistant Core has the issue?

core-2023.12.4

### What was the last working version of Home Assistant Core?

_No response_

### What type of installation are you running?

Home Assistant OS

### Integration causing the issue

renault

### Link to integration documentation on our website

https://www.home-assistant.io/integrations/renault

### Diagnostics information

_No response_

### Example YAML snippet

_No response_

### Anything in the logs that might be useful for us?

```txt
Logger: homeassistant.components.renault.renault_vehicle
Source: helpers/update_coordinator.py:332
Integration: Renault (documentation, issues)
First occurred: 15:20:41 (8 occurrences)
Last logged: 16:25:04

Error fetching UU1DBG005MU043525 location data: Error communicating with API: ('err.func.wired.overloaded', 'You have reached your quota limit')
Error fetching UU1DBG005MU043525 hvac_status data: Error communicating with API: ('err.func.wired.overloaded', 'You have reached your quota limit')
Error fetching UU1DBG005MU043525 cockpit data: Error communicating with API: ('err.func.wired.overloaded', 'You have reached your quota limit')
Error fetching UU1DBG005MU043525 battery data: Error communicating with API: ('err.func.wired.overloaded', 'You have reached your quota limit')
```

### Additional information

I have no clue but, it seems to happen more frequently when the car is charging, even though in the automation traces the automation which I am using to manage charging with PV has never sent any command, not even run. So I guess it can't be the culprit.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hey there [user], mind taking a look at this issue as it has been labeled with an integration (`renault`) you are listed as a [code owner](https://github.com/home-assistant/core/blob/dev/CODEOWNERS#L1071) for? Thanks!

<details>
<summary>Code owner commands</summary>

Code owners of `renault` can trigger bot actions by commenting:

- `@home-assistant close` Closes the issue.
- `@home-assistant rename Awesome new title` Renames the issue.
- `@home-assistant reopen` Reopen the issue.
- `@home-assistant unassign renault` Removes the current integration label and assignees on the issue, add the integration domain after the command.
- `@home-assistant add-label needs-more-information` Add a label (needs-more-information, problem in dependency, problem in custom component) to the issue.
- `@home-assistant remove-label needs-more-information` Remove a label (needs-more-information, problem in dependency, problem in custom component) on the issue.

</details>

<sub><sup>(message by CodeOwnersMention)</sup></sub>

---

[renault documentation](https://www.home-assistant.io/integrations/renault)
[renault source](https://github.com/home-assistant/core/tree/dev/homeassistant/components/renault)
<sub><sup>(message by IssueLinks)</sup></sub>

### Comment 2 ([user]):

I experince the exact same problem.

### Comment 3 ([user]):

I have a Zoe40, and I don't have these problems at all (but I have less API endpoints available...)

I have heard that it might be possible to use a "websocket" connection, but I have never had the time to investigate it. Maybe that would solve the problems if someone wants to investigate that...

### Comment 4 ([user]):

Note: the actual limit is entirely guess work.

### Comment 5 ([user]):

Hi, just a suggestion. Could we have a configurable poll rate. One if charging is active, one if not?

### Comment 6 ([user]):

I will happily review a PR if it is submitted

### Comment 7 ([user]):

> Hi, just a suggestion. Could we have a configurable poll rate. One if charging is active, one if not?

I don't think it would solve the issue tbh. We are already hitting the rate limit now, what would two different polling intervals achieve?
I see your idea, but we don't know what the quota is for which unit of time, so we can't really allocate a different rate for charging imho

### Comment 8 ([user]):

Hello, 
I have the same problem. Is there a way to set the query interval? Ideally, there is also a "button/switch" that can manually trigger the querying. For example, when a wallbox reports that a car is plugged in.

I could imagine several intervals:

1. Interval, for example, hourly.
2. Interval when the car reports that it is plugged in, for example, every 30 minutes.
3. Interval when the car is charging, then, for example, every 15 minutes.

And then triggered by connecting to the wallbox (possibly an external switch). Pulse after 2 minutes, 5 minutes, and 10 minutes.

### Comment 9 ([user]):

In ioBroker E.g. the Poll is set to every 6 Minutes.
Works fine.
I'll stop ioBroker & start HA, the error comes up after a view minutes.
The HA Integration wont work for me.

### Comment 10 ([user]):

There hasn't been any activity on this issue recently. Due to the high number of incoming GitHub notifications, we have to clean some of the old issues, as many of them have already been resolved with the latest updates.
Please make sure to update to the latest Home Assistant version and check if that solves the issue. Let us know if that works for you by adding a comment 👍
This issue has now been marked as stale and will be closed if no further activity occurs. Thank you for your contributions.

## PR Review Comments

**[user]** on `homeassistant/components/renault/const.py`:

Please keep this for now

**[user]** on `homeassistant/components/renault/const.py`:

Please remove this and keep for a follow-up PR

**[user]** on `homeassistant/components/renault/coordinator.py`:

Not needed - we have a `self.logger` property in the coordinator

**[user]** on `homeassistant/components/renault/coordinator.py`:

Please rename
```suggestion
        if self._hub.is_throttled():
```

**[user]** on `homeassistant/components/renault/coordinator.py`:

```suggestion
            # coordinator. last_update_success should still be ok
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
