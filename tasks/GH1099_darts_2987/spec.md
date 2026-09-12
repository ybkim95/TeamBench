# GH1099_darts_2987: Fix/max_samples_per_ts — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/unit8co/darts/issues/2986
- Repo: https://github.com/unit8co/darts

## Issue Description

**Describe the bug**
According to the doctoring, `max_samples_per_ts` in `TorchForecastingModel.fit()` (`ShiftedTorchTrainingDataset`) should be the upper bound of number of samples PER time series, not the number of samples extracted.

The bug occurs when we have one or multiple time series containing less than `max_samples_per_ts` samples and the actual "extractable upper bound" is being ignored. Instead, `max_samples_per_ts` samples are always extracted per time series.

**To Reproduce**

```python
from darts.utils.data import ShiftedTorchTrainingDataset
from darts.utils.timeseries_generation import linear_timeseries

series = linear_timeseries(length=1000)
dataset = ShiftedTorchTrainingDataset(
    series,
    input_chunk_length=11,
    output_chunk_length=13,
    max_samples_per_ts=5000,
)
print(f"Number of samples in dataset: {len(dataset)}")
# Number of samples in dataset: 5000
```


**Expected behavior**
The dataset should have 1000-(13+1)+1=987 samples, not 5,000. `max_samples_per_ts` should set the upper bound for the number of samples and not become the number of samples itself.


**System (please complete the following information):**
 - Python version: 3.13
 - darts version: from source (latest 0.40.0)

**Additional context**
Add any other context about the problem here.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hi [user], thanks for bringing this to our attention!

I agree that the current implementation contradicts the behavior described in the docstring, as it treats `max_samples_per_ts` as a fixed target for the number of samples per series instead of an upper bound.

To align the code with the documentation, I suggest the following fix in the `__init__` method to ensure `max_samples_per_ts` is always capped by the maximum extractable samples across the series:

```python
size_of_both_chunks = max(input_chunk_length, shift + output_chunk_length)  # Already existing line

# read all time series to get the maximum possible samples available
actual_max = max(len(ts) for ts in series) - size_of_both_chunks + 1
actual_max_samples = ceil(actual_max / stride)

if actual_max <= 0:
    raise_log(
        ValueError(
            f"The input `series` are too short to extract even a single sample. "
            f"Expected min length: `{size_of_both_chunks}`, received max length: "
            f"`{max_samples_per_ts + size_of_both_chunks - 1}`."
        )
    )

if max_samples_per_ts is None:
    max_samples_per_ts = actual_max_samples
else:
    # The Fix: Ensure max_samples_per_ts acts as a true upper bound
    max_samples_per_ts = min(max_samples_per_ts, actual_max_samples)
```
What do you think of this solution? If it looks good to you, would you like to submit a PR for this? If not, I’d be happy to implement the fix myself. Thanks again for helping improve Darts! 🚀

### Comment 2 ([user]):

[user] 

Thanks for the quick response! Your solution seems most reasonable to me. Please feel free to raise the PR as you deserve the credits for the fix.

## PR Review Comments

**[user]** on `CHANGELOG.md`:

refer to PR number here :) (#2987)
```suggestion
- Fixed a bug in `TorchTrainingDataset` where `max_samples_per_ts` was not acting as an upper bound on the number of samples per time series. Now `max_samples_per_ts` correctly acts as an upper bound, capping the dataset size at the actual number of samples that can be extracted from the longest series. [#2987]((withheld: the upstream fix is not part of the task)) by [Dustin Brunner](https://github.com/brunnedu).
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
