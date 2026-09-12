# GH74_flask_5898: redirect defaults to 303 — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pallets/flask/issues/5895
- Repo: https://github.com/pallets/flask

## Issue Description

Flask and Werkzeug `redirect` currently defaults to a [302](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/302). Routing uses [307](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/307) since that preserves method consistently. We didn't change the `redirect` default to 307, since that would break the common pattern of "GET form, POST form, redirect to GET result", ending up doing "POST result" instead. [303](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/303) seems designed exactly for this pattern, so that a redirect always results in a GET, instead of preserving the method or only rewriting it sometimes. [HTMX actually calls this out about Flask.](https://hypermedia.systems/htmx-patterns/#:~:text=cleaner%2E-,A,resource)

I don't _think_ there would actually be a problem switching to 303 as the default. It would still do the expected thing for basic page redirects and form submission redirects. I would be really surprised if anyone was relying on the 302 behavior of only converting POST and nothing else. I don't even remember that being the behavior when we were switching to 307, and I would have switched to 303 instead of leaving 302 then if I had known about it.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
