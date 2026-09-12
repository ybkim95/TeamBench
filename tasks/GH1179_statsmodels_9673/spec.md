# GH1179_statsmodels_9673: BUG: Fix conversion of 1-d arrays to scalars — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/statsmodels/statsmodels

## PR Description

- [ ] closes #xxxx
- [ ] tests added / passed. 
- [ ] code/documentation is well formatted.  
- [ ] properly formatted commit message. See 
      [NumPy's guide](https://docs.scipy.org/doc/numpy-1.15.1/dev/gitwash/development_workflow.html#writing-the-commit-message). 

<details>


**Notes**:

* It is essential that you add a test when making code changes. Tests are not 
  needed for doc changes.
* When adding a new function, test values should usually be verified in another package (e.g., R/SAS/Stata).
* When fixing a bug, you must add a test that would produce the bug in main and
  then show that it is fixed with the new code.
* New code additions must be well formatted. Changes should pass flake8. If on Linux or OSX, you can
  verify you changes are well formatted by running 
  ```
  git diff upstream/main -u -- "*.py" | flake8 --diff --isolated
  ```
  assuming `flake8` is installed. This command is also available on Windows 
  using the Windows System for Linux once `flake8` is installed in the 
  local Linux environment. While passing this test is not required, it is good practice and it help 
  improve code quality in `statsmodels`.
* Docstring additions must render correctly, including escapes and LaTeX.

</details>

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
