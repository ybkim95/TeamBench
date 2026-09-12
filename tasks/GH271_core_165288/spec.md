# GH271_core_165288: Fix KeyError 'api_domain' in Freebox zeroconf discovery — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/home-assistant/core/issues/162701
- Repo: https://github.com/home-assistant/core

## Issue Description

### The problem

The Freebox integration crashes with a KeyError: 'api_domain' during the Zeroconf discovery step.
This happens when Home Assistant receives an mDNS packet from a Freebox device (Server or Repeater) that announces the service _freebox-http._tcp but does not contain the api_domain TXT record.

This seems to happen specifically with IPv6 mDNS maintenance packets (Cache Flush) containing only PTR and AAAA records, but no TXT records.

### What version of Home Assistant Core has the issue?

2026.2.3

### What was the last working version of Home Assistant Core?

_No response_

### What type of installation are you running?

Home Assistant OS

### Integration causing the issue

freebox

### Link to integration documentation on our website

https://www.home-assistant.io/integrations/freebox

### Diagnostics information

_No response_

### Example YAML snippet

```yaml

```

### Anything in the logs that might be useful for us?

```txt
2026-02-09 09:40:43.574 ERROR (MainThread) [homeassistant] Error doing job: Task exception was never retrieved (task: None)
Traceback (most recent call last):
  File "/usr/src/homeassistant/homeassistant/config_entries.py", line 1484, in async_init
    flow, result = await self._async_init(flow_id, handler, context, data)
  File "/usr/src/homeassistant/homeassistant/config_entries.py", line 1532, in _async_init
    result = await self._async_handle_step(flow, flow.init_step, data)
  File "/usr/src/homeassistant/homeassistant/data_entry_flow.py", line 483, in _async_handle_step
    result: _FlowResultT = await getattr(flow, method)(user_input)
  File "/usr/src/homeassistant/homeassistant/components/freebox/config_flow.py", line 106, in async_step_zeroconf
    host = zeroconf_properties["api_domain"]
KeyError: 'api_domain'
```

### Additional information

I analyzed the network traffic with tcpdump when the error occurred.
The crashing packet is an IPv6 mDNS packet from the Freebox Server (or Repeater) that acts as a "Cache Flush". It contains PTR and AAAA records, but no TXT records.

Tcpdump output corresponding to the crash:

09:00:10.038774 ... IP6 ... > ff02::fb.5353: [udp sum ok] ... PTR Freebox-Server-559.local., ... AAAA fe80::...
Suggested Fix:
In homeassistant/components/freebox/config_flow.py, use .get() instead of direct key access to handle packets missing the TXT record gracefully.

Python
# Current code
host = zeroconf_properties["api_domain"]

# Suggested safe code
host = zeroconf_properties.get("api_domain")
if not host:
    return self.async_abort(reason="no_api_domain")

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hey there [user], [user], mind taking a look at this issue as it has been labeled with an integration (`freebox`) you are listed as a [code owner](https://github.com/home-assistant/core/blob/dev/CODEOWNERS#L548) for? Thanks!

<details>
<summary>Code owner commands</summary>

Code owners of `freebox` can trigger bot actions by commenting:

- `@home-assistant close` Closes the issue.
- `@home-assistant rename Awesome new title` Renames the issue.
- `@home-assistant reopen` Reopen the issue.
- `@home-assistant unassign freebox` Removes the current integration label and assignees on the issue, add the integration domain after the command.
- `@home-assistant add-label needs-more-information` Add a label (needs-more-information, problem in dependency, problem in custom component, problem in config, problem in device, feature-request) to the issue.
- `@home-assistant remove-label needs-more-information` Remove a label (needs-more-information, problem in dependency, problem in custom component, problem in config, problem in device, feature-request) on the issue.

</details>

<sub><sup>(message by CodeOwnersMention)</sup></sub>

---

[user] Thanks for reporting this issue!

Before we dive in, please make sure this isn't a duplicate by searching through existing issues. Also check recently closed issues, as your problem might already be fixed but not yet released.

https://github.com/home-assistant/core/issues?q=%20label%3A%22integration%3A%20freebox%22%20
<sub><sup>(message by IssueContext)</sup></sub>

---

[freebox documentation](https://www.home-assistant.io/integrations/freebox)
[freebox source](https://github.com/home-assistant/core/tree/dev/homeassistant/components/freebox)
<sub><sup>(message by IssueLinks)</sup></sub>

## PR Review Comments

**[user]** on `homeassistant/components/freebox/config_flow.py`:

you are missing a string for that. What would a user need to do in that case? Please add a test covering that case, as we require full test coverage for the config flow

**[user]** on `homeassistant/components/freebox/config_flow.py`:

Thanks for the review!

To give some context: this exception is triggered by malformed IPv6 mDNS cache flush packets broadcasted randomly by the Freebox (especially in AP/Mesh mode). These background packets contain PTR and AAAA records but absolutely no TXT records.

Therefore, this is a "ghost" discovery packet, not a genuine user attempt to set up the integration. The user doesn't actually need to do anything, and we probably shouldn't bother them with a failed discovery notification in the UI.

Given this, should I still add a custom string in strings.json (e.g., instructing to safely ignore it), or is there a preferred HA standard abort reason to silently drop invalid zeroconf packets without spamming the user's dashboard?

Once you let me know your preferred approach for silent drops, I will immediately add the corresponding test in test_config_flow.py to cover this branch!

**[user]** on `homeassistant/components/freebox/config_flow.py`:

add the string regardless

**[user]** on `homeassistant/components/freebox/config_flow.py`:

Added the requested string and the corresponding test for full coverage. Ready for review.

**[user]** on `homeassistant/components/freebox/config_flow.py`:

`async_step_zeroconf` still uses direct key access for `api_domain`, so it will continue to raise `KeyError` when TXT records (and thus properties) are missing. Use `zeroconf_properties.get("api_domain")` (or handle `KeyError`) before the falsy check so the flow aborts cleanly instead of crashing the task.
```suggestion
        host = zeroconf_properties.get("api_domain")
        if not host:
            return self.async_abort(reason="missing_api_domain")
        port = zeroconf_properties.get("https_port") or discovery_info.port
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
