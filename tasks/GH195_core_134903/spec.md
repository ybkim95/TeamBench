# GH195_core_134903: Fix playing TTS and local media source over DLNA — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/home-assistant/core/issues/139580
- Repo: https://github.com/home-assistant/core

## Issue Description

### The problem

If I try TTS or playing a local media file on a DLNA compatible renderer, it doesn't work and shows an error in the log:
```
[homeassistant.components.dlna_dmr] Error during call async_play_media: UpnpActionResponseError('Error during async_call(), status: 500, upnp error: 716 (Resource not found)')
```

Right before the `Resource not found` error above, the HA logs show that there's a HEAD request coming in from the speaker and that fails with an HTTP 500 error. I also saw somewhere someone hinting that DLNA renderers might send a HEAD request before sending the GET one.

There are several reports around the net about this or related DLNA problems, dating back to 2022:
- #81162
- #111078
- [Media Cast / DLNA not working with Samsung TVs or Smart Monitors](https://community.home-assistant.io/t/media-cast-dlna-not-working-with-samsung-tvs-or-smart-monitors/693075)
- [DLNA Digital Media Renderer Not Working](https://www.reddit.com/r/homeassistant/comments/1fk8ase/dlna_digital_media_renderer_not_working)

Most replies to such issues end up pointing to configuring `media_dirs` ([Setting up local media sources](https://www.home-assistant.io/more-info/local-media/setup-media), [Media Source](https://next.home-assistant.io/integrations/media_source/)), but nothing works, leading to complains about unclear documentation: https://github.com/home-assistant/home-assistant.io/issues/28940.

Also, [the documentation says there might be hiccups with Samsung devices](https://next.home-assistant.io/integrations/dlna_dmr), but that might be exactly because of the missing support for HEAD requests:
> Note that some devices, such as Samsung TVs, are rather picky about the source used to play from. The TTS action might not work in combination with these devices. 

**UPDATE 2025-03-01**
~~However, I haven't tried streaming videos yet. I'll check it later and submit a separate PR if necessary, and it seems to also be an issue like #67618.~~
Videos work with these changes and I also included a fix for local images.

I created a PR ((withheld: the upstream fix is not part of the task)) which adds support for `HEAD` requests for local_source media, image, and TTS (also allowing signed requests for `HEAD`), which fixes these problems and likely related issues mentioned above. I'd appreciate a review.

### What version of Home Assistant Core has the issue?

core-2025.2.5

### What was the last working version of Home Assistant Core?

_No response_

### What type of installation are you running?

Home Assistant OS

### Integration causing the issue

image, media_source, tts, auth

### Link to integration documentation on our website

https://www.home-assistant.io/integrations/media_source/

### Diagnostics information

_No response_

### Example YAML snippet

```yaml

```

### Anything in the logs that might be useful for us?

```txt
[homeassistant.components.dlna_dmr] Error during call async_play_media: UpnpActionResponseError('Error during async_call(), status: 500, upnp error: 716 (Resource not found)')
```

### Additional information

_No response_

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hey there [user], mind taking a look at this issue as it has been labeled with an integration (`dlna_dmr`) you are listed as a [code owner](https://github.com/home-assistant/core/blob/dev/CODEOWNERS#L349) for? Thanks!

<details>
<summary>Code owner commands</summary>

Code owners of `dlna_dmr` can trigger bot actions by commenting:

- `@home-assistant close` Closes the issue.
- `@home-assistant rename Awesome new title` Renames the issue.
- `@home-assistant reopen` Reopen the issue.
- `@home-assistant unassign dlna_dmr` Removes the current integration label and assignees on the issue, add the integration domain after the command.
- `@home-assistant add-label needs-more-information` Add a label (needs-more-information, problem in dependency, problem in custom component) to the issue.
- `@home-assistant remove-label needs-more-information` Remove a label (needs-more-information, problem in dependency, problem in custom component) on the issue.

</details>

<sub><sup>(message by CodeOwnersMention)</sup></sub>

---

[dlna_dmr documentation](https://www.home-assistant.io/integrations/dlna_dmr)
[dlna_dmr source](https://github.com/home-assistant/core/tree/dev/homeassistant/components/dlna_dmr)
<sub><sup>(message by IssueLinks)</sup></sub>

### Comment 2 ([user]):

Hey there [user], mind taking a look at this issue as it has been labeled with an integration (`media_source`) you are listed as a [code owner](https://github.com/home-assistant/core/blob/dev/CODEOWNERS#L914) for? Thanks!

<details>
<summary>Code owner commands</summary>

Code owners of `media_source` can trigger bot actions by commenting:

- `@home-assistant close` Closes the issue.
- `@home-assistant rename Awesome new title` Renames the issue.
- `@home-assistant reopen` Reopen the issue.
- `@home-assistant unassign media_source` Removes the current integration label and assignees on the issue, add the integration domain after the command.
- `@home-assistant add-label needs-more-information` Add a label (needs-more-information, problem in dependency, problem in custom component) to the issue.
- `@home-assistant remove-label needs-more-information` Remove a label (needs-more-information, problem in dependency, problem in custom component) on the issue.

</details>

<sub><sup>(message by CodeOwnersMention)</sup></sub>

---

[media_source documentation](https://www.home-assistant.io/integrations/media_source)
[media_source source](https://github.com/home-assistant/core/tree/dev/homeassistant/components/media_source)
<sub><sup>(message by IssueLinks)</sup></sub>

### Comment 3 ([user]):

There hasn't been any activity on this issue recently. Due to the high number of incoming GitHub notifications, we have to clean some of the old issues, as many of them have already been resolved with the latest updates.
Please make sure to update to the latest Home Assistant version and check if that solves the issue. Let us know if that works for you by adding a comment 👍
This issue has now been marked as stale and will be closed if no further activity occurs. Thank you for your contributions.

## PR Review Comments

**[user]** on `homeassistant/components/media_source/local_source.py`:

This doesn't appear to return the path, as the docstring says it should.

**[user]** on `homeassistant/components/image/__init__.py`:

It might be worth setting the `Content-Length` header when it's know, to let some players seek within the file.

**[user]** on `homeassistant/components/image/__init__.py`:

... I'll leave this comment here, even though it's on the `image` source, as it applies to all media types.

**[user]** on `tests/components/image/test_init.py`:

It would be a good idea to check the expected metadata (Content Type, Content Length if applicable) are returned.

**[user]** on `homeassistant/components/image/__init__.py`:

I think it makes sense, although I couldn't find any other component doing this. I'm adding it regardless.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
