# GH430_celery_10015: Fix: Avoid unnecessary Django database connection creation during cleanup — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/celery/celery

## PR Description

## Problem
When Celery iterates over Django database connections to close them (e.g., during worker initialization or task cleanup), calling `connections.all()` without parameters causes Django to automatically create a new connection for every configured database alias that doesn't already have an active connection.

This happens because Django's ConnectionHandler will lazily instantiate connections when you access an alias that hasn't been initialized yet. The code then immediately closes these newly-created connections, which is wasteful and can cause issues.

## Solution
Pass `initialized_only=True` to `connections.all()` to only iterate over connections that have already been initialized, avoiding the creation of new connections.
This parameter was added to Django specifically for this use case - it checks if a connection exists before accessing it: https://github.com/django/django/blob/main/django/utils/connection.py#L62

## Impact

* No behavior change for existing active connections - they are still properly closed
* Aligns with Django's own connection management - Django uses this same pattern in its close_old_connections() signal handlers

## PR Review Comments

**[user]** on `celery/fixups/django.py`:

The `initialized_only` parameter was added to Django's `ConnectionHandler.all()` in Django 3.1 (August 2020). However, the current codebase supports Django >= 2.2.28 (per requirements/extras/django.txt) and checks for Django >= 1.11 (line 48). Is this intended to be a breaking change requiring Django 3.1+?

If yes: Should we update the minimum Django version check on line 48 and in requirements/extras/django.txt, add a migration note in the PR description/docs, and document this version requirement change?

If no: Should we handle this gracefully for older Django versions (e.g., using a try/except or version check to fall back to `connections.all()` without parameters)?

**[user]** on `t/unit/fixups/test_django.py`:

The test mock now accepts an `initialized_only` parameter, but several other tests in this file mock `connections.all` without accounting for this new parameter (lines 188, 280, 297, 306, 319). These tests may fail with a TypeError when the actual code calls `connections.all(initialized_only=True)` but the mock doesn't accept the parameter.

Should we update these other test mocks to also accept the parameter, either by:
- Using `lambda initialized_only=False: conns` pattern
- Using `Mock(return_value=[conn])` which accepts any arguments by default
- Using `Mock(side_effect=lambda **kwargs: [conn])`

The current tests appear to work because Mock objects accept arbitrary arguments, but it would be more explicit and maintainable to handle the parameter consistently across all tests.

**[user]** on `celery/fixups/django.py`:

[user] how would you suggest we address this issue? The oldest version of Django that is still being supported by the Django team is 4.2. The previous LTS version was 3.2 which was EOL in April 2024.

I also notice that the docs state that the django requirement is for informational purposes only and "You should probably not use this in your requirements, it's here for informational purposes only." It also isn't used in any tests.

For now I've gone ahead and wrapped the method call in exception handling which seems like the path of least resistance for now.

**[user]** on `celery/fixups/django.py`:

I'm not sure the copilot is correct here. It appears to me that the `initialized_only` parameter was added in 4.1 (see (withheld: the upstream fix is not part of the task)), not 3.1.

**[user]** on `celery/fixups/django.py`:

copilot is not right here

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
