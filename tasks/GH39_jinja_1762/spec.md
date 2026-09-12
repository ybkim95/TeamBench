# GH39_jinja_1762: Pass context to test when using select — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pallets/jinja/issues/1624
- Repo: https://github.com/pallets/jinja

## Issue Description

When used from `select`, tests that are decorated with `@pass_context` fail with the error:

> jinja2.exceptions.TemplateRuntimeError: Attempted to invoke a context test without context.

For example:

```python
from jinja2 import Environment, pass_context

def main():
    env = Environment()
    env.tests["foo"] = is_foo
    output = env.from_string("""

    works: {{ "foo" is foo }}

    {%- for x in ["one", "foo" ] | select("foo") %}
    fails: {{ x }}
    {%- endfor %}

    """).render({})
    print(output)

@pass_context
def is_foo(ctx, s):
    return s == "foo"

if __name__ == "__main__":
    main()
```

Environment:

- Python version: 3.10
- Jinja version: 3.0.3

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
