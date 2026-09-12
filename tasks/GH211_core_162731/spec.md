# GH211_core_162731: Add handling of 2 IP addresses to homee — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/home-assistant/core/issues/156045
- Repo: https://github.com/home-assistant/core

## Issue Description

### The problem

1. I use Homee integration that is a part of HA Core (used to be 3rd party). Recently I noticed that 10-15 times a day, all Homee entities would be marked as Unavailable for a second and then would go back to available state. If I open the Activity page, all would be marked at the same second.
2. I stared looking and I noticed that before then, HA would reload the Homee integration and all entities would be re-added to the HA, thus marking them as Unavailable for a quick second
3. I traced that this happens because zeroconf requests the integration to reload.
4. I have zeroconf messages. What is there is: my Homee uses wifi and ethernet connection. eth is at ip 2.88 and wifi is at ip 2.227. I configured Homee integration to use 2.88 (ethernet) connection. But time to time zeroconf would see both with the same name and it would require integration to reload. Here are the zeroconf logs (stack trace is printed because I added that line to see who creates the async task):

```
2025-11-06 13:11:24.822 DEBUG (MainThread) [homeassistant.components.zeroconf.discovery] service_update: type=_ssh._tcp.local. name=homee-XXXXXXXXXX._ssh._tcp.local. state_change=Service
StateChange.Updated
2025-11-06 13:11:24.822 DEBUG (MainThread) [homeassistant.components.zeroconf.discovery] Discovered new device homee-XXXXXXXXXX._ssh._tcp.local. ZeroconfServiceInfo(ip_address=ZeroconfIP
v6Address('2003:fd:d719:9a1f:20e:c6ff:fe08:b6'), ip_addresses=[ZeroconfIPv6Address('2003:fd:d719:9a1f:20e:c6ff:fe08:b6')], port=22, hostname='homee-XXXXXXXXXX.local.', type='_ssh._tcp.lo
cal.', name='homee-XXXXXXXXXX._ssh._tcp.local.', properties={'': None})
2025-11-06 13:11:24.824 DEBUG (MainThread) [homeassistant.components.zeroconf.discovery] service_update: type=_ssh._tcp.local. name=homee-XXXXXXXXXX._ssh._tcp.local. state_change=Service
StateChange.Updated
2025-11-06 13:11:24.825 DEBUG (MainThread) [homeassistant.components.zeroconf.discovery] Discovered new device homee-XXXXXXXXXX._ssh._tcp.local. ZeroconfServiceInfo(ip_address=ZeroconfIP
v4Address('192.168.2.88'), ip_addresses=[ZeroconfIPv4Address('192.168.2.88'), ZeroconfIPv6Address('2003:fd:d719:9a1f:20e:c6ff:fe08:b6')], port=22, hostname='homee-XXXXXXXXXX.local.', typ
e='_ssh._tcp.local.', name='homee-XXXXXXXXXX._ssh._tcp.local.', properties={'': None})
2025-11-06 13:11:24.840 DEBUG (MainThread) [homeassistant.components.zeroconf.discovery] service_update: type=_ssh._tcp.local. name=homee-XXXXXXXXXX._ssh._tcp.local. state_change=Service
StateChange.Updated
2025-11-06 13:11:24.841 DEBUG (MainThread) [homeassistant.components.zeroconf.discovery] Discovered new device homee-XXXXXXXXXX._ssh._tcp.local. ZeroconfServiceInfo(ip_address=ZeroconfIP
v4Address('192.168.2.88'), ip_addresses=[ZeroconfIPv4Address('192.168.2.88'), ZeroconfIPv6Address('2003:fd:d719:9a1f:205:51ff:fe11:951c'), ZeroconfIPv6Address('2003:fd:d719:9a1f:20e:c6ff:f
e08:b6')], port=22, hostname='homee-XXXXXXXXXX.local.', type='_ssh._tcp.local.', name='homee-XXXXXXXXXX._ssh._tcp.local.', properties={'': None})
2025-11-06 13:11:24.886 DEBUG (MainThread) [homeassistant.components.zeroconf.discovery] service_update: type=_ssh._tcp.local. name=homee-XXXXXXXXXX._ssh._tcp.local. state_change=Service
StateChange.Updated
2025-11-06 13:11:24.887 DEBUG (MainThread) [homeassistant.components.zeroconf.discovery] Discovered new device homee-XXXXXXXXXX._ssh._tcp.local. ZeroconfServiceInfo(ip_address=ZeroconfIP
v4Address('192.168.2.227'), ip_addresses=[ZeroconfIPv4Address('192.168.2.227'), ZeroconfIPv4Address('192.168.2.88'), ZeroconfIPv6Address('2003:fd:d719:9a1f:205:51ff:fe11:951c'), ZeroconfIP
v6Address('2003:fd:d719:9a1f:20e:c6ff:fe08:b6')], port=22, hostname='homee-XXXXXXXXXX.local.', type='_ssh._tcp.local.', name='homee-XXXXXXXXXX._ssh._tcp.local.', properties={'': None})
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/usr/src/homeassistant/homeassistant/__main__.py", line 229, in <module>
    sys.exit(main())
  File "/usr/src/homeassistant/homeassistant/__main__.py", line 215, in main
    exit_code = runner.run(runtime_conf)
  File "/usr/src/homeassistant/homeassistant/runner.py", line 271, in run
    return loop.run_until_complete(setup_and_run_hass(runtime_config))
  File "/usr/local/lib/python3.13/asyncio/base_events.py", line 712, in run_until_complete
    self.run_forever()
  File "/usr/local/lib/python3.13/asyncio/base_events.py", line 683, in run_forever
    self._run_once()
  File "/usr/local/lib/python3.13/asyncio/base_events.py", line 2050, in _run_once
    handle._run()
  File "/usr/local/lib/python3.13/asyncio/events.py", line 89, in _run
    self._context.run(self._callback, *self._args)
  File "/usr/local/lib/python3.13/asyncio/selector_events.py", line 1244, in _read_ready
    self._protocol.datagram_received(data, addr)
  File "/usr/src/homeassistant/homeassistant/components/zeroconf/discovery.py", line 286, in async_service_update
    self._async_service_update(zeroconf, service_type, name)
  File "/usr/src/homeassistant/homeassistant/components/zeroconf/discovery.py", line 305, in _async_service_update
    self._async_process_service_update(async_service_info, service_type, name)
```

