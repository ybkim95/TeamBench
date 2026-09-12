# GH927_scipy_24706: BUG: sparse.csgraph.connected_components: fix BSR blocksize != (1,1) … — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/scipy/scipy

## PR Description

#### Reference issue
Closes gh-23142

#### What does this implement/fix?
Fix incorrect results from scipy.sparse.csgraph.connected_components when given a bsr_array with blocksize != (1, 1).
This PR calls `eliminate_zeros()` after converting BSR matrices to CSR in `validate_graph()`, ensuring only structural nonzeros are treated as edges.

Changes:

- Modify scipy/sparse/csgraph/_validation.py to eliminate explicit zeros after BSR → CSR conversion.
- Add regression test test_bsr_blocksize_connected_components() covering multiple graph configurations.

#### AI Disclosure:
Used Github Copilot for helping me find relevant files and understanding context. Everything else was done and verified manually by me.

## PR Review Comments

**[user]** on `scipy/sparse/csgraph/tests/test_connected_components.py`:

minor: for new tests we have a slight preference for `assert_allclose` (see the docs of `assert_array_almost_equal` to see why)

**[user]** on `scipy/sparse/csgraph/tests/test_connected_components.py`:

minor: parametrizing over the `graphs` would slightly improve the test feedback in the event that only a subset of them fail

**[user]** on `scipy/sparse/csgraph/_validation.py`:

I did confirm that reverting this patch causes the added test to fail.

**[user]** on `scipy/sparse/csgraph/tests/test_connected_components.py`:

minor: might be nice to reference the target issue: i.e., `# regression test for gh-23142`

**[user]** on `scipy/sparse/csgraph/_validation.py`:

The `DTYPE` usage here is not new in this PR. The current code sets the dtype to `DTYPE` as well. But...

I think the correct usage must have meant to be `dtype`. The function signature is `dtype=DTYPE` but the variable `dtype` is not used in the function... only DTYPE.  It appears that all input will be changed to np.float64 no matter what the value of `dtype` is set to.

That is not a blocker for this PR, but if others agree it could be fixed here (or in another PR

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
