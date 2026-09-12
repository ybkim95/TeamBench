# GH65_werkzeug_3110: always set `Accept-Ranges` header — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pallets/werkzeug/issues/3108
- Repo: https://github.com/pallets/werkzeug

## Issue Description

#1711 refactored the `_process_range_request` method. Before, it used to set `Accept-Ranges` as the first thing it did. Now, it only sets `Accept-Ranges` when sending a response to a Range request, which defeats the point of that header (which is to advertise support for range requests, so it's not useful if the client is already doing a range request).

basic repro:
```py
# /// script
# dependencies = [
#     "werkzeug==3.1.5",
# ]
# ///
from werkzeug.wrappers import Request, Response
from werkzeug.serving import run_simple
from werkzeug.wsgi import wrap_file
import io

def application(environ, start_response):
    text = b"Hello world!"
    wrap = wrap_file(environ, io.BytesIO(text))
    response = Response(wrap, mimetype='text/plain')
    response.set_etag('test')
    response.make_conditional(environ, accept_ranges=True, complete_length=len(text))
    return response(environ, start_response)

run_simple('127.0.0.1', 5000, application)
```

when making a request against this with `curl -i http://127.0.0.1:5000/`, there is no Accept-Ranges header. It only appears when doing a range request like `curl -i http://127.0.0.1:5000/ -H "Range: bytes=0-7"`. Note that when changing the version constraint to `werkzeug<1.0` (before #1711 was merged), we do see Accept-Ranges in the response to the basic request.

The fix would be to move the setting of Accept-Ranges back to the very beginning of `_process_range_request`.

Environment:

- Python version: 3.13.12
- Werkzeug version: 3.1.5

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
