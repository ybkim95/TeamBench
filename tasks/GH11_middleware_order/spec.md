# GH11: Middleware Error Handler Ordering — Full Specification

## Issue

Error handler middleware registered with `app.use_error_handler(handler)` only catches
exceptions from the immediately next middleware in the pipeline, not from the entire
downstream chain. Errors from handlers registered two or more positions after the error
handler slip through uncaught.

## Concrete Example

```python
app = App()
app.use(logging_middleware)       # position 1
app.use_error_handler(error_mw)   # position 2 — should catch errors from 3, 4, 5
app.use(auth_middleware)          # position 3
app.use(rate_limiter)             # position 4
app.use(route_handler)            # position 5 — raises ValueError("not found")
```

With the buggy implementation the `ValueError` from step 5 is **NOT** caught by
`error_mw` at step 2. It propagates all the way out of the pipeline unhandled.

## Root Cause

In `Pipeline.execute(request)`, middleware is executed as a flat loop. When the
pipeline encounters an error handler it tries/catches only around the single next
middleware call:

```python
for i, mw in enumerate(self._middlewares):
    if mw.is_error_handler:
        try:
            result = self._middlewares[i + 1].func(request, response)
        except Exception as e:
            result = mw.func(request, response, e)
        skip_next = True   # skips only one entry
    else:
        result = mw.func(request, response)
```

Because the `try/except` wraps only `pipeline[i+1]`, any exception raised by
`pipeline[i+2]`, `pipeline[i+3]`, … is never intercepted by the error handler.

## The Fix

Change the pipeline execution from a flat loop to a **recursive chain** (or an
explicit nested-closure stack). Each error handler must wrap
`execute_remaining(pipeline[i+1:])` — the entire suffix of the pipeline — so that
any downstream error bubbles up to it.

A correct recursive approach:

```python
def _run(self, middlewares, request, response):
    if not middlewares:
        return response
    mw = middlewares[0]
    rest = middlewares[1:]
    if mw.is_error_handler:
        try:
            return self._run(rest, request, response)
        except Exception as e:
            return mw.func(request, response, e)
    else:
        result = mw.func(request, response)
        if result is not None:
            return result
        return self._run(rest, request, response)
```

## Constraints

- **Normal (non-error) middleware execution order must remain the same** (FIFO,
  registration order).
- **`Request` and `Response` classes are correct** — do not change them.
- **Middleware registration order must be respected** — `add()` / `add_error_handler()`
  append to the same ordered list.
- Error handlers accept three arguments: `(request, response, exception)`.
- Normal middleware accepts two arguments: `(request, response)`.
- If a middleware or error handler returns a `Response` object, that terminates the
  chain (short-circuit).
- If no error handler catches a propagating exception, the exception escapes the
  pipeline.
