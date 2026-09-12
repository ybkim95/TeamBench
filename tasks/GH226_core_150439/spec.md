# GH226_core_150439: Fix brightness command not sent when in white color mode — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/home-assistant/core/issues/150269
- Repo: https://github.com/home-assistant/core

## Issue Description

### The problem

Hi, 

I've been following [#115056](https://github.com/home-assistant/core/issues/115056) and the [associated PR]((withheld: the upstream fix is not part of the task)) that allowed me to set my Tuya bulbs to White color, and it's great to now be able to do it. 

But I've noticed that I cannot change the brightness at the same time, which makes it impossible to create buttons that directly set up the light to white mode at a specific brightness, like it is possible with colors.

Playing around with actions for testing, I've noticed that the brightness option is simply ignored when setting white to true in the same action:
```yaml
action: light.turn_on
target:
  entity_id: light.rgbc_smart_bulb_thomas
data:
  white: true
  brightness: 50 # This is ignored, brightness stays at the previous level
```
I **can** change the brightness of the white light, but I have to send the brightness options alone:
```yaml
action: light.turn_on
target:
  entity_id: light.rgbc_smart_bulb_thomas
data:
  brightness: 50
```

So in the UI, brightness sliders work fine after setting the light to white, but a favorite button for *white at 50%* doesn't work.

### What version of Home Assistant Core has the issue?

core-2025.8.0

### What was the last working version of Home Assistant Core?

_No response_

### What type of installation are you running?

Home Assistant Container

### Integration causing the issue

Tuya

### Link to integration documentation on our website

https://www.home-assistant.io/integrations/tuya/

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

Hey there [user], [user], mind taking a look at this issue as it has been labeled with an integration (`tuya`) you are listed as a [code owner](https://github.com/home-assistant/core/blob/dev/CODEOWNERS#L1634) for? Thanks!

<details>
<summary>Code owner commands</summary>

Code owners of `tuya` can trigger bot actions by commenting:

- `@home-assistant close` Closes the issue.
- `@home-assistant rename Awesome new title` Renames the issue.
- `@home-assistant reopen` Reopen the issue.
- `@home-assistant unassign tuya` Removes the current integration label and assignees on the issue, add the integration domain after the command.
- `@home-assistant add-label needs-more-information` Add a label (needs-more-information, problem in dependency, problem in custom component) to the issue.
- `@home-assistant remove-label needs-more-information` Remove a label (needs-more-information, problem in dependency, problem in custom component) on the issue.

</details>

<sub><sup>(message by CodeOwnersMention)</sup></sub>

---

[tuya documentation](https://www.home-assistant.io/integrations/tuya)
[tuya source](https://github.com/home-assistant/core/tree/dev/homeassistant/components/tuya)
<sub><sup>(message by IssueLinks)</sup></sub>

### Comment 2 ([user]):

[user] is this something you could look into?

I think it's linked to #126242

cc [user]

### Comment 3 ([user]):

[user] I have created the pull request above to attempt to fix this. I have not manually tested it, but have written test cases for it and I am fairly confident that this resolves the issue. Please review.

When i get some more time, I will try installing this as a custom component and doing real-world testing.

### Comment 4 ([user]):

turns out that when you send `white: true` in the action, it will send the data to the `turn_on` method as `white: 123` where `123` is the current brightness value (from 0-255). 

If you additionally send `brightness: 50` in the action, the method gets `white: 128` where `128` is the requested brightness value (50% of 255).

The part of the code that checks for brightness value in the method arguments only checks for the `brightness` key and does not check for the value in the `white` key. The `brightness` key is there for color modes and white temperature modes, but not white.

### Comment 5 ([user]):

I managed to set up a dev environment with your PR to directly test it with my light, and I can confirm it resolves the issue. Thank you!

### Comment 6 ([user]):

> I managed to set up a dev environment with your PR to directly test it with my light, and I can confirm it resolves the issue. Thank you!

Woo!!!

## PR Review Comments

**[user]** on `tests/components/tuya/test_light.py`:

Keep this line

**[user]** on `tests/components/tuya/test_light.py`:

Use merge instead:
```suggestion
        {
            "entity_id": entity_id,
            **turn_on_input,
        },
```

**[user]** on `tests/components/tuya/test_light.py`:

```suggestion
    turn_on_input: dict[str, Any],
```

**[user]** on `tests/components/tuya/test_light.py`:

```suggestion
    expected_commands: list[dict[str, Any]],
```

**[user]** on `tests/components/tuya/test_light.py`:

```suggestion
async def test_turn_on_white(
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
