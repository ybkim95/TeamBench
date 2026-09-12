# GH1003_scipy_24496: BUG:sparse: make `sum` apply `dtype` before accumulation — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/scipy/scipy

## PR Description

Ensure that dtype affects the accumulator as documented by casting to the requested dtype before summation.

Previously, dtype was effectively applied after summation, which produced results inconsistent with the documentation and NumPy behavior for integer dtypes.

Resolves gh-23768

### Reference issue
Resolves gh-23768

### What does this implement/fix?
This fixes the sum method in sparse matrices so that the accumulator uses the requested dtype, producing results consistent with NumPy and the documentation.

### Additional information
No changes to performance optimizations were made; this is purely a correctness fix. Performance improvements may be addressed in a future PR.

## PR Review Comments

**[user]** on `scipy/sparse/_compressed.py`:

This quick piece of code handles the case where `axis=minor`, right? That is, when CSR gets `axis=1` or CSC gets `axis=0`. So I think the original comments are correct. 

I also don't think we should state "use dtype as accumulator type" in the comment on line 503 because we don't actually have an accumulator. We are just converting the dtype of the input array.

**[user]** on `scipy/sparse/tests/test_base.py`:

The `sum` method should handle duplicate entries without having to call sum_duplicates first. That is, we *want*  datsp to be non-canonical in the non-canonical test cases.

**[user]** on `scipy/sparse/_compressed.py`:

About the minor and major axes - I'm trying to understand: in CSR format, are rows the minor axis and not the major one?

About the second comment - you're right, I'll delete it.

**[user]** on `scipy/sparse/tests/test_base.py`:

OK, that makes sense.

**[user]** on `scipy/sparse/_compressed.py`:

The major axis is the compressed axis.
For CSR format, the rows are the major axis (indptr gives the info about this axis) and the columns are the minor axis.  For CSC that gets swapped.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
