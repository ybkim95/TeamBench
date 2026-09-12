# GH33_jinja_1663: `FileSystemLoader` include paths in error — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pallets/jinja/issues/1661
- Repo: https://github.com/pallets/jinja

## Issue Description

This was from https://github.com/apache/airflow/issues/23333 where trying to load a template that doesn't exist in the searchpath raises `TemplateNotFound` exception. In this case an absolute path is used which causes issue over concatenation but including `searchpath` might be a useful addition so that user can know under the paths under which the template was searched for and will be helpful during debugging.

https://github.com/pallets/jinja/blob/6f79daafe868b8ef20baecdcb45d12299529ed2e/src/jinja2/loaders.py#L218

Current exception :

```
jinja2.exceptions.TemplateNotFound: /tmp/a/python_template_exts.txt
```

Proposed exception to include searchpath :

```
jinja2.exceptions.TemplateNotFound: /tmp/a/python_template_exts.txt not found in search path ['/opt/airflow/tests/operators', '/']
```

## PR Review Comments

**[user]** on `src/jinja2/loaders.py`:

I don't know, maybe add a starred expression here

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
