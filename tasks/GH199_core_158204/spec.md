# GH199_core_158204: Fix rain count sensors' state class of Ecowitt — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/home-assistant/core/issues/157882
- Repo: https://github.com/home-assistant/core

## Issue Description

### The problem

Just updated to HAOS 2025.12 and got these notifications for my GW2000B sensors:

> The entity no longer has a state class
> 
> We have generated statistics for 'Ecowitt Event Rain Piezo' (sensor.gw2000b_event_rain_piezo) in the past, but it no longer has a state class, therefore, we cannot track long term statistics for it anymore.
> 
> Statistics cannot be generated until this entity has a supported state class.
> 
>     If the state class was previously provided by an integration, this might be a bug. Please report an issue.
>     If you previously set the state class yourself, please correct it. The different state classes and when to use which can be found in the developer documentation.
>     If the state class has permanently been removed, you may want to delete the long term statistics of it from your database.
> 
> Do you want to permanently delete the long term statistics of sensor.gw2000b_event_rain_piezo from your database?

### What version of Home Assistant Core has the issue?

core-2025.12.0

### What was the last working version of Home Assistant Core?

_No response_

### What type of installation are you running?

Home Assistant OS

### Integration causing the issue

Ecowitt

### Link to integration documentation on our website

https://www.home-assistant.io/integrations/ecowitt/

### Diagnostics information

_No response_

### Example YAML snippet

```yaml

```

### Anything in the logs that might be useful for us?

```txt

```

### Additional information

