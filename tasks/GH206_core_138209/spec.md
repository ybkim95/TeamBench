# GH206_core_138209: Fix generic_thermostat so it doesn't turn on when current temp is within target temp range — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/home-assistant/core/issues/79667
- Repo: https://github.com/home-assistant/core

## Issue Description

### The problem

Generic Thermostat - cycles if both tolerances are zero and the current temperature = target temperature.

I am using the Generic Thermostat to control my UFH. I want the thermostat to turn the heating off when at target temp, and turn it on when it falls below target temp by 0.1 degrees.

https://github.com/home-assistant/core/blob/41d2ab5b375564ccbc836736fa8896a758cffc2e/homeassistant/components/generic_thermostat/climate.py#L479-L480

If the hot and cold tolerances are 0 (zero), both `too_cold` and `too_hot` evaluate to `True` when `current temp = target temp`.

This results in the thermostat cycling (while current temp = target temp) at the min cycle rate.

https://github.com/home-assistant/core/blob/41d2ab5b375564ccbc836736fa8896a758cffc2e/homeassistant/components/generic_thermostat/climate.py#L482-L482

https://github.com/home-assistant/core/blob/41d2ab5b375564ccbc836736fa8896a758cffc2e/homeassistant/components/generic_thermostat/climate.py#L493-L493

Example: - if the room is currently at 20.5 with heating off and a schedule sets the target temperature to 20.5, the heating will needlessly come on.

### What version of Home Assistant Core has the issue?

2022.9.7

### What was the last working version of Home Assistant Core?

_No response_

### What type of installation are you running?

Home Assistant OS

### Integration causing the issue

Generic Thermostat

### Link to integration documentation on our website

https://www.home-assistant.io/integrations/generic_thermostat/

### Diagnostics information

_No response_

### Example YAML snippet

```yaml
- platform: generic_thermostat
  name: sunroom
  heater: switch.tasmota4
  target_sensor: sensor.sunroomtemp
  min_temp: 18
  max_temp: 22
  cold_tolerance: 0.0
  hot_tolerance: 0.0
  precision: 0.1
  min_cycle_duration:
    minutes: 10
  initial_hvac_mode : "heat"
  away_temp: 16
```

### Anything in the logs that might be useful for us?

_No response_

### Additional information

Solution: add an extra condition such that if both `too_hot` and `too_cold` are true, the device is always switched off or if already off no action.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

[generic_thermostat documentation](https://www.home-assistant.io/integrations/generic_thermostat)
[generic_thermostat source](https://github.com/home-assistant/core/tree/dev/homeassistant/components/generic_thermostat)

### Comment 2 ([user]):

Anyone?

### Comment 3 ([user]):

Anyone? 😄

### Comment 4 ([user]):

Just preventing this going stale.

### Comment 5 ([user]):

Thoughts?

### Comment 6 ([user]):

Please don't go stale

### Comment 7 ([user]):

Still an issue

### Comment 8 ([user]):

There hasn't been any activity on this issue recently. Due to the high number of incoming GitHub notifications, we have to clean some of the old issues, as many of them have already been resolved with the latest updates.
Please make sure to update to the latest Home Assistant version and check if that solves the issue. Let us know if that works for you by adding a comment 👍
This issue has now been marked as stale and will be closed if no further activity occurs. Thank you for your contributions.

### Comment 9 ([user]):

Still an Issue

https://github.com/home-assistant/core/blob/e904edb12e7ff5b96ee86741fcb52bffd72fc498/homeassistant/components/generic_thermostat/climate.py#L484

### Comment 10 ([user]):

There hasn't been any activity on this issue recently. Due to the high number of incoming GitHub notifications, we have to clean some of the old issues, as many of them have already been resolved with the latest updates.
Please make sure to update to the latest Home Assistant version and check if that solves the issue. Let us know if that works for you by adding a comment 👍
This issue has now been marked as stale and will be closed if no further activity occurs. Thank you for your contributions.

## PR Review Comments

**[user]** on `homeassistant/components/generic_thermostat/climate.py`:

I'm not sure your explanation in the docs is correct.

*if the target temperature is 25 and the tolerance is 0.5 the heater will start when the sensor goes below 24.5.",*

`cold_tolerance` in heating mode does nothing to turn the device on (but I think it should).

In heating mode, if target is 25 and `hot_tolerance` is 0.5, `max_temp` is 25.5, so when `curr_temp` drops below 25.5, the device will switch on (currently). I think this should be the `min_temp` that `curr_temp` is compared to i.e. switch on, when the  temperature is below the minimum allowed temperature.

Equally, in AC mode turn the device on, when it exceeds `max_temp`.

**[user]** on `homeassistant/components/generic_thermostat/climate.py`:

I only removed "or equal to" from the existing text in the documents. I am still trying to find a bit of time to think over the logic to try and get it right. I'm sure it's simple, but the way it was effectively made the cold/heat tolerance create a dead-zone - but my code changes caused that to not work.

I agree that there should be a dead-zone by definition of the tolerances... it's just making sure all test cases pass :smile:

**[user]** on `homeassistant/components/generic_thermostat/climate.py`:

If you look at the existing logic, in one case in heating mode, it compares against `too_cold` and in the other `too_hot`. In both your cases you compare to `max_temp` (when heating) and that isn't correct.

In heating you turn off at the maximum allowed temp and turn on at the minimum allowed temp. This creates the 'dead' zone.

Making one a `>=` and the other just a `<` comparator solves my issue in that when `curr` = `target` the system currently cycles `on` and `off` when tolerances are both zero.

**[user]** on `homeassistant/components/generic_thermostat/climate.py`:

Thank you for that - I knew something was off but was probably tired when writing the code. I have it working now. Again though, I've got a lot of things going on (personally) and trying to think of some test cases for this.

So far, I can only think of:

1) if the switch is on and the current temp == target temp, the switch should NOT switch off
2) if the switch is off and the current temp == target temp, the switch should NOT switch on

Basically, the switch shouldn't change if the current temp == target temp and you have zero tolerances.

Are there any other test cases unique to this situation I can test for that you can think of?

**[user]** on `homeassistant/components/generic_thermostat/climate.py`:

> So far, I can only think of:
> 
> 1. if the switch is on and the current temp == target temp, the switch should NOT switch off
> 2. if the switch is off and the current temp == target temp, the switch should NOT switch on
> 
> Basically, the switch shouldn't change if the current temp == target temp and you have zero tolerances.

No. - think about it, if you were manually turning it on and off, you want it to turn off when it reaches it's maximum allowed temp and turn on when it reaches the minimum allowed temperature.

For heating with zero tolerances -
1. If on, when current equals or exceeds the maximum, turn off
2. If off when current equals the maximum, stay off (do nothing)
3. If off when less than minimum turn on. Note - arguably when it is equal to the minimum turn on **but** if min and max are the same (zero tolerances) you get what you have now and the system cycles.

If you want to turn on when current equals the minimum, when max and min are the same (zero tolerances) you will need a special case and it cannot be handled by a generic condition.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
