# GH230_core_163096: dwd_weather_warnings: Filter expired warnings — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/home-assistant/core/issues/150737
- Repo: https://github.com/home-assistant/core

## Issue Description

### The problem

This is probably the same problem as https://github.com/home-assistant/core/issues/103352:

Even though the weather warning expired yesterday, the sensor does not reset. Both the map on dwd.de and the app no longer have the warning.

From the conversation on the earlier issue I constructed this URL, which indeed returns the warning as of now:
[maps.dwd.de API call](https://maps.dwd.de/geoserver/dwd/ows?service=WFS&version=2.0.0&request=GetFeature&typeName=dwd%3AWarnungen_Landkreise&CQL_FILTER=GC_WARNCELLID%3D%27114511000%27&OutputFormat=application/json) / [JSON data that is returned currently](https://github.com/user-attachments/files/21810850/dwd-20250816.json)

While I understand being hesitant of implementing additional logic, the returned data clearly includes
`"EXPIRES":"2025-08-15T17:00:00Z"` which both is easily machine parseable and expresses an explicit intent.

I can contribute a PR that filters on this field but would like some feedback on how you would like to treat this issue.

Thanks!

### What version of Home Assistant Core has the issue?

core-2025.8.1

### What was the last working version of Home Assistant Core?

_No response_

### What type of installation are you running?

Home Assistant Container

### Integration causing the issue

dwd_weather_warnings

### Link to integration documentation on our website

https://www.home-assistant.io/integrations/dwd_weather_warnings/

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

Hey there [user], [user], [user], mind taking a look at this issue as it has been labeled with an integration (`dwd_weather_warnings`) you are listed as a [code owner](https://github.com/home-assistant/core/blob/dev/CODEOWNERS#L386) for? Thanks!

<details>
<summary>Code owner commands</summary>

Code owners of `dwd_weather_warnings` can trigger bot actions by commenting:

- `@home-assistant close` Closes the issue.
- `@home-assistant rename Awesome new title` Renames the issue.
- `@home-assistant reopen` Reopen the issue.
- `@home-assistant unassign dwd_weather_warnings` Removes the current integration label and assignees on the issue, add the integration domain after the command.
- `@home-assistant add-label needs-more-information` Add a label (needs-more-information, problem in dependency, problem in custom component) to the issue.
- `@home-assistant remove-label needs-more-information` Remove a label (needs-more-information, problem in dependency, problem in custom component) on the issue.

</details>

<sub><sup>(message by CodeOwnersMention)</sup></sub>

---

[dwd_weather_warnings documentation](https://www.home-assistant.io/integrations/dwd_weather_warnings)
[dwd_weather_warnings source](https://github.com/home-assistant/core/tree/dev/homeassistant/components/dwd_weather_warnings)
<sub><sup>(message by IssueLinks)</sup></sub>

### Comment 2 ([user]):

Yes, I would appreciate a solution for this as well.
For now I added a condition to my Automations based on a Template sensor I created which goes negative once the Warning end is before current time.

`{{
        ((as_timestamp(state_attr("sensor.region_hannover_aktuelle_warnstufe",
        "warning_1_end")) - as_timestamp(now()))) | int(0) }}`

which is  most likely not the most elegant way, but hopefully it works ;-)
I first tried to build a condition right on the attribute "warning_1_end", however couldn't find out how to.

### Comment 3 ([user]):

Didn't have the time to look too much into it but the underlying library we use for this (https://github.com/stephan192/dwdwfsapi) already uses the `EXPIRES` property for the end time attribute of a warning: https://github.com/stephan192/dwdwfsapi/blob/master/src/dwdwfsapi/weatherwarnings.py#L44-L48

With the way the update routine of the library seems to work, the currently saved warnings are reset using the new result from the DWD request. So it **could** be an issue on DWD side.

Filtering out warnings that are already in the past, as you suggested, could be a workaround for issues on DWD side though in my opinion.

### Comment 4 ([user]):

Like already noted in #103352. This looks neither as an error of the weather warnings integration nor the used dwdwfsapi, fixing it here is the wrong place. Maybe someone contacts DWD again.

### Comment 5 ([user]):

That’s what I assumed, however the fact, that those errors might occur on DWD  sites makes me think that a workaround as mentioned above makes generally sense. However, maybe someone find a smoother solution

### Comment 6 ([user]):

I'm not sure if the DWD api is supposed to return these warnings or not – looking through the linked documentation I could not find any assurance about what warnings are supposed to be returned. Maybe some history is by design, I can't tell.

All I know is that for me this happens frequently and it is annoying, because weather warnings are shown prominently throughout my house. This seems to happen to other users as well so at least for the purposes of this integration, I think it is fair to be considered a bug.

DWD was apparently notified years ago, but they have not taken steps to permanently filter out these events (again, I am not sure if that is what they want).

My proposed solution is here: https://github.com/tribut/home-assistant/commits/dwd_expired/
Given that there seems to be some opposition to fixing the problem here, I will wait for a signal that it could be merged before taking the time to prepare a formal PR. I would certainly appreciate this problem being fixed here.

### Comment 7 ([user]):

[user] i get your point, but due to the fact that we don't know all use cases and to be backward compatible you should add a new value to the config flow. I suggest a checkbox named "filter expired warnings" with default=disabled. So we would be 100% backward compatible and get the new feature in addition.

### Comment 8 ([user]):

I would highly appreciate such a feature

### Comment 9 ([user]):

[user] Agree. I've added the checkbox in the same branch. Will need to find some time to add tests before this is ready.

### Comment 10 ([user]):

There hasn't been any activity on this issue recently. Due to the high number of incoming GitHub notifications, we have to clean some of the old issues, as many of them have already been resolved with the latest updates.
Please make sure to update to the latest Home Assistant version and check if that solves the issue. Let us know if that works for you by adding a comment 👍
This issue has now been marked as stale and will be closed if no further activity occurs. Thank you for your contributions.

## PR Review Comments

**[user]** on `homeassistant/components/dwd_weather_warnings/sensor.py`:

The _filter_expired_warnings method is missing type hints. Add type annotations for both the parameter and return value to maintain consistency with Home Assistant's strict typing requirements.

Change the method signature to:
def _filter_expired_warnings(self, warnings: list[dict[str, Any]]) -> list[dict[str, Any]]:

**[user]** on `homeassistant/components/dwd_weather_warnings/sensor.py`:

The _filter_expired_warnings method doesn't handle the case where warnings could be None. If the coordinator's API returns None for current_warnings or expected_warnings, this will cause a TypeError when attempting to iterate over None.

Add a None check at the beginning of the method:
if warnings is None:
    return []

**[user]** on `tests/components/dwd_weather_warnings/test_init.py`:

This test claims to verify filtering “depending on option state”, but it only covers a single behavior and does not set any config entry options. If filtering is meant to be optional/off by default (per PR description), add coverage for both enabled and disabled states (e.g., parametrized test asserting level/count differ) and set the option explicitly in the `MockConfigEntry`.

**[user]** on `homeassistant/components/dwd_weather_warnings/sensor.py`:

`_filter_expired_warnings` keeps warnings that do not contain `end_time`, but `extra_state_attributes` later indexes `warning[API_ATTR_WARNING_END]` unconditionally. If the API ever returns a warning without `end_time`, this will raise a `KeyError` and break attribute/state updates. Either exclude warnings missing `end_time` in the filter or use `.get()`/fallbacks when building attributes (and ensure `warning_copy` handles a missing end too).
```suggestion
            if API_ATTR_WARNING_END in warning
            and warning[API_ATTR_WARNING_END] > now
```

**[user]** on `homeassistant/components/dwd_weather_warnings/sensor.py`:

The filtering is applied unconditionally in `native_value` and `extra_state_attributes`, but the PR description says expired-warning filtering is optional and off by default. If this behavior is intended to be configurable, gate the call to `_filter_expired_warnings` behind a config entry option (with a default that preserves current behavior) and ensure the option is exposed via an options flow.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
