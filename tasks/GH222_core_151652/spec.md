# GH222_core_151652: Fix Aladdin Connect state not updating — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/home-assistant/core/issues/151642
- Repo: https://github.com/home-assistant/core

## Issue Description

### The problem

The Garage Door (Cover Entity) is not updating in HA.  My door is always showing closed in HA.  It works fine in the AC App, and shows it open when it is open, but HA never updates when the door is opened.

### What version of Home Assistant Core has the issue?

2025.9.0

### What was the last working version of Home Assistant Core?

2025.9.0

### What type of installation are you running?

Home Assistant OS

### Integration causing the issue

Aladdin Connect

### Link to integration documentation on our website

https://www.home-assistant.io/integrations/aladdin_connect/

### Diagnostics information

N/A

### Example YAML snippet

```yaml
N/A
```

### Anything in the logs that might be useful for us?

```txt
No log entries.
```

### Additional information

Here is my history from HA for the Garage Door Entity which does not show it was ever opened. 

<img width="2471" height="232" alt="Image" src="https://github.com/user-attachments/assets/d9a28e8c-75b9-4502-9593-a732e1ec70eb" />

Here is the log from my Aladdin Connect App which shows the door was opened twice during the same period. 

<img width="1284" height="2778" alt="Image" src="https://github.com/user-attachments/assets/c21c5c20-716e-4fc6-8efa-353c4cbb5c23" />

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hey there [user], mind taking a look at this issue as it has been labeled with an integration (`aladdin_connect`) you are listed as a [code owner](https://github.com/home-assistant/core/blob/dev/CODEOWNERS#L90) for? Thanks!

<details>
<summary>Code owner commands</summary>

Code owners of `aladdin_connect` can trigger bot actions by commenting:

- `@home-assistant close` Closes the issue.
- `@home-assistant rename Awesome new title` Renames the issue.
- `@home-assistant reopen` Reopen the issue.
- `@home-assistant unassign aladdin_connect` Removes the current integration label and assignees on the issue, add the integration domain after the command.
- `@home-assistant add-label needs-more-information` Add a label (needs-more-information, problem in dependency, problem in custom component) to the issue.
- `@home-assistant remove-label needs-more-information` Remove a label (needs-more-information, problem in dependency, problem in custom component) on the issue.

</details>

<sub><sup>(message by CodeOwnersMention)</sup></sub>

---

[aladdin_connect documentation](https://www.home-assistant.io/integrations/aladdin_connect)
[aladdin_connect source](https://github.com/home-assistant/core/tree/dev/homeassistant/components/aladdin_connect)
<sub><sup>(message by IssueLinks)</sup></sub>

### Comment 2 ([user]):

I am also seeing this issue.  The state of the garage door never updates, and it always shows as closed (though I am able to control the door in both directions via the integration).  I'm running HA 2025.9.0 on an RPI5.

### Comment 3 ([user]):

I am also experiencing this same issue. The state of the garage door is always "Closed" regardless of the actual position of the door.

### Comment 4 ([user]):

I've submitted a PR for review that resolves this issue. Hopefully it can be merged in and fixed soon. #151652

### Comment 5 ([user]):

Same issue as well.  Sorry I missed this during beta.

### Comment 6 ([user]):

[user] , any update on this? We are all facing this bug. I've had to migrate back to the Homebridge Aladdin Connect plugin. I'd really like to remove that complication from my setup and use this official integration.

### Comment 7 ([user]):

Is there a fix to this or do I just wait on an update? I thought I was just crazy with this issue then randomly ended up here and see it’s not just me

### Comment 8 ([user]):

iphone13

On Sat, Sep 6, 2025 at 2:17 AM trainman ***@***.***> wrote:

> *trainman* left a comment (home-assistant/core#151642)
> <https://github.com/home-assistant/core/issues/151642#issuecomment-3259951934>
>
> [user] <https://github.com/[user]> , any update on this? We
> are all facing this bug. I've had to migrate back to the Homebridge Aladdin
> Connect plugin. I'd really like to remove that complication from my setup
> and use this official integration.
>
> —
> Reply to this email directly, view it on GitHub
> <https://github.com/home-assistant/core/issues/151642#issuecomment-3259951934>,
> or unsubscribe
> <https://github.com/notifications/unsubscribe-auth/BQ35PUPFN3EA7TLYTOBSPET3RIHJDAVCNFSM6AAAAACFRX7YTWVHI2DSMVQWIX3LMV43OSLTON2WKQ3PNVWWK3TUHMZTENJZHE2TCOJTGQ>
> .
> You are receiving this because you are subscribed to this thread.Message
> ID: ***@***.***>
>

### Comment 9 ([user]):

[user] [user] this PR should fix the issue once it is merged: (withheld: the upstream fix is not part of the task)

## PR Review Comments

**[user]** on `homeassistant/components/aladdin_connect/coordinator.py`:

Why not write it as?

```suggestion
        if (status := self.client.get_door_status(self.data.device_id, self.data.door_number)) is None:
```

**[user]** on `homeassistant/components/aladdin_connect/coordinator.py`:

So, if one bit of information fails, the whole update would fail?

Shouldn't we instead only mark the specific sensor using this information as "Unknown" instead and let the rest of the integration work as intended?

../Frenck

**[user]** on `homeassistant/components/aladdin_connect/coordinator.py`:

We never set the state unknown directly. Instead, the native/state value of the entity should return `None` (which will result in an unknown state from the state engine).

**[user]** on `homeassistant/components/aladdin_connect/coordinator.py`:

This will cause the batter level to become 0% when it is flakly and have an affect on possible automation (e.g., notification triggers for an empty batter). Instead, just should also return an unknown state.

**[user]** on `homeassistant/components/aladdin_connect/coordinator.py`:

I'm very new to Python and did not know about the walrus operator. Very cool! Thanks for sharing

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
