# GH478_hass-opnsense_379: Fix system boot time calculation — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/travisghansen/hass-opnsense/issues/378
- Repo: https://github.com/travisghansen/hass-opnsense

## Issue Description

### What happened?

The entity _boottime is frequently updated as expected. The retrieved value is set as a new value, which triggers a state_changed event (and subsequently would trigger automations, creates log entries, generates a new color for state graphs)
It would most likely be better to check if the new value equals the old value and decide on that comparison, if the state should be set

### hass-opnsense Version

0.3.16

### OPNsense Firmware

25.1.5_1

### Home Assistant Version

2025.4.2

### Relevant logs

```shell

```

### Additional Details
This issue might affect other entities as well.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

You mean it's frequently "reported", not frequently "updated", nor frequently "changed".

It's 3 different things in HA's world (see [here](https://www.home-assistant.io/docs/configuration/state_object/#about-the-state-object)). :)

![Image](https://github.com/user-attachments/assets/bf577560-fb02-4bb7-9d7f-e86bae9b023f)

Home Assistant's state machine is designed to only trigger a `state_changed` event when there is an actual change in the state value or attributes. If you update an entity to the same state value with the same attributes, no `state_changed` event will be generated, and data will not be recorded.

Did you check if `state_changed` event is fired every X seconds (data update coordinator cycle) for that entity? I checked my HA production instance, waited for some data update cycles, and it doesn't fire, as expected.

![Image](https://github.com/user-attachments/assets/a25d0066-0923-4583-ad92-b563ade70641)

### Comment 2 ([user]):

If you want to easily check, you can use this in the dev tools template section:

```yaml
- Last Updated: {{ states.sensor.opnsense_system_boottime.last_updated }}
- Last Changed: {{ states.sensor.opnsense_system_boottime.last_changed }}
-Last Reported: {{ states.sensor.opnsense_system_boottime.last_reported }}
```

You will see this:

```console
- Last Updated: 2025-04-14 12:46:07.266239+00:00
- Last Changed: 2025-04-14 12:46:07.266239+00:00
-Last Reported: 2025-04-14 17:43:43.339671+00:00
```

And if you wait some polling cycles, and refresh the page, you'll notice that `last_updated` and `last_changed` remain the same, but `last_reported` changes because it is reported by the integration, but the state machine didn't record it since the value (the state) was the same, and so the `state_changed` event is not fired.

```console
- Last Updated: 2025-04-14 12:46:07.266239+00:00
- Last Changed: 2025-04-14 12:46:07.266239+00:00
-Last Reported: 2025-04-14 17:48:11.122017+00:00
```

### Comment 3 ([user]):

Well, I'm not completely new to the Home Assistant world and I know the difference between those three. I explicitly mean *changed*. 

<img width="492" alt="Image" src="https://github.com/user-attachments/assets/f71e70da-0088-41da-aade-2f55b6d1964b" />

(Dont mind the 'rooter', it's a gag)

### Comment 4 ([user]):

I've now set a watcher for state_changed and wait for a new state change (Happens in intervals between a few minutes and a few hours for me)

### Comment 5 ([user]):

Question: why should System Boottime change if it hasn't rebooted? :)

From that screenshot you posted, I don't see any change, correct?

### Comment 6 ([user]):

Why would it? I don't know, it does though. 
The screenshot shows the log. Log entries only appear on state_change. So yeah, it is changed to seemingly the same value. Don't ask me why, that's why people open bug reports to developers 🤷‍♂️
In my test period yesterday, i didn't happen to catch one of those events, I'm going to try again later.

### Comment 7 ([user]):

Managed to catch some. The timestamps are off by a second, and it seems to randomly change between them. 
I don't know how the value is generated (current time - uptime -> rounded?) and where (on the firewall or in this integration), but I guess that might be the direction we're looking at. 
Quick and dirty fix I am thinking of would be to strip the seconds and set them to 0, so minor fluctuations only lead to this error, when it's switching between 59 and 00.

```

Home Assistant: {'entity_id': 'sensor.rooter_system_boottime', 'old_state': <state sensor.rooter_system_boottime=2025-04-11T06:59:50+00:00; device_class=timestamp, icon=mdi:clock-outline, friendly_name=rooter System Boottime @ 2025-04-15T08:24:16.921716+02:00>, 'new_state': <state sensor.rooter_system_boottime=2025-04-11T06:59:51+00:00; device_class=timestamp, icon=mdi:clock-outline, friendly_name=rooter System Boottime @ 2025-04-15T10:44:05.998991+02:00>}

Home Assistant: {'entity_id': 'sensor.rooter_system_boottime', 'old_state': <state sensor.rooter_system_boottime=2025-04-11T06:59:51+00:00; device_class=timestamp, icon=mdi:clock-outline, friendly_name=rooter System Boottime @ 2025-04-15T10:44:05.998991+02:00>, 'new_state': <state sensor.rooter_system_boottime=2025-04-11T06:59:50+00:00; device_class=timestamp, icon=mdi:clock-outline, friendly_name=rooter System Boottime @ 2025-04-15T10:44:44.954067+02:00>}

Home Assistant: {'entity_id': 'sensor.rooter_system_boottime', 'old_state': <state sensor.rooter_system_boottime=2025-04-11T06:59:50+00:00; device_class=timestamp, icon=mdi:clock-outline, friendly_name=rooter System Boottime @ 2025-04-15T10:44:44.954067+02:00>, 'new_state': <state sensor.rooter_system_boottime=2025-04-11T06:59:51+00:00; device_class=timestamp, icon=mdi:clock-outline, friendly_name=rooter System Boottime @ 2025-04-15T10:48:43.050465+02:00>}

Home Assistant: {'entity_id': 'sensor.rooter_system_boottime', 'old_state': <state sensor.rooter_system_boottime=2025-04-11T06:59:51+00:00; device_class=timestamp, icon=mdi:clock-outline, friendly_name=rooter System Boottime @ 2025-04-15T10:48:43.050465+02:00>, 'new_state': <state sensor.rooter_system_boottime=2025-04-11T06:59:50+00:00; device_class=timestamp, icon=mdi:clock-outline, friendly_name=rooter System Boottime @ 2025-04-15T10:49:22.189103+02:00>}

Home Assistant: {'entity_id': 'sensor.rooter_system_boottime', 'old_state': <state sensor.rooter_system_boottime=2025-04-11T06:59:50+00:00; device_class=timestamp, icon=mdi:clock-outline, friendly_name=rooter System Boottime @ 2025-04-15T10:49:22.189103+02:00>, 'new_state': <state sensor.rooter_system_boottime=2025-04-11T06:59:51+00:00; device_class=timestamp, icon=mdi:clock-outline, friendly_name=rooter System Boottime @ 2025-04-15T10:56:32.810930+02:00>}

Home Assistant: {'entity_id': 'sensor.rooter_system_boottime', 'old_state': <state sensor.rooter_system_boottime=2025-04-11T06:59:51+00:00; device_class=timestamp, icon=mdi:clock-outline, friendly_name=rooter System Boottime @ 2025-04-15T10:56:32.810930+02:00>, 'new_state': <state sensor.rooter_system_boottime=2025-04-11T06:59:50+00:00; device_class=timestamp, icon=mdi:clock-outline, friendly_name=rooter System Boottime @ 2025-04-15T10:57:11.964247+02:00>}

Home Assistant: {'entity_id': 'sensor.rooter_system_boottime', 'old_state': <state sensor.rooter_system_boottime=2025-04-11T06:59:50+00:00; device_class=timestamp, icon=mdi:clock-outline, friendly_name=rooter System Boottime @ 2025-04-15T10:57:11.964247+02:00>, 'new_state': <state sensor.rooter_system_boottime=2025-04-11T06:59:51+00:00; device_class=timestamp, icon=mdi:clock-outline, friendly_name=rooter System Boottime @ 2025-04-15T11:04:24.895463+02:00>}

Home Assistant: {'entity_id': 'sensor.rooter_system_boottime', 'old_state': <state sensor.rooter_system_boottime=2025-04-11T06:59:51+00:00; device_class=timestamp, icon=mdi:clock-outline, friendly_name=rooter System Boottime @ 2025-04-15T11:04:24.895463+02:00>, 'new_state': <state sensor.rooter_system_boottime=2025-04-11T06:59:50+00:00; device_class=timestamp, icon=mdi:clock-outline, friendly_name=rooter System Boottime @ 2025-04-15T11:05:04.214273+02:00>}
```

Additional a small personal remark from me as a fellow hobby open source developer:
> The user might be the problem in most of the cases. However, I think it's best to, if at all, only treat the user as problem, if one is really shure he's the problem. Open Source lives by participation of users, so their constructive feedback should be welcomed, even if wrong. No bad feelings, I just wanted to share my thoughts on that matter.

### Comment 8 ([user]):

I've implemented a quick fix and opened a PR for that - Would be happy to receive your feedback and approval.

### Comment 9 ([user]):

> Additional a small personal remark from me as a fellow hobby open source developer:

I'm a user too and hobbist developer. And the only thing I did is asking questions and provide information to clear things up. It was a constructive discussion, I don't know why you perceived as if I thought you were a "problem", I can ensure that was not the case.

I always encourage discussions because I believe it's the nature of open-source projects that imposes it. Actually it was one of my main arguments vs the HA dev team, which I find is not open to discussions with users, so I'm really surprised about your comment.

I'm sorry you felt that way, but reading again my posts above, I don't think I've done anything wrong, maybe it's just my style of writing, that is a little bit "straight".

Thanks to that discussion, you've found a bug, so I think it was productive.

### Comment 10 ([user]):

Thanks for your response on that. It might have an effect, that English is not my first language, I think a lot of meaning is lost during translations. It might have also been the 8 hours of debugging on another project that annoyed me a bit, so I’m happy to read that it wasn’t meant the way I understood it! I’m going to switch my production instance to my branch to see if it runs fine and resolves that issue. Due to the very small nature of changes I don’t think there will be any side effects.

## PR Review Comments

**[user]** on `custom_components/opnsense/pyopnsense/__init__.py`:

Like I said in the discussion, this is not correct: we shouldn't use HA system time but `datetime` from the API endpoint response. The time source has to be the same.

**[user]** on `custom_components/opnsense/pyopnsense/__init__.py`:

uptime is available in the API response, it shouldn't be calculated. the PR you made in opnsense *adds* boottime, it doesn't replace uptime, IIRC.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
