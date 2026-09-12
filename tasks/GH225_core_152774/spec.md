# GH225_core_152774: Add dc:title support for Sonos sharelinks — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/home-assistant/core/issues/152305
- Repo: https://github.com/home-assistant/core

## Issue Description

### The problem

The media_playlist attribute is missing for Sonos devices, when (Spotify) playlists are triggered by Home Assistant. When the same playlists are started by the Sonos App, the media_playlist attribute is filled correctly.

### What version of Home Assistant Core has the issue?

core-2025.8.3

### What was the last working version of Home Assistant Core?

_No response_

### What type of installation are you running?

Home Assistant OS

### Integration causing the issue

Sonos

### Link to integration documentation on our website

https://www.home-assistant.io/integrations/sonos/

### Diagnostics information

_No response_

### Example YAML snippet

```yaml

```

### Anything in the logs that might be useful for us?

```txt

```

### Additional information

The rootcause is, that the SoCo Library DIDL-Lite metadata template is missing dc:title and parentID.
I implemented a workaround or potential solution in this branch:
https://github.com/SoCo/SoCo/compare/master...KarstenBade:SoCo:playlist_fix?diff=split&w
In this Branch the SoCo Lib takes the playlist title by kwargs.get("extra", {}).get("playlist_title", "") and sends the correct DIDL-Lite metadata. The Sonos Integration also needed a small patch to hand over the kwargs.

I would like to develop the official bugfix / feature enhancement myself, but wanted to discuss a clean architecture first. Therefor I decided to create this ticket for an alignment of the cleanest possible solution.

How are your thoughts? Is kwargs the correct place to hand over the playlist title?

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hey there [user], [user], mind taking a look at this issue as it has been labeled with an integration (`sonos`) you are listed as a [code owner](https://github.com/home-assistant/core/blob/dev/CODEOWNERS#L1478) for? Thanks!

<details>
<summary>Code owner commands</summary>

Code owners of `sonos` can trigger bot actions by commenting:

- `@home-assistant close` Closes the issue.
- `@home-assistant rename Awesome new title` Renames the issue.
- `@home-assistant reopen` Reopen the issue.
- `@home-assistant unassign sonos` Removes the current integration label and assignees on the issue, add the integration domain after the command.
- `@home-assistant add-label needs-more-information` Add a label (needs-more-information, problem in dependency, problem in custom component) to the issue.
- `@home-assistant remove-label needs-more-information` Remove a label (needs-more-information, problem in dependency, problem in custom component) on the issue.

</details>

<sub><sup>(message by CodeOwnersMention)</sup></sub>

---

[sonos documentation](https://www.home-assistant.io/integrations/sonos)
[sonos source](https://github.com/home-assistant/core/tree/dev/homeassistant/components/sonos)
<sub><sup>(message by IssueLinks)</sup></sub>

### Comment 2 ([user]):

An interesting issue.  I'd expect the speaker to send the same data regardless of what application initiates playing the playlist.  That seems to not be the case?  Your change implies the by sending different metadata to the speaker when requesting the playlist change the results the speaker sends?

### Comment 3 ([user]):

[user] the enqueued_transport_uri_meta_data can not be interpreted at the moment, when the playlist was started by the SoCo Lib. 
So this part is only working, when the playlist was sent by Sonos App:
https://github.com/home-assistant/core/blob/22ea269ed84fd7e47b52acbac0385760f1711290/homeassistant/components/sonos/media.py#L164-L166

And the rootcause is, that the metadata sent by SoCo is not containing the title: 
https://github.com/SoCo/SoCo/blob/6cbc67a2a9eb3b89926fa774a48bfec6c93b7d8c/soco/plugins/sharelink.py#L242

I already confirmed, that this can be solved by adapting the metadata template, but  am unsure how to solve it cleanly.
Should SoCo get the Playlist title itself, based on the URL?
Should the add_share_link_to_queue API be extended by a title?
Or my proposal: Send the title in kwargs

## PR Review Comments

**[user]** on `homeassistant/components/sonos/media_player.py`:

Using `pop()` on `kwargs.get("extra", {})` will modify a temporary dictionary and not affect the original `kwargs["extra"]`. This should be `kwargs.get("extra", {}).get("title", "")` instead to safely extract the title without side effects.
```suggestion
            title = kwargs.get("extra", {}).get("title", "")
```

**[user]** on `homeassistant/components/sonos/media_player.py`:

Please add a test to test_media_player.py to verify this information can be passed in from a service call.

**[user]** on `homeassistant/components/sonos/media_player.py`:

There is an existing test:  test_play_media_share_link_add which this could be added to.

**[user]** on `homeassistant/components/sonos/media_player.py`:

I adapted the implementation to use get instead of pop.

**[user]** on `homeassistant/components/sonos/media_player.py`:

Thanks for pointing this out.
I added the title to all sharelink related tests:

`test_play_media_share_link_add`
`test_play_media_share_link_next`
`test_play_media_share_link_play`
`test_play_media_share_link_replace`

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
