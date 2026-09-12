# GH613_celery_10038: Add `__class_getitem__` to generic classes — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/celery/celery

## PR Description

This will not change any behavior in normal usage, but will enable the `celery-types` project to use generics for:
* `Celery`
* `Task`
* `AsyncResult`
* `Signature`
* `_LocalStack`
* `_FastLocalStack`
* `FallbackContext`
* `class_property`

For example, this will allow annotations like:
```python
app = Celery[CustomTask]()
```

See the recent discussion: https://github.com/sbdchd/celery-types/issues/157#issuecomment-3696892836

## PR Review Comments

**[user]** on `celery/app/task.py`:

`__class_getitem__` must be decorated with `@classmethod` to work properly. Without this decorator, Python will not recognize it as the special method for subscripting classes (e.g., `Task[CustomType]`), and the typing functionality this PR aims to enable will not work.
```suggestion

    @classmethod
```

**[user]** on `celery/app/base.py`:

`__class_getitem__` must be decorated with `@classmethod` to work properly. Without this decorator, Python will not recognize it as the special method for subscripting classes (e.g., `Celery[CustomTask]`), and the typing functionality this PR aims to enable will not work.
```suggestion

    @classmethod
```

**[user]** on `celery/app/task.py`:

This new functionality is not covered by tests. Consider adding a test to verify that `Task[SomeType]` returns the `Task` class itself and that this enables type annotation support for downstream typing efforts. This is especially important since the implementation requires the `@classmethod` decorator to work correctly.

**[user]** on `celery/app/base.py`:

This new functionality is not covered by tests. Consider adding a test to verify that `Celery[SomeType]` returns the `Celery` class itself and that this enables type annotation support for downstream typing efforts. This is especially important since the implementation requires the `@classmethod` decorator to work correctly.

**[user]** on `celery/app/task.py`:

Incorrect. Per [the docs](https://docs.python.org/3/reference/datamodel.html#object.__class_getitem__):
> When defined on a class, `__class_getitem__()` is automatically a class method. As such, there is no need for it to be decorated with `@classmethod` when it is defined.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
