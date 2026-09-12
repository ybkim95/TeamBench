# GH902_scikit_learn_21336: FIX Prevents segfault in SVC when internals are altered — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/scikit-learn/scikit-learn/issues/1234
- Repo: https://github.com/scikit-learn/scikit-learn

## Issue Description

This should clean up the stuff I pushed earlier.
cc [user] [user] Could you have a brief look? What I pushed earlier is buggy but I didn't dare push again after so many failed fixes.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

This is good. I am merging it in.

### Comment 2 ([user]):

Thanks [user] :)

## PR Review Comments

**[user]** on `doc/whats_new/v1.1.rst`:

```suggestion
  This fix also resolves `CVE-2020-28975 <https://nvd.nist.gov/vuln/detail/CVE-2020-28975>`_. :pr:``21336` by `Thomas Fan`_.
```

**[user]** on `doc/whats_new/v1.1.rst`:

```suggestion
  in its internal representation and raise an error instead of segfaulting.
```

**[user]** on `doc/whats_new/v1.1.rst`:

```suggestion
- |Fix| :class:`svm.SVC` and :class:`svm.SVR` check for an inconsistency
```

**[user]** on `doc/whats_new/v1.1.rst`:

```suggestion
  in it's internal representation and raise an error instead of segfaulting.
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
