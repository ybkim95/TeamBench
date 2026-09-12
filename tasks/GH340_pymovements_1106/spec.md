# GH340_pymovements_1106: fix: Use GAZE_COORDS message to determine screen resolution — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pymovements/pymovements/issues/1086
- Repo: https://github.com/pymovements/pymovements

## Issue Description

## Current Behavior

`parse_eyelink()` currently uses the `DISPLAY_COORDS` message to detect the screen resolution. This is an optional message to define the resolution for Data Viewer, and some ASC files may not contain such a message. `from_asc()` results in an error in such cases.

## Expected Behavior

The `GAZE_COORDS` should be used because (as far as I can tell) it is always logged at the beginning of a trial. Theoretically, it might be possible to use a different resolution for each trial, but I don't expect this to be common, so we could just proceed in the same way as with the sampling rate (#887), where we warn the user about inconsistent resolution settings.

## Minimum acceptance criteria

- ASC files without `DISPLAY_COORDS` message parsed correctly

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Good catch, didn't know that. Handling it like sampling rate in #887 would be great for a start.

## PR Review Comments

**[user]** on `src/pymovements/gaze/_utils/parsing.py`:

instead of removing this regex completely, can you add the parsed info to the metadata dictionary? the regex group name and the metadata key can be simply `DISPLAY_COORDS`.

**[user]** on `src/pymovements/gaze/_utils/parsing.py`:

as above: instead of removing this completely, rename `resolution` to `DISPLAY_COORDS`.

**[user]** on `tests/unit/gaze/_utils/_parsing_test.py`:

instead of replacing this, just add a second line with the `GAZE_COORDS`

**[user]** on `tests/unit/gaze/io/asc_test.py`:

the error message is better with integers instead of floats, as the type of `Screen.width_px` is `int`.

**[user]** on `src/pymovements/gaze/io.py`:

Can you use `math.ceil()` instead of `round()`?

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