<img width="615" height="571" alt="Image" src="https://github.com/user-attachments/assets/62431a08-aa56-474c-80b1-23f41bc214a9" />

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hey there [user], mind taking a look at this issue as it has been labeled with an integration (`ecowitt`) you are listed as a [code owner](https://github.com/home-assistant/core/blob/dev/CODEOWNERS#L416) for? Thanks!

<details>
<summary>Code owner commands</summary>

Code owners of `ecowitt` can trigger bot actions by commenting:

- `@home-assistant close` Closes the issue.
- `@home-assistant rename Awesome new title` Renames the issue.
- `@home-assistant reopen` Reopen the issue.
- `@home-assistant unassign ecowitt` Removes the current integration label and assignees on the issue, add the integration domain after the command.
- `@home-assistant add-label needs-more-information` Add a label (needs-more-information, problem in dependency, problem in custom component) to the issue.
- `@home-assistant remove-label needs-more-information` Remove a label (needs-more-information, problem in dependency, problem in custom component) on the issue.

</details>

<sub><sup>(message by CodeOwnersMention)</sup></sub>

---

[ecowitt documentation](https://www.home-assistant.io/integrations/ecowitt)
[ecowitt source](https://github.com/home-assistant/core/tree/dev/homeassistant/components/ecowitt)
<sub><sup>(message by IssueLinks)</sup></sub>

### Comment 2 ([user]):

This is correct.
The invalid state class was removed.
You can follow the tepair process, and delete the long term statistics.

### Comment 3 ([user]):

Thank you for verifying!

### Comment 4 ([user]):

Hi [user] 

I have the same message for my GW2000A, in case I proceed with the repair as suggested above, am I still gonna have the long term statistics for my rain history in any ways? 
In the 'States' sections currently I don't see any 'state classes' to my rain sensors, and I thought this is mandatory to have the long term statistics in home assistant.
Many thanks

<img width="623" height="386" alt="Image" src="https://github.com/user-attachments/assets/d63619ab-8e23-4a96-958a-a974572ca688" />

### Comment 5 ([user]):

The state class was only removed from rolling window sensors.
The state class for "lifetime total" was not removed.

See #157409 and #155812

### Comment 6 ([user]):

> The state class was only removed from rolling window sensors. The state class for "lifetime total" was not removed.
> 
> See [#157409]((withheld: the upstream fix is not part of the task)) and [#155812]((withheld: the upstream fix is not part of the task))

Hi, unfortunatelly this is not the case, the state class attribute is now removed for all of my rain sensors, and I'm worried that I'm loosing the long term history if I proceed with the repair

<img width="538" height="278" alt="Image" src="https://github.com/user-attachments/assets/ad73cfa9-ff71-4934-aea3-9247fffea886" />

### Comment 7 ([user]):

[user] , i do not have any rolling windows from ecowitt, but all rain sensors are screaming now

<img width="680" height="605" alt="Image" src="https://github.com/user-attachments/assets/567020fa-e1e7-488c-807d-c94acc78336d" />

### Comment 8 ([user]):

"yearly" "monthly" "weekly", etc. are rolling windows.
The state class was invalid - it has been removed.

You need to follow the repair process, and delete the long term statistics for these sensors.

### Comment 9 ([user]):

> "yearly" "monthly" "weekly", etc. are rolling windows.

[user] any chance you can clarify the difference between a rolling window and a (resetting) total? 

Daily, Weekly, Monthly and Yearly rain totals accumulate until the reset point (1st hour of day, day of week, month and year). 

They do **not** report the rain for the previous 365 days, 30 days or 24 hours. 

They are resetting totals. 

See history chart in https://github.com/home-assistant/core/issues/157903 where you can see the resets. 

Attached is another example of Weekly and Monthly rain showing the resets. 

An explanation would be of great assistance. 

![Screenshot_20251204_220814_Home Assistant.jpg](https://github.com/user-attachments/assets/7bab5cab-5dc0-488f-8eb7-17fdeec7dd84)

### Comment 10 ([user]):

It appears that this "repair" simply deletes all historic data. I tried one repair on daily rain rate and where I used to have years of data, I now have 10 days. Is that the expected outcome of the repair?

## PR Review Comments

**[user]** on `homeassistant/components/ecowitt/sensor.py`:

This logic for detecting and overriding state classes for rolling window sensors lacks test coverage. Given the critical nature of state class assignments for long-term statistics (as mentioned in the PR description), tests should be added to verify:
1. Rolling window sensors (matching the regex) correctly get MEASUREMENT state class
2. Non-rolling window rain count sensors correctly retain TOTAL_INCREASING state class
3. The regex pattern matches all expected sensor key formats (hourlyrainmm, hourlyrainin, last24hrainmm, last24hrainin, hrain_piezo variants, etc.)

Consider adding tests in `tests/components/ecowitt/test_sensor.py` following the Home Assistant testing patterns with fixtures and snapshots.

**[user]** on `homeassistant/components/ecowitt/sensor.py`:

[nitpick] Consider using a raw string (r"...") for the regex pattern to improve readability and make escape sequences more explicit. Also, adding parentheses around the entire alternation could make the pattern structure clearer:

```python
_ROLLING_WINDOW_RAIN_COUNT_SENSOR = re.compile(
    r"(?:hourly|last24h)rain(?:in|mm)|(?:last24)?hrain_piezo(?:mm)?"
)
```

This doesn't change functionality but improves code maintainability.
```suggestion
    r"((?:hourly|last24h)rain(?:in|mm)|(?:last24)?hrain_piezo(?:mm)?)"
```

**[user]** on `homeassistant/components/ecowitt/sensor.py`:

The comment mentions "Hourly and 24h rain count sensors" but the regex also matches piezo rain sensor variants (`hrain_piezo`, `last24hrain_piezo`). Consider updating the comment to be more comprehensive:

```python
# Hourly, 24h, and piezo rain count sensors are rolling window sensors
```

This makes it clearer that piezo sensors are also included in the pattern.
```suggestion
# Hourly, 24h, and piezo rain count sensors are rolling window sensors
```

**[user]** on `homeassistant/components/ecowitt/sensor.py`:

There is nothing need to be escaped, so raw string isn't useful.

**[user]** on `homeassistant/components/ecowitt/sensor.py`:

Whether the data comes from piezo or not is orthogonal to whether its time period is hourly or 24h.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
