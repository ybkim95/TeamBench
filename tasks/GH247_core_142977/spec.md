# GH247_core_142977: Fix Automation/Script: sequence within a parallel ignoring enabled flag — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/home-assistant/core/issues/125438
- Repo: https://github.com/home-assistant/core

## Issue Description

### The problem

first noticed this in 2024.8 and remains in 2024.9.
running haos on a HA yellow

if you have a parallel building block that has sequence building blocks inside it then the sequences ignore "enabled: false" and run

so you have

parallel block
> Sequence Block 1
>>some stuff

> Sequence Block 2
>>some other stuff

even if "Sequence Block 2" is disabled then "some other stuff" still runs

have attached yaml for my repro script below using 2 dummy switch helpers and attached the trace showing both sequences running despite the 2nd one being disabled

Obviously a highly specific situation but caused me some issues that I had to work around so felt I should report

### What version of Home Assistant Core has the issue?

2024.9.1

### What was the last working version of Home Assistant Core?

_No response_

### What type of installation are you running?

Home Assistant OS

### Integration causing the issue

_No response_

### Link to integration documentation on our website

_No response_

### Diagnostics information

_No response_

### Example YAML snippet

```yaml
alias: bug repro
sequence:
  - parallel:
      - sequence:
          - action: input_boolean.toggle
            target:
              entity_id: input_boolean.dummy_switch_1
            data: {}
      - sequence:
          - action: input_boolean.toggle
            target:
              entity_id: input_boolean.dummy_switch_2
            data: {}
            enabled: true
        enabled: false
description: ""
```

### Anything in the logs that might be useful for us?

```txt
{
  "trace": {
    "last_step": "sequence/0/parallel/1/sequence/0",
    "run_id": "e72cbc4040455a101c6ef4ac9c20e63c",
    "state": "stopped",
    "script_execution": "finished",
    "timestamp": {
      "start": "2024-09-06T20:07:43.592581+00:00",
      "finish": "2024-09-06T20:07:43.608815+00:00"
    },
    "domain": "script",
    "item_id": "bug_repro",
    "trace": {
      "sequence/0": [
        {
          "path": "sequence/0",
          "timestamp": "2024-09-06T20:07:43.593733+00:00",
          "changed_variables": {
            "this": {
              "entity_id": "script.bug_repro",
              "state": "off",
              "attributes": {
                "last_triggered": "2024-09-06T20:02:28.407484+00:00",
                "mode": "single",
                "current": 0,
                "friendly_name": "bug repro"
              },
              "last_changed": "2024-09-06T20:02:53.486709+00:00",
              "last_reported": "2024-09-06T20:02:53.486709+00:00",
              "last_updated": "2024-09-06T20:02:53.486709+00:00",
              "context": {
                "id": "01J74EXDXER0BRVRV8GTNFVC4J",
                "parent_id": null,
                "user_id": null
              }
            },
            "context": {
              "id": "01J74F69783QXYRE0PE1EDHMYK",
              "parent_id": null,
              "user_id": "47977d8561934a268fa577c524482c56"
            }
          }
        }
      ],
      "sequence/0/parallel/0/sequence/0": [
        {
          "path": "sequence/0/parallel/0/sequence/0",
          "timestamp": "2024-09-06T20:07:43.595173+00:00",
          "result": {
            "params": {
              "domain": "input_boolean",
              "service": "toggle",
              "service_data": {},
              "target": {
                "entity_id": [
                  "input_boolean.dummy_switch_1"
                ]
              }
            },
            "running_script": false
          }
        }
      ],
      "sequence/0/parallel/1/sequence/0": [
        {
          "path": "sequence/0/parallel/1/sequence/0",
          "timestamp": "2024-09-06T20:07:43.598026+00:00",
          "result": {
            "params": {
              "domain": "input_boolean",
              "service": "toggle",
              "service_data": {},
              "target": {
                "entity_id": [
                  "input_boolean.dummy_switch_2"
                ]
              }
            },
            "running_script": false
          }
        }
      ]
    },
    "config": {
      "alias": "bug repro",
      "sequence": [
        {
          "parallel": [
            {
              "sequence": [
                {
                  "action": "input_boolean.toggle",
                  "target": {
                    "entity_id": "input_boolean.dummy_switch_1"
                  },
                  "data": {}
                }
              ]
            },
            {
              "sequence": [
                {
                  "action": "input_boolean.toggle",
                  "target": {
                    "entity_id": "input_boolean.dummy_switch_2"
                  },
                  "data": {},
                  "enabled": true
                }
              ],
              "enabled": false
            }
          ]
        }
      ],
      "description": ""
    },
    "blueprint_inputs": null,
    "context": {
      "id": "01J74F69783QXYRE0PE1EDHMYK",
      "parent_id": null,
      "user_id": "47977d8561934a268fa577c524482c56"
    }
  },
  "logbookEntries": []
}
```

