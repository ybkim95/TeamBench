# GH1185_airflow_62174: Order of task arguments in task definition causing error when parsing DAG — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/apache/airflow

## PR Description

Current PR fixes an issue related to default values(https://github.com/apache/airflow/issues/56128) So when:

```python
# example_2.py
from airflow.decorators import dag, task


@dag()
def example_2():
    @task
    def foo(start_date, end_date): ...

    foo(None, None)


example_2()
```

under the hood signature of `def foo` will be transformed into something like that:
```python
def foo(start_date=None, end_date):
```

which is incorrect syntax according to python requirement for `default` values. So if the first variable has a `default` value, then all other variables should also have it, so correct signature should be:

```python
def foo(start_date=None, end_date=None):
```

so current PR makes sure that if the first variable has a `default` value, then all others should also have it.

second example for the original issue:
```python
# example_1.py
from airflow.decorators import dag, task


@dag()
def example_1():
    @task
    def foo(end_date, start_date): ...

    foo(None, None)


example_1()
```
works well, because the last variable could have `default` value without any problem according to Python syntax.

## PR Review Comments

**[user]** on `task-sdk/tests/task_sdk/bases/test_decorator.py`:

Maybe rename this and all other occurrences to something more intuitive? Such as `dummy_task`?

**[user]** on `task-sdk/tests/task_sdk/bases/test_decorator.py`:

yep. done.

**[user]** on `task-sdk/src/airflow/sdk/bases/decorator.py`:

To clarify, replacing with defaults is just for the interpreter here. The actual param values are still honored. I've verified it.

**[user]** on `task-sdk/src/airflow/sdk/bases/decorator.py`:

This injects `default=None` for all positional params after the first defaulted one, not just context-key params. If a user writes `def foo(start_date, my_data): ...; foo()` and forgets `my_data`, the parse-time `signature.bind()` check won't catch it because `my_data` now has a default too. The error moves to runtime.

Before this PR the error message was confusing, but at least it happened early. Worth considering whether only params between context-key-defaulted params and the next user-provided default should get `None`, rather than all trailing positional params.

**[user]** on `task-sdk/tests/task_sdk/bases/test_decorator.py`:

`inspect.signature(op.python_callable)` returns the original function's signature. The fix modifies a local `parameters` list used only for `bind()` validation; it never touches the callable itself. So this test is verifying that the original callable's defaults are preserved (which was always true), not that the fix's default-injection logic produces the right values.

Consider inspecting the modified signature instead (e.g., by capturing it inside `__init__` or testing that `signature.bind()` succeeds/fails as expected).

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
