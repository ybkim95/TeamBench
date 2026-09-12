# GH202_core_126242: Fix ColorMode.WHITE support in Tuya — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/home-assistant/core/issues/115056
- Repo: https://github.com/home-assistant/core

## Issue Description

### The problem

Hi,
Since HA 2024.4.0 I noticed that HA does not show the color mode correctly of my Tuya bulbs.

So

- on/off is correctly displayed
- when I change color in HA: icon shows the selected color
- when I switch back to white modus in the Tuya app (I can’t switch to white modus in HA): the color of the icon in HA remains in color modus although the bulb works now in white modus
- on/off works in HA, but when I want to change the brightness in HA, the old color modus is sent to the bulb

This makes that all my Tuya bulbs become more or less useless in HA:
- I can’t switch to white modus in HA
- I can’t dimm my lights because than they switch to a random color modus

Anybody same problem?
Any solution?

Kind regards,
Bart Plessers

### What version of Home Assistant Core has the issue?

core-2024.4.1

### What was the last working version of Home Assistant Core?

core-2024.3.x

### What type of installation are you running?

Home Assistant OS

### Integration causing the issue

Tuya

### Link to integration documentation on our website

https://www.home-assistant.io/integrations/tuya/

### Diagnostics information

_No response_

### Example YAML snippet

_No response_

### Anything in the logs that might be useful for us?

_No response_

### Additional information

_No response_

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

extra info: after some investigation, I noticed that this problem only occurs with Tuya lights that only support [white + color]
I have some other Tuya bulbs that support [white with colortemp + color], here the above problem does not occur...

### Comment 2 ([user]):

> set to White (CCT in Tuya App)

Are you sure this light has the capability to change color temperature? Or does it have only white + color?
In my experience:
- lights with (white + CCT, and RGB) do not have any problem
- lights with (white and RGB) experience the above problem

Seems that HA is not aware anymore of the white capabilities of the bulb if it does not support colortemp (CCT)

### Comment 3 ([user]):

Hi everyone,

I installed a previous version of HA (2023.3.1) on my proxmox server. Here this problem does not occur.

On following screenshot: 
![2024-04-09_11-02-51](https://github.com/home-assistant/core/assets/10470708/148078df-b550-42bc-8bed-c3485ac51c96)

- left image: HA 2024.3.1
- right image: HA 2024.4.2

What I did:
- in HA changed color of the bulb to blue
- in TUYA-app, I changed back to white

Version 2024.3.1:  shows the correct state of the bulb
Version 2024.4.2:  state of bulb is NOT updated and remains blue

### Comment 4 ([user]):

In example, following screenshots from my Tuya app

## TYPE 1
This bulb supports white with CCT and color:
![white with CCT + color](https://github.com/home-assistant/core/assets/10470708/98e175f4-ff20-4c79-b5b7-ddb3e2ad6206)

You can see that you can select a warm white on the left side of the arc, and a cool white (more blue) on the right side of the arc. The light still remains in “white modus”, but you can modify the correlated color temperature (CCT)
Beside this, you can also choose the “color modus” (on the top, select “kleur”).
In that case, you can choose any RGB color that you want

## TYPE 2
This bulb only supports white and color:
![white + color](https://github.com/home-assistant/core/assets/10470708/2b76cf61-b518-4b1f-ae5a-cbcc06911a96)

You can see that there is no difference in color temperature in the arc. The white modus supports only one temperature of white.
Beside this, you can also choose the “color modus” (on the top, select “kleur”).

The problem we are dealing with does only occur on bulbs of **type 2**.
As far as I can see on your screenshot, is that in your “CCT” modus, there is no possibility to change the color temp. It seems that you can only activate one colortemp. So it looks like it’s also a “type 2” bulb.

### Comment 5 ([user]):

FYI [user] 
I downgraded to HA 2024.3.3
This version has no problems with this kind of Tuya lights

### Comment 6 ([user]):

Here is some other interesting thing:
I have 2 concurrent instances of HA running on my ProxMox server. Both have the Tuya integration running

What you can see here: same light, but other version of HA:

## HA 2024.3.3
![2024-04-10_21-54-57](https://github.com/home-assistant/core/assets/10470708/00033c84-93c4-4601-ad1d-3c8cd1ed204c)

## HA 2024.4.2
![2024-04-10_21-54-27](https://github.com/home-assistant/core/assets/10470708/c9660b91-c05e-4a96-a6ce-4eb9d2dca554)

So it seems that HA 2024.4.x does not recognize the "brightness" modus of this tuya bulb!

### Comment 7 ([user]):

I got same problem.

### Comment 8 ([user]):

Created a new issue on
https://github.com/tuya/tuya-home-assistant/issues/987

### Comment 9 ([user]):

Yup, I started suffering from this recently, "supported_modes" comes back only with "hs", whereas a few weeks ago it was coming back with "brightness" as well.  Except even then I couldn't actually *change* to "brightness" from turn_on - once HA set the light to "hs", it was stuck in "hs".  Now it's stuck in "hs" every single time I make any sort of change from HA.

I am *suspicious* of 770e48d5.

### Comment 10 ([user]):

With 770e48d, it looks like WORK_MODE must be "white" to get brightness.  How do I work out what device.category is of my particular devices? 

EDIT: looks like category == "dj" from device info > device diagnostics.

And I can see data.status.work_mode = "white" whenever the tuya app was the last set to white, and HA hasn't come along and fiddled with the settings yet.  Alas, as soon as HA fiddles with the brightness (not just power - power toggle leaves the settings as they were), data.status.work_mode reverts to "colour" (I praise the developers for their proper spelling of "colour").

I can't find a way of getting work_mode back into "white".  Also, the GUI can't do it, which tells me it's not my fault.

## PR Review Comments

**[user]** on `homeassistant/components/tuya/light.py`:

This part of the code can't be correct. We are mapping kelvin to a min/max mireds here.

**[user]** on `homeassistant/components/tuya/light.py`:

I have reverted the command to what's on the dev branch.

The actual code change here should just be the addition of the `if` statement to check if the bulb has color temp available.

this must have been a merge/rebasing issue.

**[user]** on `tests/components/tuya/fixtures/smart_light_bulb_colorandwhite_nocolortemp.json`:

You MUSTN'T obfuscate the product_id - we need it to differentiate various products

**[user]** on `tests/components/tuya/fixtures/smart_light_bulb_colorandwhite_nocolortemp.json`:

Please rename the fixture to be prefixed by the category, eg. `dj_smart_light_bulb.json`

**[user]** on `tests/components/tuya/__init__.py`:

Keep alphabetical order (between `cz_dual_channel_metering` and `dlq_earu_electric_eawcpt` once correctly prefixed with `dj`)

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
