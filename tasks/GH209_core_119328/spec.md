# GH209_core_119328: Remove obsolete device links in Utility Meter helper — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/home-assistant/core/issues/111380
- Repo: https://github.com/home-assistant/core

## Issue Description

### The problem

When i am going to 
/Settings/Devices & Services/MQTT/Devices
one Device has "utility meters" listed in "Device Info" but don't have one.
Don't have any other issues with that, its only a'beauty mistake'.

![image](https://github.com/home-assistant/core/assets/85791333/126d0e92-0716-4dcf-9513-7a0879b84767)

Its very strange, because when i klick on one "utility meters" i receive this:
![image](https://github.com/home-assistant/core/assets/85791333/42261c22-7f0d-4c57-94e2-5347f812e8fe)

Seven entities have two devices! Don't know how that is possible.
When i click on this two devices i receive this:

![image](https://github.com/home-assistant/core/assets/85791333/eddc4b01-fe07-4395-8d6f-87316aecf1fd)

The 7 devices that are belonging to two devices are only attached to device "Cerbo-GX".
The device "Quattro-II 48/5000/70-2x50 L1" has no utility meters linked...

Anyone ideas to fix this?
Thanks in advance
Marc

### What version of Home Assistant Core has the issue?

core-2024.2.3

### What was the last working version of Home Assistant Core?

not Version specific

### What type of installation are you running?

Home Assistant OS

### Integration causing the issue

perhaps MQTT ? don't know

### Link to integration documentation on our website

https://www.home-assistant.io/integrations/sensor.mqtt/

### Diagnostics information

[mqtt-d3da3448b546e3c93c74fc82d6ddf065-Quattro-II 48_5000_70-2x50 L1-9e6142914a9ba93eefc7dbaac7d116be.json](https://github.com/home-assistant/core/files/14396248/mqtt-d3da3448b546e3c93c74fc82d6ddf065-Quattro-II.48_5000_70-2x50.L1-9e6142914a9ba93eefc7dbaac7d116be.json)
[mqtt-d3da3448b546e3c93c74fc82d6ddf065-Cerbo-GX-ca963d908cac2dbb35faa4e7d503696b.json](https://github.com/home-assistant/core/files/14396324/mqtt-d3da3448b546e3c93c74fc82d6ddf065-Cerbo-GX-ca963d908cac2dbb35faa4e7d503696b.json)

### Example YAML snippet

```yaml
This is a part of my MQTT configuration belonging to these 7 source entities which are the base for these utility meters:

      # dbus-service-name: com.victronenergy.vebus
      # dbus-obj-path: /Energy/AcIn1ToAcOut
      - name: "Energy from AC-In 1 to AC-out"
        state_topic: "victron/N/c0619ab2e930/vebus/276/Energy/AcIn1ToAcOut"
        unique_id: "5c4bf864-6816-4098-b104-67af7beb0800"
        state_class: total_increasing
        device_class: energy
        value_template: '{{ value_json.value | round(2) }}'
        unit_of_measurement: "kWh"
        device:
            name: "Cerbo-GX"
            manufacturer: "Victron"
            model: "Cerbo-GX"
            identifiers:
                - "c0619ab2e930"

      # dbus-service-name: com.victronenergy.vebus
      # dbus-obj-path: /Energy/AcIn1ToInverter
      - name: "Energy from AC-In 1 to battery"
        state_topic: "victron/N/c0619ab2e930/vebus/276/Energy/AcIn1ToInverter"
        unique_id: "8e3765fb-80b7-437b-9941-be290fe60f8d"
        state_class: total_increasing
        device_class: energy
        value_template: '{{ value_json.value | round(2) }}'
        unit_of_measurement: "kWh"
        device:
            name: "Cerbo-GX"
            manufacturer: "Victron"
            model: "Cerbo-GX"
            identifiers:
                - "c0619ab2e930"

      # dbus-service-name: com.victronenergy.vebus
      # dbus-obj-path: /Energy/AcIn2ToAcOut
      - name: "Energy from AC-In 2 to AC-out"
        state_topic: "victron/N/c0619ab2e930/vebus/276/Energy/AcIn2ToAcOut"
        unique_id: "f5db947c-e352-4d3a-9092-dc647041c4ff"
        state_class: total_increasing
        device_class: energy
        value_template: '{{ value_json.value | round(2) }}'
        unit_of_measurement: "kWh"
        device:
            name: "Cerbo-GX"
            manufacturer: "Victron"
            model: "Cerbo-GX"
            identifiers:
                - "c0619ab2e930"

      # dbus-service-name: com.victronenergy.vebus
      # dbus-obj-path: /Energy/AcIn2ToInverter
      - name: "Energy from AC-In 2 to battery"
        state_topic: "victron/N/c0619ab2e930/vebus/276/Energy/AcIn2ToInverter"
        unique_id: "48500db4-3f31-44cf-9b62-6eb463719c5d"
        state_class: total_increasing
        device_class: energy
        value_template: '{{ value_json.value | round(2) }}'
        unit_of_measurement: "kWh"
        device:
            name: "Cerbo-GX"
            manufacturer: "Victron"
            model: "Cerbo-GX"
            identifiers:
                - "c0619ab2e930"

      # dbus-service-name: com.victronenergy.vebus
      # dbus-obj-path: /Energy/InverterToAcIn1
      - name: "Energy from battery to AC-in 1"
        state_topic: "victron/N/c0619ab2e930/vebus/276/Energy/InverterToAcIn1"
        unique_id: "8e9ec4ff-b62c-4e95-9034-f341a1f3150f"
        state_class: total_increasing
        device_class: energy
        value_template: '{{ value_json.value | round(2) }}'
        unit_of_measurement: "kWh"
        device:
            name: "Cerbo-GX"
            manufacturer: "Victron"
            model: "Cerbo-GX"
            identifiers:
                - "c0619ab2e930"

      # dbus-service-name: com.victronenergy.vebus
      # dbus-obj-path: /Energy/InverterToAcIn2
      - name: "Energy from battery to AC-in 2"
        state_topic: "victron/N/c0619ab2e930/vebus/276/Energy/InverterToAcIn2"
        unique_id: "ec55e984-96f8-44d0-a10d-4fa45c8faa19"
        state_class: total_increasing
        device_class: energy
        value_template: '{{ value_json.value | round(2) }}'
        unit_of_measurement: "kWh"
        device:
            name: "Cerbo-GX"
            manufacturer: "Victron"
            model: "Cerbo-GX"
            identifiers:
                - "c0619ab2e930"

      # dbus-service-name: com.victronenergy.vebus
      # dbus-obj-path: /Energy/InverterToAcOut
      - name: "Energy from battery to AC-out"
        state_topic: "victron/N/c0619ab2e930/vebus/276/Energy/InverterToAcOut"
        unique_id: "b85be846-b8b2-4b93-a075-60a19fbba4e8"
        state_class: total_increasing
        device_class: energy
        value_template: '{{ value_json.value | round(2) }}'
        unit_of_measurement: "kWh"
        device:
            name: "Cerbo-GX"
            manufacturer: "Victron"
            model: "Cerbo-GX"
            identifiers:
                - "c0619ab2e930"
```

### Anything in the logs that might be useful for us?

_No response_

### Additional information

_No response_

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hey there [user], [user], mind taking a look at this issue as it has been labeled with an integration (`mqtt`) you are listed as a [code owner](https://github.com/home-assistant/core/blob/dev/CODEOWNERS#L844) for? Thanks!

<details>
<summary>Code owner commands</summary>

Code owners of `mqtt` can trigger bot actions by commenting:

- `@home-assistant close` Closes the issue.
- `@home-assistant rename Awesome new title` Renames the issue.
- `@home-assistant reopen` Reopen the issue.
- `@home-assistant unassign mqtt` Removes the current integration label and assignees on the issue, add the integration domain after the command.
- `@home-assistant add-label needs-more-information` Add a label (needs-more-information, problem in dependency, problem in custom component) to the issue.
- `@home-assistant remove-label needs-more-information` Remove a label (needs-more-information, problem in dependency, problem in custom component) on the issue.

</details>

<sub><sup>(message by CodeOwnersMention)</sup></sub>

---

[mqtt documentation](https://www.home-assistant.io/integrations/mqtt)
[mqtt source](https://github.com/home-assistant/core/tree/dev/homeassistant/components/mqtt)
<sub><sup>(message by IssueLinks)</sup></sub>

### Comment 2 ([user]):

If you had a previous config with an other device reference this could create a new device context. An MQTT entity can be bound to one device only AFAIN.

### Comment 3 ([user]):

How can i remove the wrong device context now?

### Comment 4 ([user]):

For MQTT you can remove the device from the UI, but if there are other entities from an other integration e.g. Utility Meter linked to the same device, then the device will remain.

### Comment 5 ([user]):

> For MQTT you can remove the device from the UI, but if there are other entities from an other integration e.g. Utility Meter linked to the same device, then the device will remain.

I don't want to delete the device, its still there. I want only unlink the wrong "utility meter" links. How can i do this? There ist no "utility meter" linked at this moment...

### Comment 6 ([user]):

Perhaps the utility meter entities use the same device reference?

### Comment 7 ([user]):

> Perhaps the utility meter entities use the same device reference?

How can i check this?
When i go to /Settings/Devices&Services/Helpers all utility meter entities are shown, but no reference configurable.
I can only reference the source entity. And the source entity is not referenced to the device, its linked to another device. Its only referenced to the same Area.

![image](https://github.com/home-assistant/core/assets/85791333/0e60d10c-aea7-4a2c-b652-00f412d06a51)

![image](https://github.com/home-assistant/core/assets/85791333/b7ee8381-f0c1-492a-9977-0c437c767010)

### Comment 8 ([user]):

I have no idea to be honest

### Comment 9 ([user]):

Hey there [user], mind taking a look at this issue as it has been labeled with an integration (`utility_meter`) you are listed as a [code owner](https://github.com/home-assistant/core/blob/dev/CODEOWNERS#L1453) for? Thanks!

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

### Comment 10 ([user]):

As far as I can see, utility meter also has linked the device in your description (multiple times), that is why it is listed. I saw it my router (Fritzbox) adds device trackers to all devices. But it seems the issue is with the utility meter helpers. I do not think this is an issue with MQTT.

## PR Review Comments

**[user]** on `homeassistant/components/utility_meter/__init__.py`:

I'm not convinced the unconditional remove here is great, I think we should add a check in the for loop if the device has an entity matching our source sensor before continuing.

**[user]** on `homeassistant/components/utility_meter/__init__.py`:

The only point of the integration is links to another entity. Anything linking to to this config entry that is not part of its source config is wrong.

We could avoid removing the link if it is still valid, but it adds complexity which i couldn't find a good reason for.

If we do validate the links, i think the consideration of doing it on startup instead make a lot of sense.

**[user]** on `homeassistant/components/utility_meter/__init__.py`:

> Anything linking to to this config entry that is not part of its source config is wrong.

Yeah, exactly, but the PR removes ALL links, not just the links which are not part of the source config.

**[user]** on `homeassistant/components/utility_meter/__init__.py`:

Yup, its copied from threshold and generic_hygrostat that i wrote. The links get recreated after startup.

We need some helper code to do this the same in all helpers that do dependant entities.

**[user]** on `homeassistant/components/utility_meter/__init__.py`:

I changed the code so that the cleaning occurs throughout the configuration and so that the link with the current device is preserved. I've also added a test that I believe covers possible regressions.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
