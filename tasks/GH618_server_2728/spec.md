# GH618_server_2728: fix(jellyfin): Add defensive checks for missing audio metadata — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/music-assistant/server

## PR Description

Fixes KeyError when Jellyfin MediaStreamInfos are missing Channels field.

Changes:
- Handle empty MediaStreams arrays gracefully
- Use .get() with defaults for Channels (stereo) and codec
- Maintain consistency with existing SampleRate/BitDepth patterns

This prevents crashes on libraries with incomplete Jellyfin metadata while using sensible defaults (2 channels, CD quality assumed).

Closes music-assistant/support#4447

## PR Review Comments

**[user]** on `music_assistant/providers/jellyfin/parsers.py`:

The new defensive behavior for missing or empty `MediaStreams` arrays lacks test coverage. Consider adding a test fixture with missing/empty MediaStreams to verify this edge case is handled correctly and returns an AudioFormat with `ContentType.UNKNOWN`.

**[user]** on `music_assistant/providers/jellyfin/parsers.py`:

The new defensive handling for missing `Channels` field lacks test coverage. Consider adding a test fixture with MediaStreams present but Channels field missing to verify the default value of 2 channels is applied correctly.

**[user]** on `tests/providers/jellyfin/test_parsers.py`:

Import of 'ITEM_KEY_MEDIA_CHANNELS' is not used.
```suggestion

```

**[user]** on `tests/providers/jellyfin/test_parsers.py`:

The test assertion `assert hasattr(result, "content_type")` is weak and doesn't verify the actual value. Consider asserting the expected value explicitly:
```python
assert result.content_type == ContentType.UNKNOWN
```
This ensures the function returns the expected `ContentType.UNKNOWN` when MediaStreams is empty, matching the implementation on line 180 of `parsers.py`.

**[user]** on `tests/providers/jellyfin/test_parsers.py`:

Import of 'JellyTrack' is not used.
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
