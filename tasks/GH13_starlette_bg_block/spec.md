# GH13: BaseHTTPMiddleware Blocks on Background Tasks

## Goal

Fix `middleware.py` so background tasks attached to responses do not block
subsequent concurrent HTTP requests.

## Requirements

1. A health-check request sent concurrently with a main request must respond
   in under 2 seconds, even though the background task sleeps for 3 seconds
2. The main route (`/notify`, `/track`, or `/action`) must still return 200
3. The health route (`/health`, `/ping`, or `/status`) must still return 200
4. Background work must still execute (just not block the connection)
5. All tests in `test_app.py` pass: `pytest test_app.py -v`

## Supporting Documents

- `middleware.py` — contains the buggy `BaseHTTPMiddleware` subclass
- `app.py` — Starlette application (correct, do not modify)
- `test_app.py` — pytest-asyncio tests

## Contradiction / Hidden Complexity

The bug is structural: `BaseHTTPMiddleware` keeps the ASGI send/receive
lifecycle open until all `BackgroundTask` objects on the response have
completed. This is a known Starlette limitation
(https://github.com/encode/starlette/issues/919). A naive agent may try to
make the background task faster rather than fixing the middleware architecture.

The fix requires replacing `BaseHTTPMiddleware` with a raw ASGI middleware
class (or using `asyncio.create_task` to decouple the work from the response
lifecycle).

## Important Notes

- Fix is in `middleware.py` only
- Do NOT modify `app.py` or `test_app.py`
- The background task must still run — do not simply remove it
