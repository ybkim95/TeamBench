# GH11: Fix Middleware Error Handler Ordering

The web framework's middleware pipeline has a bug where error-handling
middleware doesn't catch errors from all downstream handlers. Errors
from handlers registered after the error handler slip through uncaught.

Fix the middleware pipeline in `middleware.py`.
