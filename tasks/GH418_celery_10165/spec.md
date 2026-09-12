# GH418_celery_10165: Fix NameError with TYPE_CHECKING annotations on Python 3.14+ (PEP 649) — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/celery/celery

## PR Description

*Note*: Before submitting this pull request, please review our [contributing
guidelines](https://docs.celeryq.dev/en/main/contributing.html).

## Description

Fix NameError when registering tasks whose annotations reference types only imported under TYPE_CHECKING on Python 3.14+.

In Python 3.14, annotations are deferred by default ([PEP 649](https://peps.python.org/pep-0649/)). Accessing fun.__annotations__ triggers lazy evaluation, which raises NameError for types only imported under TYPE_CHECKING. Two sites in Celery eagerly triggered this evaluation:

celery/app/base.py — _task_from_fun: Replaced direct fun.__annotations__ access with inspect.get_annotations(fun, format=annotationlib.Format.STRING) on Python 3.14+, which returns annotations as strings without evaluating them.

celery/utils/functional.py — head_from_fun: inspect.getfullargspec internally evaluates annotations on 3.14+ and raises NameError for TYPE_CHECKING-only types. Added a _getfullargspec wrapper on Python 3.14+ that calls inspect.signature(..., annotation_format=annotationlib.Format.STRING) and reconstructs a FullArgSpec with annotations omitted, since head_from_fun never uses annotations anyway.

Fixes https://github.com/celery/celery/discussions/10099

## PR Review Comments

**[user]** on `t/unit/utils/test_functional.py`:

The `exec('def f(args: Sequence[str], ...)')` line will raise `NameError` at definition time on Python versions where annotations are evaluated eagerly (i.e., < 3.14), because `Sequence` is not defined in the exec globals/locals. To keep this regression test runnable across supported versions, either gate it behind a `sys.version_info >= (3, 14)` skip, or make the exec’ed function store annotations as strings (e.g., via `from __future__ import annotations`) so `Sequence` doesn’t need to exist at runtime.
```suggestion
        fun = (
            'from __future__ import annotations\n'
            'def f(args: Sequence[str], x: int = 0):\n'
            '    return args'
        )
        exec(fun, {}, local)
```

**[user]** on `t/unit/app/test_app.py`:

This `exec` defines a function annotated with `Sequence[str]` but does not provide `Sequence` in the exec environment, which will raise `NameError` on Python versions where annotations are evaluated eagerly (< 3.14). To avoid breaking the test suite on currently supported interpreters, consider either skipping this test on < 3.14 or changing the exec string so annotations are stored as strings (e.g., using `from __future__ import annotations`).

**[user]** on `celery/utils/functional.py`:

The PR description mentions adding a `__code__`-based fallback in `head_from_fun`, but the implementation here instead switches to `inspect.signature(..., annotation_format=Format.STRING)` and reconstructs a `FullArgSpec`. If the intent changed, it’d help to update the PR description to match the actual approach (or clarify why signature-based extraction is preferred over `__code__`).

**[user]** on `t/unit/utils/test_functional.py`:

Done, chose to skip tests for pre python 3.14

**[user]** on `celery/utils/functional.py`:

Updated PR description to match

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
