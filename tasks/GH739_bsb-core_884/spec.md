# GH739_bsb-core_884: fix: update morphology introduce_point function — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/dbbs-lab/bsb-core/issues/883
- Repo: https://github.com/dbbs-lab/bsb-core

## Issue Description

The function seems to have been outdated for a while. It needs to be updated to bsb 4.

## PR Review Comments

**[user]** on `bsb/morphologies/__init__.py`:

```suggestion
        # By default duplicate the existing property value ...
        for k, v in self._properties.items():
```

**[user]** on `bsb/morphologies/__init__.py`:

```suggestion
        # ... and overwrite it with any new property values, if given.
        if properties is not None:
```

**[user]** on `bsb/morphologies/__init__.py`:

raise an error if an incorrect property is given. _NEVER_ silently ignore a case where a user unambiguously makes a mistake.

**[user]** on `tests/test_morphologies.py`:

```suggestion
        self.assertAll(b.tags == np.array([4, 5, 5, 6, 7]))
```

use the class the way the user would so that we are more likely to catch the problems they will run into

**[user]** on `tests/test_morphologies.py`:

```suggestion
        self.assertAll(b.tags == np.array([4, 5, 5, 6, 8, 7]))
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
