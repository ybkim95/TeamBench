"""
Tests for the middleware pipeline.

test_basic_middleware, test_error_handler_catches_next,
test_middleware_order_preserved, and test_no_error_passthrough pass even with
the buggy flat-loop implementation.

test_error_handler_catches_downstream, test_multiple_error_handlers, and
test_error_handler_response expose the bug and only pass after the fix.
"""

import pytest
from middleware import App, Pipeline, Request, Response


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_request(path: str = "/", method: str = "GET") -> Request:
    return Request(method=method, path=path)


# ---------------------------------------------------------------------------
# Tests that pass even with the buggy implementation
# ---------------------------------------------------------------------------

def test_basic_middleware():
    """Normal middleware chain executes in order and produces a response."""
    log = []

    def mw_a(req, res):
        log.append("a")

    def mw_b(req, res):
        log.append("b")
        res.body = "hello"

    app = App()
    app.use(mw_a)
    app.use(mw_b)

    resp = app.handle(make_request())
    assert resp.body == "hello"
    assert log == ["a", "b"]


def test_error_handler_catches_next():
    """
    Error handler immediately followed by the raising middleware catches the
    exception.  This works in both the buggy and fixed implementations.
    """
    def raiser(req, res):
        raise ValueError("boom")

    def error_mw(req, res, exc):
        res.status_code = 500
        res.body = f"caught: {exc}"
        return res

    app = App()
    app.use_error_handler(error_mw)
    app.use(raiser)

    resp = app.handle(make_request())
    assert resp.status_code == 500
    assert "caught: boom" in resp.body


def test_middleware_order_preserved():
    """Normal middleware executes strictly in registration order."""
    order = []

    def mw1(req, res):
        order.append(1)

    def mw2(req, res):
        order.append(2)

    def mw3(req, res):
        order.append(3)

    app = App()
    app.use(mw1)
    app.use(mw2)
    app.use(mw3)

    app.handle(make_request())
    assert order == [1, 2, 3]


def test_no_error_passthrough():
    """When no exception is raised, the error handler is transparent."""
    log = []

    def normal(req, res):
        log.append("normal")

    def error_mw(req, res, exc):
        log.append("error_handler_called")
        return res

    app = App()
    app.use_error_handler(error_mw)
    app.use(normal)

    app.handle(make_request())
    assert "error_handler_called" not in log
    assert "normal" in log


# ---------------------------------------------------------------------------
# Tests that expose the bug (require the fix to pass)
# ---------------------------------------------------------------------------

def test_error_handler_catches_downstream():
    """
    THE CORE BUG: an error handler must catch exceptions from ALL downstream
    middleware, not just the single next one.

    Pipeline:
        logging_mw  (pos 0) — normal
        error_mw    (pos 1) — error handler, should catch errors from 2, 3, 4
        auth_mw     (pos 2) — normal
        rate_mw     (pos 3) — normal
        route_mw    (pos 4) — raises ValueError two steps past error_mw
    """
    log = []

    def logging_mw(req, res):
        log.append("log")

    def error_mw(req, res, exc):
        log.append("error_handler")
        res.status_code = 500
        res.body = f"handled: {exc}"
        return res

    def auth_mw(req, res):
        log.append("auth")

    def rate_mw(req, res):
        log.append("rate")

    def route_mw(req, res):
        log.append("route")
        raise ValueError("not found")

    app = App()
    app.use(logging_mw)
    app.use_error_handler(error_mw)
    app.use(auth_mw)
    app.use(rate_mw)
    app.use(route_mw)

    resp = app.handle(make_request())

    assert resp.status_code == 500, (
        "Error handler should have set status_code=500 but got "
        f"{resp.status_code}. The flat-loop bug causes the ValueError to "
        "escape instead of being caught by error_mw."
    )
    assert "handled: not found" in resp.body
    assert "error_handler" in log


def test_multiple_error_handlers():
    """
    When multiple error handlers are registered, the first one whose scope
    covers the raising middleware handles the error.

    Pipeline:
        outer_error  (pos 0) — error handler covering the entire rest
        normal_a     (pos 1) — normal
        inner_error  (pos 2) — error handler covering pos 3+
        normal_b     (pos 3) — normal
        raiser       (pos 4) — raises RuntimeError

    inner_error is closer to the raiser; it should catch the error first.
    outer_error should NOT also fire.
    """
    fired = []

    def outer_error(req, res, exc):
        fired.append("outer")
        res.status_code = 503
        res.body = "outer caught"
        return res

    def normal_a(req, res):
        pass

    def inner_error(req, res, exc):
        fired.append("inner")
        res.status_code = 422
        res.body = "inner caught"
        return res

    def normal_b(req, res):
        pass

    def raiser(req, res):
        raise RuntimeError("deep error")

    app = App()
    app.use_error_handler(outer_error)
    app.use(normal_a)
    app.use_error_handler(inner_error)
    app.use(normal_b)
    app.use(raiser)

    resp = app.handle(make_request())

    assert "inner" in fired, "inner_error should have caught the RuntimeError"
    assert "outer" not in fired, "outer_error should not fire when inner already handled it"
    assert resp.status_code == 422


def test_error_handler_response():
    """
    Error handler can return a custom Response that short-circuits the rest of
    the pipeline, and that response is what handle() returns.
    """
    def raiser(req, res):
        raise KeyError("missing key")

    def normal_after(req, res):
        # This must NOT run after the error handler returns early.
        res.body = "should not appear"

    def error_mw(req, res, exc):
        custom = Response(status_code=400, body="bad request: missing key")
        return custom

    app = App()
    app.use_error_handler(error_mw)
    app.use(raiser)
    app.use(normal_after)

    resp = app.handle(make_request())

    assert resp.status_code == 400
    assert "bad request" in resp.body
    assert "should not appear" not in resp.body
