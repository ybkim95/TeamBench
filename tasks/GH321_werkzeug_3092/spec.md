# GH321_werkzeug_3092: `redirect` defaults to 303 — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/pallets/werkzeug

## PR Description

See https://github.com/pallets/flask/issues/5895. `303` switches all methods to `GET` (except `HEAD`), unlike `301`/`302` which only switches `POST`. With `301`, HTMX and other libraries that use the full range of methods will cause incorrect behavior after making an API call that redirects to a result. For example, `DELETE /users/123` that returns a redirect to `/users`, the redirect will also be `DELETE /users` instead of `GET /users`. Just as `307` is used for routing redirects to always preserve the method, `303` is used for redirects after mutations to always _not_ preserve the method.

This also fixes some behaviors in the test client's redirect handling:

- More headers about the request body are cleared, following https://fetch.spec.whatwg.org/#http-redirect-fetch.
- Fixed an issue I inadvertently added when I made a previous fix for `input_stream` handling,  which caused the form and files data to not be cleared on redirect.
- _All_ files in the multidict are closed when calling `EnvironBuilder.close`, not only the first file associated with each key.
- `305` is no longer handled as a redirect, it hasn't been part of the HTTP spec for a long time.
- The test client only switches `301`/`302` `POST` to `GET`, not other methods.

---

In fixing the file closing oversight, I noticed that how `EnvironBuilder` handles `form`, `files`, `input_stream`, and `close` is really weird. `close` sets `closed = True`, so subsequent calls to `close` don't run again, but the builder is still completely usable in a closed state. `input_stream` is not closed, presumably since it's assumed to be managed externally, and we do have some tests that currently rely on that property. I don't know what to do about all this, but something I'll think about.

I also noticed that we commonly use the pattern

```python
builder = EnvironBuilder(...)

try:
    return builder.get_environ()
finally:
    builder.close()
```

Which suggests we should make `EnvironBuilder` a context manager.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
