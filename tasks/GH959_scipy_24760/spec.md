# GH959_scipy_24760: BUG: integrate: fix ComplexWarning in _sparse_num_jac with complex ODE — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/scipy/scipy

## PR Description

#### Reference issue

Closes gh-24671.

#### What does this implement/fix?

`_sparse_num_jac` in `scipy/integrate/_ivp/common.py` creates `h_vecs` and `h_new_all` as float64 arrays (NumPy's default), but when the ODE state vector `y` is complex, the perturbation step `h` is complex128 — even though its imaginary part is numerically zero. This causes NumPy to emit a spurious `ComplexWarning: Casting complex values to real discards the imaginary part` whenever complex values are assigned into those float64 arrays.

The fix is straightforward: add `dtype=h.dtype` to the three `np.empty`/`np.zeros` calls in `_sparse_num_jac`:

- `h_vecs = np.empty((n_groups, n), dtype=h.dtype)`
- `h_new_all = np.zeros(n, dtype=h.dtype)`
- `h_vecs = np.empty((groups_unique.shape[0], n), dtype=h.dtype)`

The dense path (`_dense_num_jac`) already handles this correctly because `np.diag(h)` naturally inherits the dtype of `h`. This change makes the sparse path consistent with the dense path.

A regression test `test_integration_complex_sparse` is added. Since `pytest.ini` sets `filterwarnings = error`, the test would fail before the fix and passes cleanly after.

#### Additional information

The warning is spurious: the imaginary part being cast away is always exactly zero (the step `h` is computed from real arithmetic even though `y` is complex), so results are numerically correct both before and after the fix. The only change in behavior is the absence of the spurious warning.

#### AI Generation Disclosure

No AI tools used.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
