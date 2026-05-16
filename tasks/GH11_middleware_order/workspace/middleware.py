"""
Minimal middleware pipeline for a web framework.

This module provides Request, Response, Middleware, Pipeline, and App classes
that together form a simple WSGI-like middleware stack.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional


# ---------------------------------------------------------------------------
# HTTP primitives
# ---------------------------------------------------------------------------

@dataclass
class Request:
    """Represents an incoming HTTP request."""

    method: str
    path: str
    headers: dict[str, str] = field(default_factory=dict)
    body: str = ""
    # Middleware may attach arbitrary data here (e.g. parsed auth token).
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class Response:
    """Represents an outgoing HTTP response."""

    status_code: int = 200
    body: str = ""
    headers: dict[str, str] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Middleware primitives
# ---------------------------------------------------------------------------

@dataclass
class Middleware:
    """Wraps a callable with metadata used by the pipeline."""

    func: Callable
    is_error_handler: bool = False


# ---------------------------------------------------------------------------
# Pipeline — fixed with recursive chain
# ---------------------------------------------------------------------------

class Pipeline:
    """
    Executes an ordered list of middleware functions against a request.

    Middleware functions have signature:
        func(request: Request, response: Response) -> Optional[Response]

    Error-handler middleware functions have signature:
        func(request: Request, response: Response, exc: Exception) -> Optional[Response]
    """

    def __init__(self) -> None:
        self._middlewares: list[Middleware] = []

    def add(self, func: Callable) -> None:
        """Register a normal (non-error) middleware function."""
        self._middlewares.append(Middleware(func=func, is_error_handler=False))

    def add_error_handler(self, func: Callable) -> None:
        """Register an error-handling middleware function."""
        self._middlewares.append(Middleware(func=func, is_error_handler=True))

    def _run(self, middlewares: list[Middleware], request: Request, response: Response) -> Response:
        """Recursively execute the middleware chain."""
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

    def execute(self, request: Request) -> Response:
        """Run the middleware chain and return the final Response."""
        response = Response()
        return self._run(self._middlewares, request, response)


# ---------------------------------------------------------------------------
# App — thin facade over Pipeline
# ---------------------------------------------------------------------------

class App:
    """
    High-level application object.

    Usage::

        app = App()
        app.use(logging_middleware)
        app.use_error_handler(error_middleware)
        app.use(route_handler)

        response = app.handle(request)
    """

    def __init__(self) -> None:
        self._pipeline = Pipeline()

    def use(self, func: Callable) -> "App":
        """Append a normal middleware to the pipeline."""
        self._pipeline.add(func)
        return self

    def use_error_handler(self, func: Callable) -> "App":
        """Append an error-handling middleware to the pipeline."""
        self._pipeline.add_error_handler(func)
        return self

    def handle(self, request: Request) -> Response:
        """Process *request* through the middleware pipeline."""
        return self._pipeline.execute(request)
