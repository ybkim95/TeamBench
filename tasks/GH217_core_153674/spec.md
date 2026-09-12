# GH217_core_153674: Portainer fix multiple environments & containers — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/home-assistant/core/issues/153589
- Repo: https://github.com/home-assistant/core

## Issue Description

### The problem

I have imported three docker endpoints into Home Assistant via the new Portainer integration.
Everything works fine except one thing:
Two endpoints have containers installed with identical container names, in my case `portaineragent` (which obviously are running the portainer agent).
However, the Portainer integration does only show one of these two containers. Could it be that this is because of the identical container names?
Thanks!

### What version of Home Assistant Core has the issue?

core-2025.10.0

### What was the last working version of Home Assistant Core?

core-2025.10.0

### What type of installation are you running?

Home Assistant OS

### Integration causing the issue

Portainer

### Link to integration documentation on our website

https://www.home-assistant.io/integrations/portainer

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

Hey there [user], mind taking a look at this issue as it has been labeled with an integration (`portainer`) you are listed as a [code owner](https://github.com/home-assistant/core/blob/dev/CODEOWNERS#L1207) for? Thanks!

<details>
<summary>Code owner commands</summary>

Code owners of `portainer` can trigger bot actions by commenting:

- `@home-assistant close` Closes the issue.
- `@home-assistant rename Awesome new title` Renames the issue.
- `@home-assistant reopen` Reopen the issue.
- `@home-assistant unassign portainer` Removes the current integration label and assignees on the issue, add the integration domain after the command.
- `@home-assistant add-label needs-more-information` Add a label (needs-more-information, problem in dependency, problem in custom component) to the issue.
- `@home-assistant remove-label needs-more-information` Remove a label (needs-more-information, problem in dependency, problem in custom component) on the issue.

</details>

<sub><sup>(message by CodeOwnersMention)</sup></sub>

---

[portainer documentation](https://www.home-assistant.io/integrations/portainer)
[portainer source](https://github.com/home-assistant/core/tree/dev/homeassistant/components/portainer)
<sub><sup>(message by IssueLinks)</sup></sub>

### Comment 2 ([user]):

Thanks for reporting. They should be allowed, since the endpoint is unique, as well as the containerID. Can you maybe share some more details, like is it marked unavailable or an error is thrown?

### Comment 3 ([user]):

Unfortunately there are no errors thrown on HAOS core logs.
The portainer UI shows that the container is running fine:

<img width="1133" height="307" alt="Image" src="https://github.com/user-attachments/assets/5a55a042-499d-4e10-8286-645d93114ff4" />

On HAOS Portainer integration only the agent running on debian02 is showing up, the one running on debian03 is missing.
Which is weird, because there is another container running on debian03 and it is showing up fine on HAOS Portiner integration.

EDIT: Oh, I just mentioned there is a fix being pushed?

### Comment 4 ([user]):

I think you've made a valid point here. I am working a new fix. The stale states were caused due to another reason (which has been patched in version 2025.10.1). :)

### Comment 5 ([user]):

Same here. I have some containers with the same name on multiple machines - "portainer_agent" for example - and this integration shows only one of them. "glances" is another I have on multiple servers.

### Comment 6 ([user]):

I have duplicate containers across instances of portainer (for instance watchtower) which are currently getting named sequentially.   

This could be addressed by, instead of one device with one entity for each container and endpoint, making each endpoint  (instance of portainer) the device, then each container would be an entity of that device, with the name of the name of the container prefixed by the device name. 

For example, if I  have Plex and Watchtower on an instance of Portainer named Media and Radarr and Watchtower on Portainer named Downloader, it yields 6 devices (1 for each container and 1 for each endpoint), including watchtower and watchtower_2.  With my suggestion, create the device with the Endpoint name (media and downloader) and create entities for each container, which would then be unique per device (i.e. media_watchtower & downloader_watchtower), as well as any additional entities unique to that endpoint.

### Comment 7 ([user]):

Hmm… is this considered as solved in HAOS 2025.11? Because the issue still persists on 2025.11 in my case, even after re-importing the according Portainer instance.
Thanks!

### Comment 8 ([user]):

No, the PR is still under review...

### Comment 9 ([user]):

There hasn't been any activity on this issue recently. Due to the high number of incoming GitHub notifications, we have to clean some of the old issues, as many of them have already been resolved with the latest updates.
Please make sure to update to the latest Home Assistant version and check if that solves the issue. Let us know if that works for you by adding a comment 👍
This issue has now been marked as stale and will be closed if no further activity occurs. Thank you for your contributions.

### Comment 10 ([user]):

> No, the PR is still under review...

For 3 months?

## PR Review Comments

**[user]** on `homeassistant/components/portainer/__init__.py`:

Using `assert` for runtime validation is not recommended in production code as it can be disabled with optimization flags. Consider using a proper conditional check with error handling or raising a more descriptive exception.
```suggestion
            if parent_device is None:
                raise RuntimeError(f"Parent device with id {device.via_device_id} not found in device registry")
```

**[user]** on `homeassistant/components/portainer/__init__.py`:

The nested string splitting logic is complex and fragile. Consider using a more robust approach or adding comments to explain the expected format and what each part represents.
```suggestion
                # The expected format of entity.unique_id is: <something>_<rest>
                # where <rest> is expected to be: <something>_<rest_tail>
                unique_id_parts = entity.unique_id.split("_", 1)
                if len(unique_id_parts) != 2:
                    _LOGGER.warning("Unexpected unique_id format: %s", entity.unique_id)
                    continue
                _, rest = unique_id_parts
                rest_parts = rest.split("_", 1)
                if len(rest_parts) != 2:
                    _LOGGER.warning("Unexpected rest format in unique_id: %s", rest)
                    continue
                _, rest_tail = rest_parts
```

**[user]** on `homeassistant/components/portainer/__init__.py`:

why isn't this a minor version migration?

**[user]** on `homeassistant/components/portainer/__init__.py`:

the identifiers is not 100% sure to have the first one as the one for the integration

**[user]** on `homeassistant/components/portainer/__init__.py`:

you can move this outside of the for loop

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
