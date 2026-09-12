# GH474_server_2565: Fix Squeezelite sample rate for multi client streams — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/music-assistant/server

## PR Description

Previously, squeezelite players in sync groups were limited to 
44.1kHz/16-bit output even when configured to support higher 
sample rates and bit depths (e.g., 96kHz/24-bit). Individual 
players worked correctly, but grouping them caused quality 
degradation.

The issue was in _serve_multi_client_stream() which created 
AudioFormat with only the content type, causing sample rate 
and bit depth to default to minimum values.

This fix:
- Uses streams controller's get_output_format() to properly 
  determine output format based on player capabilities
- Preserves original content format through MultiClientStream
- Passes content format to get_output_format() for proper 
  quality negotiation

Grouped players now output at min(content_format, player_capability),
matching the behavior of individual players.

Fixes: [music-assistant/server#<issue_number>](https://github.com/music-assistant/support/issues/4300)

## PR Review Comments

**[user]** on `music_assistant/providers/squeezelite/multi_client_stream.py`:

why is this ? shouldn't be needed. multiclientstream is alway just pcm

**[user]** on `music_assistant/providers/squeezelite/player.py`:

eeks what is this

**[user]** on `music_assistant/providers/squeezelite/player.py`:

I dont really see the benefit of adding an extra variable here

**[user]** on `music_assistant/providers/squeezelite/player.py`:

???

**[user]** on `music_assistant/providers/squeezelite/player.py`:

```suggestion
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
