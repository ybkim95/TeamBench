# GH381_celery_10013: Fix Redis Sentinel ACL authentication support — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/celery/celery

## PR Description

## Description

**Support for Redis Sentinel ACL authentication (username + password) in SentinelBackend** 

### Problem

When using Redis Sentinel with ACL authentication (Redis 6.0+ feature), the `SentinelBackend` fails to authenticate because:

1. **`_params_from_url`** - Does not extract the `username` from the sentinel URL. The username is present in `connparams["hosts"][0]["username"]` but was never propagated to the top-level `connparams`.

2. **`_get_pool`** - Does not pass credentials (`username`, `password`) to `sentinel_instance.master_for()` when creating the connection pool.

### Solution

This change fixes both issues:
- Extract `username` from sentinel hosts alongside `db` and `password` in `_params_from_url`
- Pass ACL credentials to `master_for()` in `_get_pool`

### Usage

```python
# Sentinel URL with ACL authentication (username:password)
app.conf.result_backend = 'sentinel://myuser:mypass@sentinel1:26379/0;sentinel://myuser:mypass@sentinel2:26379/0'

app.conf.result_backend_transport_options = {
    'master_name': 'mymaster',
}
```

### Changes
- `celery/backends/redis.py`: Fixed `_params_from_url` and `_get_pool` methods in `SentinelBackend`
- `t/unit/backends/test_redis.py`: Added unit tests for ACL authentication support

### Related Issues
- [#6301 - Complete redis Sentinel documentation in regards to authentication](https://github.com/celery/celery/issues/6301)

## PR Review Comments

**[user]** on `celery/backends/redis.py`:

This appears to enable Redis Sentinel ACL authentication (username + password), which is user-facing behavior. Should we add documentation updates showing the usage pattern with username in the sentinel URL?

If yes: Could we add an example in `docs/getting-started/backends-and-brokers/redis.rst` near line 108 (in the Sentinel result backend section) showing:
```python
app.conf.result_backend = 'sentinel://myuser:mypass@host:port/db;...'
```
and possibly a `versionchanged:: 5.6.1` note mentioning ACL auth support for Sentinel result backends?

If no: Could you share the rationale for deferring docs, and note where users should look for usage guidance?

**[user]** on `celery/backends/redis.py`:

This is actually a bugfix rather than a new feature. The parent `RedisBackend._params_from_url` method already parses username from URLs, and regular Redis URLs already support ACL authentication with the `username:password@host` format.
The issue was that `SentinelBackend._params_from_url` was only copying db and password to the top-level connparams, but not username — so the username was being parsed from the URL but then lost before being passed to the Sentinel connection.
Since users would already expect Sentinel URLs to work the same way as regular Redis URLs (which is the documented behavior), I don't think we need additional documentation for this. The fix just makes Sentinel behave consistently with the existing URL format.

**[user]** on `Changelog.rst`:

[user] this shouldn’t have been merged. [I’ll clean it]((withheld: the upstream fix is not part of the task)); note for next time.

**[user]** on `Changelog.rst`:

OK thanks

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