There are 2 IP addesses:
```
ip_addresses=[ZeroconfIPv4Address('192.168.2.227'), ZeroconfIPv4Address('192.168.2.88'), ZeroconfIPv6Address('2003:fd:d719:9a1f:205:51ff:fe11:951c'), ZeroconfIP v6Address('2003:fd:d719:9a1f:20e:c6ff:fe08:b6')]
```

I had to turn off wifi on Homee and now it all works correct. No reloads.

I am opening this issue to see is there a better way to handle this situation. 

### What version of Home Assistant Core has the issue?

2025.10.3

### What was the last working version of Home Assistant Core?

2025.10.3

### What type of installation are you running?

Home Assistant Container

### Integration causing the issue

Homee

### Link to integration documentation on our website

_No response_

### Diagnostics information

_No response_

### Example YAML snippet

```yaml

```

### Anything in the logs that might be useful for us?

```txt
Here is how the reloads would look in the logs:

2025-11-05 14:58:49.281 INFO (MainThread) [homeassistant.components.alarm_control_panel] Setting up homee.alarm_control_panel
2025-11-05 14:58:49.284 INFO (MainThread) [homeassistant.components.binary_sensor] Setting up homee.binary_sensor
2025-11-05 14:58:49.290 INFO (MainThread) [homeassistant.components.button] Setting up homee.button
2025-11-05 14:58:49.295 INFO (MainThread) [homeassistant.components.climate] Setting up homee.climate
2025-11-05 14:58:49.295 INFO (MainThread) [homeassistant.components.cover] Setting up homee.cover
2025-11-05 14:58:49.295 INFO (MainThread) [homeassistant.components.event] Setting up homee.event
2025-11-05 14:58:49.296 INFO (MainThread) [homeassistant.components.fan] Setting up homee.fan
2025-11-05 14:58:49.297 INFO (MainThread) [homeassistant.components.light] Setting up homee.light
2025-11-05 14:58:49.297 INFO (MainThread) [homeassistant.components.lock] Setting up homee.lock
2025-11-05 14:58:49.297 INFO (MainThread) [homeassistant.components.number] Setting up homee.number
2025-11-05 14:58:49.303 INFO (MainThread) [homeassistant.components.select] Setting up homee.select
2025-11-05 14:58:49.304 INFO (MainThread) [homeassistant.components.sensor] Setting up homee.sensor
2025-11-05 14:58:49.331 INFO (MainThread) [homeassistant.components.siren] Setting up homee.siren
2025-11-05 14:58:49.332 INFO (MainThread) [homeassistant.components.switch] Setting up homee.switch
2025-11-05 14:58:49.345 INFO (MainThread) [homeassistant.components.valve] Setting up homee.valve
2025-11-05 15:55:04.392 INFO (MainThread) [homeassistant.components.alarm_control_panel] Setting up homee.alarm_control_panel
2025-11-05 15:55:04.396 INFO (MainThread) [homeassistant.components.binary_sensor] Setting up homee.binary_sensor
2025-11-05 15:55:04.401 INFO (MainThread) [homeassistant.components.button] Setting up homee.button
2025-11-05 15:55:04.405 INFO (MainThread) [homeassistant.components.climate] Setting up homee.climate
2025-11-05 15:55:04.405 INFO (MainThread) [homeassistant.components.cover] Setting up homee.cover
2025-11-05 15:55:04.405 INFO (MainThread) [homeassistant.components.event] Setting up homee.event
2025-11-05 15:55:04.406 INFO (MainThread) [homeassistant.components.fan] Setting up homee.fan
2025-11-05 15:55:04.406 INFO (MainThread) [homeassistant.components.light] Setting up homee.light
2025-11-05 15:55:04.407 INFO (MainThread) [homeassistant.components.lock] Setting up homee.lock
2025-11-05 15:55:04.407 INFO (MainThread) [homeassistant.components.number] Setting up homee.number
2025-11-05 15:55:04.413 INFO (MainThread) [homeassistant.components.select] Setting up homee.select
2025-11-05 15:55:04.413 INFO (MainThread) [homeassistant.components.sensor] Setting up homee.sensor
2025-11-05 15:55:04.440 INFO (MainThread) [homeassistant.components.siren] Setting up homee.siren
2025-11-05 15:55:04.441 INFO (MainThread) [homeassistant.components.switch] Setting up homee.switch
2025-11-05 15:55:04.454 INFO (MainThread) [homeassistant.components.valve] Setting up homee.valve
2025-11-05 16:51:19.482 INFO (MainThread) [homeassistant.components.alarm_control_panel] Setting up homee.alarm_control_panel
2025-11-05 16:51:19.485 INFO (MainThread) [homeassistant.components.binary_sensor] Setting up homee.binary_sensor
2025-11-05 16:51:19.491 INFO (MainThread) [homeassistant.components.button] Setting up homee.button
2025-11-05 16:51:19.495 INFO (MainThread) [homeassistant.components.climate] Setting up homee.climate
2025-11-05 16:51:19.496 INFO (MainThread) [homeassistant.components.cover] Setting up homee.cover
2025-11-05 16:51:19.496 INFO (MainThread) [homeassistant.components.event] Setting up homee.event
2025-11-05 16:51:19.497 INFO (MainThread) [homeassistant.components.fan] Setting up homee.fan
2025-11-05 16:51:19.497 INFO (MainThread) [homeassistant.components.light] Setting up homee.light
2025-11-05 16:51:19.498 INFO (MainThread) [homeassistant.components.lock] Setting up homee.lock
2025-11-05 16:51:19.498 INFO (MainThread) [homeassistant.components.number] Setting up homee.number
2025-11-05 16:51:19.504 INFO (MainThread) [homeassistant.components.select] Setting up homee.select
2025-11-05 16:51:19.505 INFO (MainThread) [homeassistant.components.sensor] Setting up homee.sensor
2025-11-05 16:51:19.538 INFO (MainThread) [homeassistant.components.siren] Setting up homee.siren
2025-11-05 16:51:19.539 INFO (MainThread) [homeassistant.components.switch] Setting up homee.switch
2025-11-05 16:51:19.553 INFO (MainThread) [homeassistant.components.valve] Setting up homee.valve
```

