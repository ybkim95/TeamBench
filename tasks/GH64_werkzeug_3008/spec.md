# GH64_werkzeug_3008: validate `request.trusted_hosts` in `Map.bind_to_environ` — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pallets/werkzeug/issues/3007
- Repo: https://github.com/pallets/werkzeug

## Issue Description

`Map.bind_to_environ` can be passed an environ or a request object. But it always calls `get_host(environ)`. If it used `request.host` if a request was passed, this would check `request.trusted_hosts` during routing. See pallets/flask#5636

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Consider making `request.trusted_hosts` a property, so setting it would automatically trigger validation. I'm not sure if this is a good idea or not. It's not particularly useful in Werkzeug, where the `request` is available to be configured before routing. It's only really convenient in Flask where a view (after routing) may want to set specific trusted hosts.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
