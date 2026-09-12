# GH347_pymovements_1359: fix: preserve all columns in `data` on `Events` init — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pymovements/pymovements/issues/1349
- Repo: https://github.com/pymovements/pymovements

## Issue Description

When cloning an `Events` object that has event properties added via `add_event_properties()`, the properties are lost. The `clone()` method does not preserve additional event property columns.

https://github.com/pymovements/pymovements/blob/43bfff286d1b91a4c50c9ed124506a2cf018cd34/src/pymovements/events/events.py#L182-L183

how I fixed it locally
```python
if self.trial_columns is not None:
      # check what other columns exist in the dataframe, without minimal schema and trial cols
      other_cols = [
          col for col in self.frame.columns
          if col not in self.trial_columns and col not in self._minimal_schema
      ]
      self.frame = self.frame.select([*self.trial_columns, *self._minimal_schema.keys(), *other_cols])
```

## Current Behavior
- if I run gaze.clone(), on a gaze instance which already includes event properties, the properties are overwritten and are not cloned together with the rest of the gaze object

## Expected Behavior
The cloned Events object should preserve all columns, including event properties, in the same order as the original.

## Minimum acceptance criteria
- `clone()` preserves all event property columns
- Column order is maintained
- Data integrity is preserved for all columns

## Failure Information (for bugs)

### Steps to Reproduce

- Creating an Events instance with trial data
- Adding event properties via `add_event_properties()`
- Calling `clone()` on the Events object
- -> The cloned Events object is missing the additional property columns

## Context

In `Events.__init__()` at lines 182-183, when `trial_columns` is set, the code reorders columns using:

https://github.com/pymovements/pymovements/blob/43bfff286d1b91a4c50c9ed124506a2cf018cd34/src/pymovements/events/events.py#L182-L183

This selects only trial columns and minimal schema columns, silently dropping any additional columns added via `add_event_properties()`. Any workflow using `clone()` on Events with properties will lose data silently.

## Checklist

- [x] I am running the latest version
- [x] I checked the documentation and found no answer
- [x] I checked to make sure that this issue has not already been filed
- [x] I have provided sufficient information for the team

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

[user] Thank you for the valuable report of this silent data loss! The snippet made it easy to analyse what happens, still, I modified it to make it more robust.

The original code only selected trial columns and minimal schema columns, dropping any additional columns (like event properties that were added via `add_event_properties()`). The suggested fix used `self._minimal_schema` which is a dictionary, not a set of column names. When you check `col not in self._minimal_schema`, you're checking if `col` is a dictionary key, which works but is less explicit, compared to `self._minimal_schema.keys()`.
The modified approach directly works with sets which is in O(1) instead of O(n) for lists. This approach also preserves order and is a bit more readable, imo :)

## PR Review Comments

**[user]** on `tests/unit/events/events_test.py`:

By initiatilizing your events this way:

```python
events = Events(
    data=pl.from_dict({
        'name': ['fixation', 'saccade', 'fixation'],
        'onsets': [100, 200, 300],
        'offsets': [150, 250, 350],
        'trial_id': [1, 1, 2],
        'custom_property': [1.5, 2.5, 1.5],
    },
    trial_columns='trial_id',
)
```

you omit test dependencies by not calling any unrelated pymovements methods.

**[user]** on `tests/unit/events/events_test.py`:

these asserts are redundant as already tested by `assert_frame_equal()`

**[user]** on `tests/unit/events/events_test.py`:

the way this test is written it is actually not a unit test, but a functional test (also called acceptance test), that tests the interplay between calling different units.

Although there are quite a lot of old tests in `tests/unit/` written in that way, I would like avoid that in the future and put them where they belong in `tests/functional` (or alternatively `tests/functional/regressions`, `tests/regressions`, ).

the test at hand however can also be just subsumed as a test parameter to the already existing test function `test_init_expected_df` by using the dataframe from my proposed `pl.from_dict()` codeblock

**[user]** on `tests/unit/events/events_test.py`:

although the first one might not be redundant, as it checks the `Events.columns` field not the dataframe

**[user]** on `tests/unit/events/events_test.py`:

True, thanks for the hint!

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
