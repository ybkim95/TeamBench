# GH550_werkzeug_3128: improve list quote handling — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/pallets/werkzeug

## PR Description

`parse_list_header` is more accurate in how it parses quoted and empty items according to RFC 9110 https://httpwg.org/specs/rfc9110.html#abnf.extension. Previously it just wrapped `urllib.request.parse_http_list`, which was a bit _too_ simple.

- Empty parts are now discarded.
- Backslash escapes are not unconditionally removed from quoted strings. `unquote_header_value` is used consistently for this purpose.
- An unclosed quoted string is considered invalid and results in an empty list, rather than consuming the rest of the value. I considered raising a `ValueError`, but in general our parsing functions return empty values for invalid input.

## PR Review Comments

**[user]** on `src/werkzeug/http.py`:

```suggestion
    """Remove double quotes and backslash escapes from a header value.
```

The previous text uses it to mention escaped quotes and backslashes, I don't think repeating it here adds much... if someone doesn't know what a backslash is I'm gonna lose my last bit of faith in humanity ;)

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
