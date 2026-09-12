# GH8: Fix Dependency Cache Race Condition

The web framework's dependency injection has a race condition where cached
dependency results leak between concurrent requests. Users report that
request-specific data (like current user) sometimes returns wrong values
under concurrent load.

Fix the dependency resolver in `dependency_injection.py`.
