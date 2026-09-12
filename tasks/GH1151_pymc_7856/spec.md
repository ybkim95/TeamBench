# GH1151_pymc_7856: Do not fail with zero-sized arrays in `dataset_to_point_list` — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/pymc-devs/pymc

## PR Description

Numpy does not support reshape(-1, ...) when size is zero

<!-- readthedocs-preview pymc start -->
----
📚 Documentation preview 📚: https://pymc--7856.org.readthedocs.build/en/7856/

<!-- readthedocs-preview pymc end -->

## PR Review Comments

**[user]** on `pymc/backends/arviz.py`:

should be the same as 

```
stacked_size = np.prod([ds.sizes[dim] for dim in sample_dims], dtype=int)
```

feel free to choose whichever you prefer

**[user]** on `pymc/backends/arviz.py`:

ds may be a dict

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
