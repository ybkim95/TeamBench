# GH208_core_129066: Fix race condition in statistics that created spikes — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/home-assistant/core/issues/119738
- Repo: https://github.com/home-assistant/core

## Issue Description

### The problem

I have created a number of statistics entities with long time periods (days or weeks) which are getting corrupted when HA restarts.  Looking at their graphs I see large spikes around the time of a restart. E.g.:
![Screenshot (14)](https://github.com/home-assistant/core/assets/114306651/0cf68372-6e02-4351-b1b5-b9c3d1081d79)

The source sensor does not show any discontinuity at the restart:
![Screenshot (15)](https://github.com/home-assistant/core/assets/114306651/ee02f8e4-24e3-4ade-91ee-b8d37a6ba407)

### What version of Home Assistant Core has the issue?

core-2024.6.2

### What was the last working version of Home Assistant Core?

_No response_

### What type of installation are you running?

Home Assistant OS

### Integration causing the issue

Statistics

### Link to integration documentation on our website

_No response_

### Diagnostics information

_No response_

### Example YAML snippet

```yaml
- platform: statistics
    name: wind_60hr
    unique_id: wind_60hr
    entity_id: sensor.wind_display
    state_characteristic: average_linear
    precision: 2
    max_age:
      hours: 60
```

### Anything in the logs that might be useful for us?

_No response_

### Additional information

Exactly this issue has been previously raised https://github.com/home-assistant/core/issues/89000 but went stale
I have reported details https://community.home-assistant.io/t/corruption-in-long-period-statistics-sensors-at-ha-re-starts/739113

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hey there [user], mind taking a look at this issue as it has been labeled with an integration (`statistics`) you are listed as a [code owner](https://github.com/home-assistant/core/blob/dev/CODEOWNERS#L1341) for? Thanks!

<details>
<summary>Code owner commands</summary>

Code owners of `statistics` can trigger bot actions by commenting:

- `@home-assistant close` Closes the issue.
- `@home-assistant rename Awesome new title` Renames the issue.
- `@home-assistant reopen` Reopen the issue.
- `@home-assistant unassign statistics` Removes the current integration label and assignees on the issue, add the integration domain after the command.
- `@home-assistant add-label needs-more-information` Add a label (needs-more-information, problem in dependency, problem in custom component) to the issue.
- `@home-assistant remove-label needs-more-information` Remove a label (needs-more-information, problem in dependency, problem in custom component) on the issue.

</details>

<sub><sup>(message by CodeOwnersMention)</sup></sub>

---

[statistics documentation](https://www.home-assistant.io/integrations/statistics)
[statistics source](https://github.com/home-assistant/core/tree/dev/homeassistant/components/statistics)
<sub><sup>(message by IssueLinks)</sup></sub>

### Comment 2 ([user]):

I also have this sometimes after a restart But not for every restart. First time I noticed was after my update to 2024.7.
But (for me) it also can happen when just reloading the statistics yaml in Dev Tools (as reported by someone else in [the stale issue](https://github.com/home-assistant/core/issues/89000)). 

That a reload can trigger this, basically excludes a missing source sensor as a cause. During reload the source remained present.

Just an example, where the source sensor remained nearly zero, but the statistics daily average sensor spikes between +31k and -31k when  I reloaded the statistics yaml config. Note I reloaded 3-4 times in a row but just one spiked:

![image](https://github.com/user-attachments/assets/9b245b5e-c925-45fb-98b7-e40d5f2662cd)

Sensor config:
``` 
  - platform: statistics
    name: "PM2.5 daily average"
    unique_id: pm2_5_daily_average
    entity_id: sensor.apollo_air_1_c1c714_pm_2_5_m_weight_concentration
    state_characteristic: average_linear
    max_age:
      hours: 24
``` 

At the same time, a 15 minute average sensor for the same source sensor spiked as well. But lower values and first negative and then positive:
![image](https://github.com/user-attachments/assets/6da3de4f-2e86-4510-92d4-797b15180f47)

Update: Someone in the forums suggested that the spike size seems to correlate with max_age. That is what I see as well

### Comment 3 ([user]):

Seems somewhat related so I'll add here: I see spikes all over the place, without HA restart, in different stats (linear average, minimum), where apparently 2 different values are recorded by statistics at the same timestamp:

<img width="754" alt="image" src="https://github.com/user-attachments/assets/e218d27c-33a1-43c6-8870-5d315234a6c6">

### Comment 4 ([user]):

I have also seen those spikes and didn't see any reason for them in my source data. I'm pretty sure that this happens because an undefined value is incorrectly being interpreted as MAX_INT or something and then getting into the calculation when the system is restarted.

I moved away from the statistics / average_step because of this. Currently I am using filters instead, which at least don't give me any spikes.

Both options have the annoying habit of becoming "undefined" when the value is stable for a long time. Currently, I am countering that with a template that is switching between the computed average and the actual source value depending on how long the value remains stable.

This is pretty annoying because it means copying the same code again and again. It would be great if this functionality would be part of the integration itself.

Sensor:
```
- platform: filter
  name: "inverter_grid_export_avg_30"
  entity_id: sensor.inverter_grid_export
  filters:
    - filter: time_simple_moving_average
      window_size: 00:00:30
```

Template:
```
- trigger:
    - platform: state
      entity_id:
        - sensor.inverter_grid_export_avg_30
- sensor:
    - name: "inverter_grid_export_avg"
      unit_of_measurement: 'W'
      state_class: measurement
      icon: mdi:transmission-tower-export
      availability: "{{ (states('sensor.inverter_grid_export_avg_30') | is_number) or (states('sensor.inverter_grid_export') | is_number) }}"
      state: >   
        {% set avg_30 = states('sensor.inverter_grid_export_avg_30') | float(0) %}
        {% set current = states('sensor.inverter_grid_export') | float(0) %}
        {% if (state_attr('sensor.inverter_grid_export', 'last_changed') == none) %}
          {% set last_changed = 0 %}
        {% else %}
          {% set last_changed = (now() - states.sensor.inverter_grid_export.last_changed).total_seconds() | int(0) %}
        {% endif %}
        {% if (last_changed <= 30) %} 
          {{ avg_30 }}
        {% else %}
          {{ current }}
        {% endif %}
```

### Comment 5 ([user]):

I am also facing this problem. I would love to not have to solve this in convoluted ways with filters and templates. 
![image](https://github.com/user-attachments/assets/d427d860-8a3f-4bbd-bdd5-5f2edb904bc5)

Any way to bring this thread to the attention of some devs?

### Comment 6 ([user]):

I just noticed that it is only my statistic helpers that have a value measured in kW. The statistics that use W, deg C or PPM are not affected by the restart.

### Comment 7 ([user]):

I have found a solution that will trigger a computation of the statistics values, even if the input value is stable. It was also mentioned in another thread here somewhere.

`
      # adding this will make sure the value is changing and hence the statistics are recomputed
      attributes:
        update_trigger: "{{ now().microsecond }}"
`

Adding such an attribute will change the state of a sensor whenever it is computed. Any statistic based on that sensor would then also be recomputed. I like this solution better than having to create a lot of otherwise useless sensors and it produces a lot less code.

This is definitely a workaround for the issue that statistics are not recomputed when the actual value is stable for longer times.

I'm still using statistics in a few places and I don't see the spikes anymore (min and max, not average). I'm not sure whether this is just a coincidence, since I made a couple of other changes as well.

### Comment 8 ([user]):

Hey everyone,
I am the main developer of the statistics component and while I would love to resolve this issue, I am not in the position to invest any significant work the next couple of months... Sadly. I would love to review a PR by one of you guys though. Just fyi, I think the first change that should be implemented is to switch from the change event to the newly introduced update event. That was indeed introduced because myself and others asked for it.

Btw I was planning to release a "custom component" to accelerate the development of a "statistics beta" component.

### Comment 9 ([user]):

I have started to fix the issues and will soon create a merge request.

I have solved or am on the was of solving the following issues:

- the time based average functions are now including the values before and after the last change (average step / linear), this is in particular relevant when values stay stable for a longer time
- many functions that currently require at least two values to work, can now work with a single value as well (e.g. simple average)
- the peaks will be a thing of the past (they happen because the value sequence is not correctly ordered according to time stamps)
- I will also try to add a refresh trigger, so that the average can be recomputed even if the inputs didn't change

### Comment 10 ([user]):

Thank you for your efforts – it would be so good to get back to using this integration.  Whilst you are looking at it, is there any way to define a period for the statistic; by both its start (done), but also by its end or length in time (only sample size currently allowed)?

 

Cheers,

David Inwood

 

From: unfug-at-github ***@***.***> 
Sent: Saturday, August 24, 2024 10:47 AM
To: home-assistant/core ***@***.***>
Cc: Dtrotmw ***@***.***>; Author ***@***.***>
Subject: Re: [home-assistant/core] Spikes in statistics averages when HA restarts (Issue #119738)

 

I have started to fix the issues and will soon create a merge request.

I have solved or am on the was of solving the following issues:

*	the time based average functions are now including the values before and after the last change (average step / linear), this is in particular relevant when values stay stable for a longer time
*	many functions that currently require at least two values to work, can now work with a single value as well (e.g. simple average)
*	the peaks will be a thing of the past (they happen because the value sequence is not correctly ordered according to time stamps)
*	I will also try to add a refresh trigger, so that the average can be recomputed even if the inputs didn't change

—
Reply to this email directly, view it on GitHub <https://github.com/home-assistant/core/issues/119738#issuecomment-2308279771> , or unsubscribe <https://github.com/notifications/unsubscribe-auth/A3IC4W2LTSJ4T26SB3OOQ23ZTBJBDAVCNFSM6AAAAABJLVYWCSVHI2DSMVQWIX3LMV43OSLTON2WKQ3PNVWWK3TUHMZDGMBYGI3TSNZXGE> .
You are receiving this because you authored the thread.  <https://github.com/notifications/beacon/A3IC4W5EY2PAZ47DZVAFWRLZTBJBDA5CNFSM6AAAAABJLVYWCSWGG33NNVSW45C7OR4XAZNMJFZXG5LFINXW23LFNZ2KUY3PNVWWK3TUL5UWJTUJSWG5W.gif> Message ID: ***@***.*** ***@***.***> >

## PR Review Comments

**[user]** on `tests/components/statistics/test_sensor.py`:

Am I missing something or is this not the opposite of what should happen?
It should grab all the relevant states from the recorder and then start collecting state changes from events?

**[user]** on `tests/components/statistics/test_sensor.py`:

Currently, we have a race condition. New values are added to the queue before the values loaded from the database were loaded. As [user] proposed we are now accepting new values only after loading data from the database succeeded. This means that whatever comes in before will be ignored.

**[user]** on `tests/components/statistics/test_sensor.py`:

Double?

**[user]** on `tests/components/statistics/test_sensor.py`:

Hey [user] could it be that this test case wrongly succeeds because you are using `average_step`? Will it start to fail if you switch to `mean`?

**[user]** on `tests/components/statistics/test_sensor.py`:

It will fail if you switch to mean without changing the value as well. The mean of [1 .. 9] is 5 (= (1+2+3+4+5+6+7+8+9)/9), whereas average_step computes 4.5 (= (1+2+3+4+5+6+7+8)/8). With average_step the last value is not affecting the computation.

The important part is in both cases the value 10 that is added before the database finishes loading doesn't make it into the computation (otherwise the mean would be 5.5, and average_step 5).

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
