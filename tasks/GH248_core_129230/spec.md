# GH248_core_129230: Fix timeout issue on Roomba integration when adding a new device — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/home-assistant/core/issues/117071
- Repo: https://github.com/home-assistant/core

## Issue Description

### The problem

I can't set up my Roomba integration. Even after manually inputting the correct password, it fails

### What version of Home Assistant Core has the issue?

core-2024.5.2

### What was the last working version of Home Assistant Core?

_No response_

### What type of installation are you running?

Home Assistant OS

### Integration causing the issue

roomba

### Link to integration documentation on our website

https://www.home-assistant.io/integrations/roomba/

### Diagnostics information

_No response_

### Example YAML snippet

_No response_

### Anything in the logs that might be useful for us?

_No response_

### Additional information

After some debugging I managed to track down the issue to the fact that we do not use the "continuous" mode of roombapy (or alternatively, the delay of 1 second is too low).

https://github.com/home-assistant/core/blob/fd8c36d93b3124f5215b78b4eab1fa4ee9d684e7/homeassistant/components/roomba/config_flow.py#L58

https://github.com/home-assistant/core/blob/fd8c36d93b3124f5215b78b4eab1fa4ee9d684e7/homeassistant/components/roomba/const.py#L12

 This causes the connection to reset itself too fast, before the "name" property is being updated on the state object, causing the loop to timeout. 

https://github.com/home-assistant/core/blob/fd8c36d93b3124f5215b78b4eab1fa4ee9d684e7/homeassistant/components/roomba/__init__.py#L82-L90

Manually changing the code fixed it and I managed to connect.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hey there [user], [user], [user], [user], [user], mind taking a look at this issue as it has been labeled with an integration (`roomba`) you are listed as a [code owner](https://github.com/home-assistant/core/blob/dev/CODEOWNERS#L1175) for? Thanks!

<details>
<summary>Code owner commands</summary>

Code owners of `roomba` can trigger bot actions by commenting:

- `@home-assistant close` Closes the issue.
- `@home-assistant rename Awesome new title` Renames the issue.
- `@home-assistant reopen` Reopen the issue.
- `@home-assistant unassign roomba` Removes the current integration label and assignees on the issue, add the integration domain after the command.
- `@home-assistant add-label needs-more-information` Add a label (needs-more-information, problem in dependency, problem in custom component) to the issue.
- `@home-assistant remove-label needs-more-information` Remove a label (needs-more-information, problem in dependency, problem in custom component) on the issue.

</details>

<sub><sup>(message by CodeOwnersMention)</sup></sub>

---

[roomba documentation](https://www.home-assistant.io/integrations/roomba)
[roomba source](https://github.com/home-assistant/core/tree/dev/homeassistant/components/roomba)
<sub><sup>(message by IssueLinks)</sup></sub>

### Comment 2 ([user]):

[user] can we please also include the fix in (withheld: the upstream fix is not part of the task)?

### Comment 3 ([user]):

Are you saying that the provided config settings are not changing the underlying code?

![Screenshot_20240705_110339_Chrome](https://github.com/home-assistant/core/assets/7085931/6767454f-d8a2-4d48-8d7b-922da9a4861b)

### Comment 4 ([user]):

I've tried continuous on, off. Tried changing the delay all the way up to 5.

Nothing works still for a J9+ vacuum.

### Comment 5 ([user]):

What I did was copy the Roomba component of Core. Put it in the folder custom_components. Find the file config_flow.py and change continuous to true. Reload HA and it worked for me.

### Comment 6 ([user]):

[user], forgive the noob question, but where is the Roomba component of Core that I need to copy?  I have a J9+ (no mop) and am trying to follow your steps by rote.

### Comment 7 ([user]):

No problem, it’s [this](https://github.com/home-assistant/core/tree/fd8c36d93b3124f5215b78b4eab1fa4ee9d684e7/homeassistant/components/roomba) folder that you need to copy to a folder that you have to create called custom_components inside the homassistant folder. Which is accessible with for instance the  studio code server plugin in HA

https://github.com/home-assistant/core/tree/fd8c36d93b3124f5215b78b4eab1fa4ee9d684e7/homeassistant/components/roomba

### Comment 8 ([user]):

[user] thanks for the direction.  Was able to do that without a problem, as well as make the change to Continuous.  But I'm still getting "Failed to Connect" when trying to add my J9.  The odd thing is that HA finds the vacuum no problem, and I'm able to retrieve my password no problem.  But I always get the same error.  Wish there was something, anything, I could do.  Especially since Neato's API appears to have died for the last time.

### Comment 9 ([user]):

[user]  [user]  [user]  [user]  [user] 
Hey guys, I appreciate nobody is paid for doing this, so please consider this polite begging on my part.  But, can anybody take a look at these problems?  Seems like a consistent issue affecting lots of people across the HA community.

### Comment 10 ([user]):

Unfortunately after an update of core i once again am failing to connect to my device through HA... Also not possible with the workaround or so it seems. 

[user] maybe  there is a new issue now.

## PR Review Comments

**[user]** on `homeassistant/components/roomba/const.py`:

Should we not use 30 sec instead?

**[user]** on `homeassistant/components/roomba/const.py`:

Maybe 30 sec will be almost.

**[user]** on `homeassistant/components/roomba/const.py`:

Almost? If it okay as well I suggest we use 30 seconds instead

**[user]** on `homeassistant/components/roomba/const.py`:

Note that it seems you must update the tests as well

**[user]** on `homeassistant/components/roomba/const.py`:

I am not familiar with HA development and I don't really understand what I have to do. What do you mean by "it seems you must update the tests as well" ?

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
