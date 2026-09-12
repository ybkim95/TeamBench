# GH210_core_147527: Recalculate derivative unit correctly when source or options change — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/home-assistant/core/issues/136419
- Repo: https://github.com/home-assistant/core

## Issue Description

### The problem

Hi

I have created a Derivative sensor with time unit hour.
But the sensor shows the unit in per Minute.

I have this problem described in this issue https://github.com/home-assistant/core/issues/95666

But that was closed without any fix or solution

### What version of Home Assistant Core has the issue?

core-2025.1.3

### What was the last working version of Home Assistant Core?

_No response_

### What type of installation are you running?

Home Assistant OS

### Integration causing the issue

Helper derivate 

### Link to integration documentation on our website

_No response_

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

Hey there [user], mind taking a look at this issue as it has been labeled with an integration (`derivative`) you are listed as a [code owner](https://github.com/home-assistant/core/blob/dev/CODEOWNERS#L321) for? Thanks!

<details>
<summary>Code owner commands</summary>

Code owners of `derivative` can trigger bot actions by commenting:

- `@home-assistant close` Closes the issue.
- `@home-assistant rename Awesome new title` Renames the issue.
- `@home-assistant reopen` Reopen the issue.
- `@home-assistant unassign derivative` Removes the current integration label and assignees on the issue, add the integration domain after the command.
- `@home-assistant add-label needs-more-information` Add a label (needs-more-information, problem in dependency, problem in custom component) to the issue.
- `@home-assistant remove-label needs-more-information` Remove a label (needs-more-information, problem in dependency, problem in custom component) on the issue.

</details>

<sub><sup>(message by CodeOwnersMention)</sup></sub>

---

[derivative documentation](https://www.home-assistant.io/integrations/derivative)
[derivative source](https://github.com/home-assistant/core/tree/dev/homeassistant/components/derivative)
<sub><sup>(message by IssueLinks)</sup></sub>

### Comment 2 ([user]):

I believe something is wrong with the derivative sensor units. I created a sensor using the "Mega" prefix on a base sensor in MB/s, and it showed MMB/s. Now it is stuck with this unit even changing the prefix, and the scale of the chart is completely off.

The download in this picture was at 26MB/s
![Image](https://github.com/user-attachments/assets/f04b2584-b18b-4fcf-8194-3df8e7997403)

Any idea, while we wait for a fix, if this behavior can be changed manually in the configuration files?

### Comment 3 ([user]):

In my case the derivative sensor unit lacks (/) symbol. %min instead of %/min

![Image](https://github.com/user-attachments/assets/9322b215-acc8-4bad-8b7c-d877df63caa9)

### Comment 4 ([user]):

There hasn't been any activity on this issue recently. Due to the high number of incoming GitHub notifications, we have to clean some of the old issues, as many of them have already been resolved with the latest updates.
Please make sure to update to the latest Home Assistant version and check if that solves the issue. Let us know if that works for you by adding a comment 👍
This issue has now been marked as stale and will be closed if no further activity occurs. Thank you for your contributions.

### Comment 5 ([user]):

Still an issue as of 5/19/25

### Comment 6 ([user]):

Still an issue as of 5/25/25. Timeunit doesn't change anything.

I have not idea about python programming but with the help of chatgpt I copyed the derivative implementation 1:1 as a custom component and changed.

```
if self.native_unit_of_measurement is None:
        unit = new_state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        self._attr_native_unit_of_measurement = self._unit_template.format(
            "" if unit is None else unit
        )
```
to
```
#if self.native_unit_of_measurement is None:
unit = new_state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
self._attr_native_unit_of_measurement = self._unit_template.format(
    "" if unit is None else unit
)
```

Now changing the time unit in the ui is working correctly.

**Explanation from chatgpt**

Likely Cause

The core issue lies in how and when the native_unit_of_measurement is set. This property controls the unit shown in the UI. In your code, it’s only set during:

    Sensor initialization — if unit_of_measurement is provided.

    First sensor update — inside calc_derivative:

    if self.native_unit_of_measurement is None:
        unit = new_state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        self._attr_native_unit_of_measurement = self._unit_template.format(
            "" if unit is None else unit
        )

But this only happens once, when native_unit_of_measurement is None.

### Comment 7 ([user]):

Can confirm this is still an issue in 2025.7.4. I am traveling by car at miraculous speeds of 1700 ft/s (over 1100 mph), as calculated by a derivative of the nearest distance sensor from the Proximity integration. Looks like there's a PR open at least.

### Comment 8 ([user]):

Can confirm this is still an issue in 2025.7.4. I am traveling by car at miraculous speeds of 1700 ft/s (over 1100 mph), as calculated by a derivative of the nearest distance sensor from the Proximity integration. Looks like there's a PR open at least.

### Comment 9 ([user]):

Still an issue on Core 2025.9.1

## PR Review Comments

**[user]** on `homeassistant/components/derivative/sensor.py`:

I added this check for `is_running`, not sure if this is the best approach here. 

We want to restore the unit when we reboot hass, but when user runs an options flow, we also end up here. In that case I _don't_ want to restore the unit from last_sensor_data, because we want to calculate a new unit from the source sensor. 

Not sure if there is a better way to differentiate the two cases.

**[user]** on `homeassistant/components/derivative/sensor.py`:

You could try storing the unit in `options` instead.

**[user]** on `homeassistant/components/derivative/sensor.py`:

I'm not sure I understand what you mean, could you fill out that idea a little bit?

To summarize: 
 - config/options flow picks the `unit_time`
 - We get a UoM from the source sensor as soon as possible.
 - Once we get that, we build the UoM for the derivative as `source UoM / unit_time`
 - When we restore the entity (either on boot or on reload), we restore the UoM. I don't know how to differentiate boot vs reload other than what I've done.
 - I'm looking for a way to clear/reset the stored UoM when we rerun options flow (as we may change the unit_time). Even better would be if we only clear it if the unit_time changes in options flow (and not unrelated options like `name` or something like that). 
 
In what way do you see adding the unit to `config_entry.options` helps the solution?

Thank you.

**[user]** on `homeassistant/components/derivative/sensor.py`:

Catching a SyntaxError here seems inappropriate for errors produced by rounding a Decimal. Consider catching a more relevant exception (such as ValueError or InvalidOperation) to accurately handle conversion errors.
```suggestion
            except (InvalidOperation, DecimalException) as err:
```

**[user]** on `homeassistant/components/derivative/sensor.py`:

When the integration starts, you look in `options` and if the unit is there, you restore it.
You store it there in the first place when your integration detects what it is from the source sensor.
In the options flow you remove it from the `options` / set it to `None`.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
