# GH1048_keras_22294: fix(progbar): handle target=0 to prevent crash with empty dataset — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/keras-team/keras/issues/19687
- Repo: https://github.com/keras-team/keras

## Issue Description

I accidentally filtered out all examples and tried to evaluate on an empty dataset.
Was getting a confusing crash in the progress bar code as `self.target == 0`.

See [here](https://github.com/keras-team/keras/blob/master/keras/src/utils/progbar.py#L119)

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Could you please share an example to reproduce the reported behavior. Thanks

### Comment 2 ([user]):

So `self.target` was set to 0 in `keras/src/utils/progbar.py`, as i passed in a dataset with all examples filtered out :face_exhaling:.

`numdigits = int(math.log10(self.target)) + 1` then tries to take log of 0.

### Comment 3 ([user]):

Hi [user], I don't think throwing an error is unreasonable in this situation. What behavior would you expect from Keras?

### Comment 4 ([user]):

I think just a warning "dataset is empty"?

I can imagine some complicated thing where someone filters different examples each epoch. The rest of the code doesn't seem to mind empty datasets.

## PR Review Comments

**[user]** on `keras/src/utils/progbar.py`:

![medium](https://www.gstatic.com/codereviewagent/medium-priority.svg)

The condition `self.target is not None and self.target > 0` is now used in three places within this method (here, and on lines 141 and 189). To improve code clarity and maintainability by avoiding repetition, consider defining a variable for this check before the `if self.verbose == 1:` block and reusing it.

For example:
```python
# In update() method, around line 111
has_positive_target = self.target is not None and self.target > 0

if self.verbose == 1:
    # ...
    # line 122
    if has_positive_target:
        # ...
    # ...
    # line 141
    if has_positive_target and not finalize:
        # ...
elif self.verbose == 2:
    # line 189
    if finalize and has_positive_target:
        # ...
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