### Additional information

_No response_

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hey there [user], mind taking a look at this issue as it has been labeled with an integration (`homee`) you are listed as a [code owner](https://github.com/home-assistant/core/blob/dev/CODEOWNERS#L673) for? Thanks!

<details>
<summary>Code owner commands</summary>

Code owners of `homee` can trigger bot actions by commenting:

- `@home-assistant close` Closes the issue.
- `@home-assistant rename Awesome new title` Renames the issue.
- `@home-assistant reopen` Reopen the issue.
- `@home-assistant unassign homee` Removes the current integration label and assignees on the issue, add the integration domain after the command.
- `@home-assistant add-label needs-more-information` Add a label (needs-more-information, problem in dependency, problem in custom component) to the issue.
- `@home-assistant remove-label needs-more-information` Remove a label (needs-more-information, problem in dependency, problem in custom component) on the issue.

</details>

<sub><sup>(message by CodeOwnersMention)</sup></sub>

---

[homee documentation](https://www.home-assistant.io/integrations/homee)
[homee source](https://github.com/home-assistant/core/tree/dev/homeassistant/components/homee)
<sub><sup>(message by IssueLinks)</sup></sub>

### Comment 2 ([user]):

I'm not sure if we can handle devices with multiple IP-Addresses in HA.
I try to find out.

### Comment 3 ([user]):

It should be possible - hope to get on it soon.

### Comment 4 ([user]):

Still on my todo list, but no time currently

### Comment 5 ([user]):

[user]: In the zeroconf logs, where it says `name='homee-XXXXXXXXXX._ssh._tcp.local`,  did you exchange the ID with XXX, or ist it in the logs that way?

I would like to know, if homee broadcasts the same name for both IP-Addresses.

If the logs are that way, are you able to add a line logging the name in the homee config-flow in `async def async_step_zeroconf`? it would be `discovery_info.hostname[6:18]`

### Comment 6 ([user]):

I am confident it was me who updated the real ID with XXXX. There was an ID of the Homee as I recall. Mine is 00055111.... (replaced last 4 symbols with .)

## PR Review Comments

**[user]** on `homeassistant/components/homee/config_flow.py`:

Typing is nice, but not when they can be inferred. :)

**[user]** on `homeassistant/components/homee/config_flow.py`:

I think, instead of building your own logic, you could use maybe the `_async_abort_entries_match` method? It really does what the name of method calls it: aborting when entries match. For instance code can be made like such:

```py
self._async_abort_entries_match(
            {CONF_HOST: user_input[CONF_HOST]}
        )
```

If I understand your config flow well, this is basically what you want to prevent. If you this is applicable to you, please adapt your code and that will make it perfectly in line with other integrations and methods the Core has to offer. :)

**[user]** on `homeassistant/components/homee/config_flow.py`:

Indeed mypy doesn't complain.
I added this, because vscode didn't pick up the runtime_data structure.

**[user]** on `homeassistant/components/homee/config_flow.py`:

Hmm, not sure here. The description says `Abort if current entries match all data.`
The case here does not match all data, since the IP is different.

**[user]** on `homeassistant/components/homee/config_flow.py`:

Yea this is the one exception where we do need custom logic.

One thing to note is, please also add that the config entry state needs to be loaded in order to work

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