### Additional information

_No response_

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hey there [user]/core, mind taking a look at this issue as it has been labeled with an integration (`automation`) you are listed as a [code owner](https://github.com/home-assistant/core/blob/dev/CODEOWNERS#L166) for? Thanks!

<details>
<summary>Code owner commands</summary>

Code owners of `automation` can trigger bot actions by commenting:

- `@home-assistant close` Closes the issue.
- `@home-assistant rename Awesome new title` Renames the issue.
- `@home-assistant reopen` Reopen the issue.
- `@home-assistant unassign automation` Removes the current integration label and assignees on the issue, add the integration domain after the command.
- `@home-assistant add-label needs-more-information` Add a label (needs-more-information, problem in dependency, problem in custom component) to the issue.
- `@home-assistant remove-label needs-more-information` Remove a label (needs-more-information, problem in dependency, problem in custom component) on the issue.

</details>

<sub><sup>(message by CodeOwnersMention)</sup></sub>

---

[automation documentation](https://www.home-assistant.io/integrations/automation)
[automation source](https://github.com/home-assistant/core/tree/dev/homeassistant/components/automation)
<sub><sup>(message by IssueLinks)</sup></sub>

### Comment 2 ([user]):

I think this needs something in the ballpark here:

![CleanShot 2024-11-26 at 14 47 31@2x](https://github.com/user-attachments/assets/a5a97bcc-2b32-4ab9-ac38-b9162066b341)

(in `helpers/script.py`); Small thought... probably not the best... still wanted to note it here :)

### Comment 3 ([user]):

There hasn't been any activity on this issue recently. Due to the high number of incoming GitHub notifications, we have to clean some of the old issues, as many of them have already been resolved with the latest updates.
Please make sure to update to the latest Home Assistant version and check if that solves the issue. Let us know if that works for you by adding a comment 👍
This issue has now been marked as stale and will be closed if no further activity occurs. Thank you for your contributions.

### Comment 4 ([user]):

I have had a go at fixing this in (withheld: the upstream fix is not part of the task) however it currently incomplete. it does actually solve the issue but it doesn't report back "not run as disabled" in the trace and instead just says "did not run". maybe someone could help me finish this off as I am not sure how to go about this.

### Comment 5 ([user]):

[user] 
I was about to open a new issue when I found this open one.

I have been having this issue on:
Core 2025.2.4
Supervisor 2025.02.4
Operating System   14.1
Frontend 20250214.0

I see it's tagged as stale.
I don't want to destroy some automations by deleting half of it.

### Comment 6 ([user]):

with some help from [user] and some learning I have had another go at fixing this one,  hopefully (withheld: the upstream fix is not part of the task) isn't too bad and the fix and test can be used :)

## PR Review Comments

**[user]** on `homeassistant/helpers/script.py`:

If `enabled` is an attribute of a `Script`, it should ideally be checked there, probably in `Script.async_run`.

**[user]** on `homeassistant/helpers/script.py`:

Although the intention is to never use it for top-level script anyway, so if that is documented, then I guess moving the check simply to `_async_run_script` should also be OK.

**[user]** on `homeassistant/helpers/script.py`:

[user] fair warning this is my first PR in core so please feel free to hand hold a bit if you want... or shout at me for doing it wrong :) I am happy either way.

when moving the check up to to `_async_run_script ` do you mean something like this?
![image](https://github.com/user-attachments/assets/f8e704cc-eb94-4aa1-955e-f0643bc40e71)

**[user]** on `homeassistant/helpers/script.py`:

Yes, but:
- do not move the docstring
- check for just `script.enabled`, do not check for `parallel`
- adjust the log by removing parallel

**[user]** on `homeassistant/helpers/script.py`:

[user] right, gotcha, so its more generic, like this?
![image](https://github.com/user-attachments/assets/12e79249-ceda-4a74-a9a4-a76e9d3a3650)

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
