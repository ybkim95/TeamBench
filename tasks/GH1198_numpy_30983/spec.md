# GH1198_numpy_30983: BUG: f2py: restore .r/.i field access on complex types via union typedef — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/numpy/numpy

## PR Description

#30966 changed `f2py`'s complex_double/complex_float/complex_long_double typedefs from `struct {T r,i;}` to direct `npy_cdouble`/`npy_cfloat`/ `npy_clongdouble` aliases.


and forgot to check downstream. In this case it broke scipy https://github.com/scipy/scipy/issues/24775 because .pyf callstatements use `(a+k)->r` and `(a+k)->i` on complex_double* pointers, and npy_cdouble (double _Complex) has no .r/.i fields as reported by [user] (thanks!)

Fix by using a union containing an anonymous struct (for .r/.i backward compat) and the native npy_* type (for layout guarantee):

    typedef union { struct {double r,i;}; npy_cdouble _npy; } complex_double;

Internal `_from_pyobj` functions and `pyobj_from` macros now access the `_npy` member for npy_cset*/npy_creal*/npy_cimag* calls, while `rules.py` and `callstatement .r/.i` patterns work unchanged through the anonymous struct.

Closes scipy/scipy#24775. Tested on SciPy this time 😅 

<!--         ----------------------------------------------------------------
                MAKE SURE YOUR PR GETS THE ATTENTION IT DESERVES!
                ----------------------------------------------------------------

*  FORMAT IT RIGHT:
      https://www.numpy.org/devdocs/dev/development_workflow.html#writing-the-commit-message

*  IF IT'S A NEW FEATURE OR API CHANGE, TEST THE WATERS:
      https://www.numpy.org/devdocs/dev/development_workflow.html#get-the-mailing-list-s-opinion

*  HIT ALL THE GUIDELINES:
      https://numpy.org/devdocs/dev/index.html#guidelines

*  WHAT TO DO IF WE HAVEN'T GOTTEN BACK TO YOU:
      https://www.numpy.org/devdocs/dev/development_workflow.html#getting-your-pr-reviewed
-->

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
