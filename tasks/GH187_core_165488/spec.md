# GH187_core_165488: Fix optional static values in bsblan — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/home-assistant/core/issues/165319
- Repo: https://github.com/home-assistant/core

## Issue Description

### The problem

Cannot get this integration to work. Getting errors with retreiving data.

### What version of Home Assistant Core has the issue?

2026.3.1

### What was the last working version of Home Assistant Core?

_No response_

### What type of installation are you running?

Home Assistant OS

### Integration causing the issue

BSB-LAN

### Link to integration documentation on our website

_No response_

### Diagnostics information

[home-assistant_bsblan_2026-03-11T07-47-17.444Z.log](https://github.com/user-attachments/files/25897030/home-assistant_bsblan_2026-03-11T07-47-17.444Z.log)

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

Hey there [user], mind taking a look at this issue as it has been labeled with an integration (`bsblan`) you are listed as a [code owner](https://github.com/home-assistant/core/blob/dev/CODEOWNERS#L259) for? Thanks!

<details>
<summary>Code owner commands</summary>

Code owners of `bsblan` can trigger bot actions by commenting:

- `@home-assistant close` Closes the issue.
- `@home-assistant rename Awesome new title` Renames the issue.
- `@home-assistant reopen` Reopen the issue.
- `@home-assistant unassign bsblan` Removes the current integration label and assignees on the issue, add the integration domain after the command.
- `@home-assistant add-label needs-more-information` Add a label (needs-more-information, problem in dependency, problem in custom component, problem in config, problem in device, feature-request) to the issue.
- `@home-assistant remove-label needs-more-information` Remove a label (needs-more-information, problem in dependency, problem in custom component, problem in config, problem in device, feature-request) on the issue.

</details>

<sub><sup>(message by CodeOwnersMention)</sup></sub>

---

[user] Thanks for reporting this issue!

Before we dive in, please make sure this isn't a duplicate by searching through existing issues. Also check recently closed issues, as your problem might already be fixed but not yet released.

https://github.com/home-assistant/core/issues?q=%20label%3A%22integration%3A%20bsblan%22%20
<sub><sup>(message by IssueContext)</sup></sub>

---

[bsblan documentation](https://www.home-assistant.io/integrations/bsblan)
[bsblan source](https://github.com/home-assistant/core/tree/dev/homeassistant/components/bsblan)
<sub><sup>(message by IssueLinks)</sup></sub>

### Comment 2 ([user]):

I thought I made these values optional. Will check why it errors

### Comment 3 ([user]):

Are there any new Information on this topic, because if got the same Issue. The everything is Setup like it is supposed to but I still got the Error:  Configuration error: An unknown error occurred while retrieving static device data

### Comment 4 ([user]):

[user] You tested this branch? (withheld: the upstream fix is not part of the task)
Maybe I'll spin up a fake server to test it. It should work

### Comment 5 ([user]):

I tested it with a fake server this branch and it did the setup fine. So I hope the fix is in the next dot release

### Comment 6 ([user]):

[user] [user] Let me know if it works now. It's in the latest core the fix.

## PR Review Comments

**[user]** on `homeassistant/components/bsblan/__init__.py`:

`static_values()` is now fetched after `device()`/`info()` complete, which makes setup do an additional sequential I/O round-trip (previously all three were fetched in parallel). Consider starting `static_values()` concurrently (e.g., create a task before the gather, or use `asyncio.gather(..., return_exceptions=True)` and ignore only the static-values exception) so startup latency doesn’t regress when static values are available.

**[user]** on `homeassistant/components/bsblan/diagnostics.py`:

Use an explicit `is not None` check instead of truthiness here (e.g., `data.static is not None`) to avoid any unexpected falsy behavior and to make the intent (nullable field) clearer now that `static` can be `None`.

**[user]** on `homeassistant/components/bsblan/__init__.py`:

this is not really needed as is the bus that bsblan uses is not parallel either

**[user]** on `tests/components/bsblan/test_climate.py`:

Is it possible to state a specific value for this test?

Based on the contents of the json file, i expect it will be 18.5
```suggestion
    assert state.attributes["current_temperature"] == 18.5
```

**[user]** on `tests/components/bsblan/test_climate.py`:

Thanks will do. Also I could parametrize another test.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
