# GH363_celery_10040: Add redis-py DriverInfo support to Redis backend — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/celery/celery

## PR Description

## Description

Adds support for redis-py's `DriverInfo` class to identify Celery as an upstream driver in Redis connection metadata, following the [Redis client library identification guidance](https://redis.io/docs/latest/commands/client-setinfo/).

This improves observability for Redis administrators by making Celery connections easily identifiable when inspecting connected clients (e.g., via `CLIENT LIST` or `CLIENT INFO` commands).

## Changes

- Add `_add_driver_info()` method to `RedisBackend` class
- Use `DriverInfo` class when available
- Fallback to `lib_name`/`lib_version` for older redis-py versions
- Follow Flask-Caching pattern: `lib_name='redis-py(celery_v{version})'`
- Add 4 comprehensive unit tests covering all scenarios

## Motivation

Redis recommends that client libraries identify themselves using `CLIENT SETINFO` to help administrators understand which applications are connected. This change aligns Celery with this best practice by:

- Setting `lib-name` to identify Celery as the upstream driver (e.g., `redis-py(celery_v5.4.0)`)
- Setting `lib-ver` to the redis-py client version
- Making Celery connections distinguishable from other redis-py users

## Testing

- Added 4 unit tests covering all code paths
- All existing Redis backend tests pass (97/97)
- No decrease in test coverage
- Linting passes (flake8, isort)
- Security scan passes (bandit)

## Checklist

- [x] Unit tests added
- [x] Test coverage maintained
- [x] Code follows project style
- [x] Imports sorted with isort
- [x] Security check passed

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
