# GH1017_scikit_learn_21654: [MRG] FIX segmentation fault on memory mapped contiguous memoryview — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/scikit-learn/scikit-learn

## PR Description

#### What does this implement/fix? Explain your changes.
Hunting for the segmentation fault in (withheld: the upstream fix is not part of the task)#issuecomment-967296818.

Edit: The fix is to not use joblib for creating readonly (memory mapped) arrays, but to use `np.memmap` instead, at least where aligned arrays are required.

#### Any other comments?
A segmentation fault happens on `Ubuntu_Bionic py37_conda_forge_openblas_ubuntu_1804` when a memory mapped readonly array (via joblib) is passed to a contiguous memoryview in Cython.

## PR Review Comments

**[user]** on `sklearn/utils/_readonly_array_wrapper.pyx`:

The expression in the docstring below should be updated accordingly to also use `[::1]` instead of `[:]`

**[user]** on `sklearn/utils/tests/test_readonly_wrapper.py`:

Nitpick. Note that this change might not be `black`-compliant.
```suggestion
# TODO: remove this fixture and its associated parametrization
# once https://github.com/joblib/joblib/issues/563 is fixed.
def _create_aligned_memmap_backed_data(data):
    return create_memmap_backed_data(
        data, mmap_mode="r", return_folder=False, aligned=True
    )


@pytest.mark.parametrize("readonly", [_readonly_array_copy, _create_aligned_memmap_backed_data])
```

**[user]** on `sklearn/utils/tests/test_testing.py`:

```suggestion

# TODO: remove once https://github.com/joblib/joblib/issues/563 is fixed.
@pytest.mark.parametrize("dtype", [np.float32, np.float64, np.int32, np.int64])
def test_memmap_on_contiguous_data(dtype):
    """Test memory mapped array on contigous memoryview."""
    x = np.arange(10).astype(dtype)
    assert x.flags["C_CONTIGUOUS"]
    assert x.flags["ALIGNED"]

    # _test_sum consumes contiguous arrays
    # def _test_sum(NUM_TYPES[::1] x):
    sum_origin = _test_sum(x)

    # now on memory mapped data
    # aligned=True so avoid https://github.com/joblib/joblib/issues/563
    # without alignment, this can produce segmentation faults, see
    # (withheld: the upstream fix is not part of the task)
    x_mmap = create_memmap_backed_data(x, mmap_mode="r+", aligned=True)
    sum_mmap = _test_sum(x_mmap)
    assert sum_mmap == pytest.approx(sum_origin, rel=1e-11)
```

**[user]** on `sklearn/utils/_testing.py`:

```suggestion
    # TODO: remove the aligned case once https://github.com/joblib/joblib/issues/563
    # is fixed.
    if aligned:
        if isinstance(data, np.ndarray) and data.flags.aligned:
            # https://numpy.org/doc/stable/reference/generated/numpy.memmap.html
            filename = op.join(temp_folder, "data.dat")
            fp = np.memmap(filename, dtype=data.dtype, mode="w+", shape=data.shape)
            fp[:] = data[:]  # write data to memmap array
            fp.flush()
            memmap_backed_data = np.memmap(
                filename, dtype=data.dtype, mode=mmap_mode, shape=data.shape
            )
        else:
            raise ValueError("If aligned=True, input must be a single numpy array.")
    else:
        filename = op.join(temp_folder, "data.pkl")
```

**[user]** on `sklearn/utils/_testing.py`:

```suggestion
    aligned : bool, default=False
        If True, if input is a single numpy array and if the input array is aligned,
        the memory mapped array will also be aligned. This is a workaround for
        https://github.com/joblib/joblib/issues/563 .
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
