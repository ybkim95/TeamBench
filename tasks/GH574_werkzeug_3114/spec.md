# GH574_werkzeug_3114: update CSP directives — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/pallets/werkzeug

## PR Description

Added three new directive properties: `require_trusted_types_for`, `trusted_types`, and `upgrade_insecure_requests`. Did not add directives that were marked experimental in MDN, or that were marked deprecated but that we never added. Reorganized the properties based on the sections in the MDN docs.

`navigate-to` and `plugin-types` are no longer listed on MDN. `report-uri` and `prefetch-src` are listed as deprecated. These all raise deprecation warnings to be removed in Werkzeug 3.3. It's still possible to set any key using `csp[key] = value` instead of the properties, if needed.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
