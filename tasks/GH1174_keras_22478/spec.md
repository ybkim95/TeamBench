# GH1174_keras_22478: [Fix] rgb_to_hsv does not validate channel count for Keras Input with channels_first — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/keras-team/keras

## PR Description

Fixes issues: #22472 #22473 

Root cause:
RGBToHSV / HSVToRGB did not check channel count = 3 in compute_output_spec.
So, Symbolic keras.Input allowed invalid channels (especially channels_first), while eager execution failed later.

Solution:
Added explicit channel-count validation in ```compute_output_spec()``` for both ops, handling channels_first correctly.
Regression tests to ensure invalid-channel inputs raise errors for both rgb_to_hsv and hsv_to_rgb.

## PR Review Comments

**[user]** on `keras/src/ops/image.py`:

![high](https://www.gstatic.com/codereviewagent/high-priority.svg)

The special handling for 3D `channels_first` tensors is brittle and can lead to incorrect validation for valid shapes.

Specifically, for a shape like `(None, H, W)`, the logic incorrectly reassigns `channels_axis` to `-2`, assuming the second dimension (`H`) represents channels. This is incorrect for the `channels_first` format, where the channel axis for a 3D tensor is always `0` (or `-3`).

This heuristic leads to incorrect failures for valid symbolic shapes like `(None, 20, 20)`, which should be interpreted as `(C, H, W)` with an unknown channel count (`C=None`). The current code would incorrectly treat it as having 20 channels and raise an error.

A more robust approach is to consistently use the correct channel axis and let the `channels is not None` check handle cases with dynamic channel dimensions. This avoids making risky assumptions about ambiguous shapes.

This feedback also applies to the identical logic in `HSVToRGB.compute_output_spec` (lines 184-194).

```suggestion
        channels_axis = -1 if self.data_format == "channels_last" else -3
        channels = images_shape[channels_axis]
        if channels is not None and channels != 3:
            raise ValueError(
                "Input images must have 3 channels, but received images with "
                f"{channels} channels."
            )
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
