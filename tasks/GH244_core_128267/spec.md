# GH244_core_128267: Set friendly name of utility meter select entity when configured through YAML — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/home-assistant/core/issues/128198
- Repo: https://github.com/home-assistant/core

## Issue Description

### The problem

I am creating a Utility Meter helper in the configuration.yaml file with the following code.

```yaml
utility_meter:
  energy_grid_import_today:
    name: Energy Grid Import Today
    source: sensor.grid_import_today_f
    cycle: daily
    tariffs:
      - Peak
      - Off-Peak
    unique_id: 22b7da94-805a-4b58-820e-31e6289ba23f
```

The two sensor created for Peak & Off-Peak are named correctly, however the created "Select" entity does not use the Friendly Name. These are the entities created with the above code.

```yaml
energy_grid_import_today
Energy Grid Import Today Peak
Energy Grid Import Today Off-Peak
```

I would have expected "energy_grid_import_today" to be named "Energy Grid Import Today" but its not.

### What version of Home Assistant Core has the issue?

2024.10.2

### What was the last working version of Home Assistant Core?

_No response_

### What type of installation are you running?

Home Assistant Container

### Integration causing the issue

_No response_

### Link to integration documentation on our website

_No response_

### Diagnostics information

_No response_

### Example YAML snippet

```yaml
utility_meter:
  energy_grid_import_today:
    name: Energy Grid Import Today
    source: sensor.grid_import_today_f
    cycle: daily
    tariffs:
      - Peak
      - Off-Peak
    unique_id: 22b7da94-805a-4b58-820e-31e6289ba23f
```

### Anything in the logs that might be useful for us?

_No response_

### Additional information

If I remove the tariffs section, the code will create a sensor with the correct friendly name.

It seems to be an issue when specifying tariffs.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hey there [user], mind taking a look at this issue as it has been labeled with an integration (`utility_meter`) you are listed as a [code owner](https://github.com/home-assistant/core/blob/dev/CODEOWNERS#L1579) for? Thanks!

<details>
<summary>Code owner commands</summary>

Code owners of `utility_meter` can trigger bot actions by commenting:

- `@home-assistant close` Closes the issue.
- `@home-assistant rename Awesome new title` Renames the issue.
- `@home-assistant reopen` Reopen the issue.
- `@home-assistant unassign utility_meter` Removes the current integration label and assignees on the issue, add the integration domain after the command.
- `@home-assistant add-label needs-more-information` Add a label (needs-more-information, problem in dependency, problem in custom component) to the issue.
- `@home-assistant remove-label needs-more-information` Remove a label (needs-more-information, problem in dependency, problem in custom component) on the issue.

</details>

<sub><sup>(message by CodeOwnersMention)</sup></sub>

---

[utility_meter documentation](https://www.home-assistant.io/integrations/utility_meter)
[utility_meter source](https://github.com/home-assistant/core/tree/dev/homeassistant/components/utility_meter)
<sub><sup>(message by IssueLinks)</sup></sub>

### Comment 2 ([user]):

Thanks, the linked PR should address the issue

## PR Review Comments

**[user]** on `homeassistant/components/utility_meter/select.py`:

I am a little confused, the PR is talking about setting a friendly name, but in reality we only set the entity_id to a fixed value. Isn't the solution to set `_attr_has_entity_name = True`?

**[user]** on `homeassistant/components/utility_meter/select.py`:

this line is to avoid a breaking change. 

The most important line in this PR is line 67:

` conf_meter_name = hass.data[DATA_UTILITY][meter].get(CONF_NAME, meter)`

which enables exchanging `meter` (the slug in yaml) for the name configured in YAML

The issue was that this simple change was breaking the entity_id, so I had to include the suggest_entity_id (much like it happens in utility_meter sensor platform)

**[user]** on `homeassistant/components/utility_meter/select.py`:

Does every utility meter have a unique_id?

**[user]** on `homeassistant/components/utility_meter/select.py`:

Config Entry yes, YAML no... (you need to explicitly set it)

**[user]** on `homeassistant/components/utility_meter/select.py`:

Because if you have a unique_id, the entity_id will stay the same. So I am mostly wondering if changes to names count as breaking change when it comes to YAML based integrations (I haven't had those yet and a lot of YAML stuff was before my time)

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
