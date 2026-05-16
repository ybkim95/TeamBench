# GH103_redis-py_3998: Fixing security concern in __repr__ methods for ConnectionPools - passwords might leak in plain text logs — Full Specification (Planner Only)

## Source
- PR: https://github.com/redis/redis-py/pull/3998
- Issue: https://github.com/redis/redis-py/issues/3993
- Repo: https://github.com/redis/redis-py

## Issue Description

## Security Vulnerability Report

**Severity**: MEDIUM (CVSS 5.5)
**CWE**: CWE-532 — Insertion of Sensitive Information into Log File
**CVSS Vector**: CVSS:3.1/AV:L/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N
**Reporter**: Conner Webber (conner.webber000@gmail.com)
**90-day disclosure deadline**: 2026-06-06

> **Note**: I attempted to file this via GitHub's Private Vulnerability Reporting (PVRA), but it is not enabled on this repository. I also checked for a SECURITY.md — none exists for redis-py. The main redis/redis SECURITY.md points to redis@redis.io which I am also contacting. Filing here so the maintainers are aware.

## Summary

`ConnectionPool.__repr__()` in `redis/connection.py` (lines 2848-2854) iterates over **all** `connection_kwargs` and includes them in the string representation — including `password`.

When a Redis connection is created with a password (via URL or explicit `password=` parameter), the password is stored in `connection_kwargs['password']`. Any code path that triggers `repr()` on a `ConnectionPool` instance will expose the Redis password in plaintext.

The `Connection` class itself is **not affected** — its `repr_pieces()` method (lines 1465-1469) deliberately excludes the password field. `ConnectionPool.__repr__` was missed when that mitigation was added.

## Affected Code

```python
# redis/connection.py:2848-2854
def __repr__(self) -> str:
    conn_kwargs = ",".join([f"{k}={v}" for k, v in self.connection_kwargs.items()])
    return (...)
```

## Steps to Reproduce

```python
import redis
import logging

logging.basicConfig(level=logging.DEBUG)

pool = redis.ConnectionPool.from_url('redis://:MySecretPassword@localhost:6379/0')
print(repr(pool))  # Password visible in output
logging.debug('Pool state: %r', pool)  # Password written to log file
```

## Impact

Redis passwords are exposed in:
- Application log files (any framework that logs connection objects)
- Error tracking services (Sentry, Datadog, etc.)
- Debugger output
- Tracebacks printed to stderr
- Monitoring dashboards

This is especially impactful in cloud/containerized environments where logs are aggregated and accessible to operations teams who should not have database credentials.

## Suggested Fix

Filter sensitive keys from `connection_kwargs` in `__repr__`, consistent with how `Connection.repr_pieces()` already handles it:

```python
def __repr__(self) -> str:
    SENSITIVE_KEYS = {'password', 'credential_provider'}
    conn_kwargs = ",".join(
        [f"{k}={'***' if k in SENSITIVE_KEYS else v}"
         for k, v in self.connection_kwargs.items()]
    )
    return (...)
```

## Affected Versions

All current versions of redis-py that include `ConnectionPool.__repr__`.

## Issue Discussion (Root Cause Analysis)

### Comment 1 (@spartan8806):

Hey — apologies for the confusion here. We accidentally posted a reply meant for a different thread and then closed this one by mistake trying to clean it up. The actual report is still valid though. Sorry about the mess!

## PR Review Comments

**@cursor[bot]** on `redis/connection.py`:

### Duplicated sensitive keys list may diverge across files

**Medium Severity**

<!-- DESCRIPTION START -->
`SENSITIVE_REPR_KEYS` is independently defined with identical contents in both the sync `ConnectionPool` (`redis/connection.py`) and the async `ConnectionPool` (`redis/asyncio/connection.py`). If a new sensitive key (e.g., `token`) is added to one but not the other, credentials would silently leak in the forgotten pool's `__repr__`. A shared constant would eliminate this risk.
<!-- DESCRIPTION END -->

<!-- BUGBOT_BUG_ID: a4490fe7-a623-4243-80a9-11950f5e5e0e -->

<!-- LOCATIONS START
redis/connection.py#L2879-L2887
redis/asyncio/connection.py#L1311-L1319
LOCATIONS END -->
<details>
<summary>Additional Locations (1)</summary>

- [`redis/asyncio/connection.py#L1311-L1319`](https://github.com/redis/redis-py/blob/01fa7a9d8698652dd0f0faf88a6ea409849edde4/redis/asyncio/connection.py#L1311-L1319)

</details>

<p><a href="https://cursor.com/open?data=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImJ1Z2JvdC12MiJ9.eyJ2ZXJzaW9uIjoxLCJ0eXBlIjoiQlVHQk9UX0ZJWF9JTl9DVVJTT1IiLCJkYXRhIjp7InJlZGlzS2V5IjoiYnVnYm90OjYxMWMzNmQwLWQ1M2MtNDUyNS05ZDNkLTI5YTRjY2U0YWJmNyIsImVuY3J5cHRpb25LZXkiOiJjQWx2UWs1d2FKRTNOMDRleExidVlvdGpHT3lYdGRuRGpLeXNSQUIxTGs0IiwiYnJhbmNoIjoicHNfZml4X3NlY3VyaXR5X2NvbmNlcm5fcGFzc3dvcmRfZXhwb3NlZF90aHJvdWdoX19yZXByX18iLCJyZXBvT3duZXIiOiJyZWRpcyIsInJlcG9OYW1lIjoicmVkaXMtcHkifSwiaWF0IjoxNzczMTUwMjg1LCJleHAiOjE3NzU3NDIyODV9.y20QVfdhtbpkXi50omEJEMlWolgaHiH56f8FrEeDf8HrOvc2z90cLaWRV-kG2KdE6e1-0OtkoKwOQpOoO1pRjQMipQRldU7dnydT0Uv0UjXXzRhNIsKz-TKMVxeQgIBIWbig1ce146hiRsWEv7kLD5RxH9e_rrnwnNiLDV1yeoKRhADatyuwd1A89WK6tepbTY6jM6UIYty_kTexxbZny5Jb5CbPhX4byByed6KoBpoJhhz2AkNaCggukz4WH05jSBy8U4TPtuTHFDtZHgBxZWdfKBly0rXF9OtdsoWBoio5Dpw6rG6F4fjPOD6WkefuGTogLbmpRayOFlldtwHMfQ" target="_blank" rel="noopener noreferrer"><picture><source media="(prefers-color-scheme: dark)" srcset="https://cursor.com/assets/images/fix-in-cursor-dark.png"><source media="(prefers-color-scheme: light)" srcset="https://cursor.com/assets/images/fix-in-cursor-light.png"><img alt="Fix in Cursor" width="115" height="28" src="https://cursor.com/assets/images/fix-in-cursor-dark.png"></picture></a>&nbsp;<a href="https://cursor.com/agents?data=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImJ1Z2JvdC12MiJ9.eyJ2ZXJzaW9uIjoxLCJ0eXBlIjoiQlVHQk9UX0ZJWF9JTl9XRUIiLCJkYXRhIjp7InJlZGlzS2V5IjoiYnVnYm90OjYxMWMzNmQwLWQ1M2MtNDUyNS05ZDNkLTI5YTRjY2U0YWJmNyIsImVuY3J5cHRpb25LZXkiOiJjQWx2UWs1d2FKRTNOMDRleExidVlvdGpHT3lYdGRuRGpLeXNSQUIxTGs0IiwiYnJhbmNoIjoicHNfZml4X3NlY3VyaXR5X2NvbmNlcm5fcGFzc3dvcmRfZXhwb3NlZF90aHJvdWdoX19yZXByX18iLCJyZXBvT3duZXIiOiJyZWRpcyIsInJlcG9OYW1lIjoicmVkaXMtcHkiLCJwck51bWJlciI6Mzk5OCwiY29tbWl0U2hhIjoiMDFmYTdhOWQ4Njk4NjUyZGQwZjBmYWY4OGE2ZWE0MDk4NDllZGRlNCIsInByb3ZpZGVyIjoiZ2l0aHViIn0sImlhdCI6MTc3MzE1MDI4NSwiZXhwIjoxNzc1NzQyMjg1fQ.bVyA1guCmG7OzQ-KZ4yvdQlEB0fisvvK2znJDUcSC1kcm88c_ZduViVbJVXw41NbrXz3CACZEYEuKoXTYJjYIJQGcTFB3zVdbsUptPi-UKq9_VS85EDY6c0iSkQog7Tz3w0w27m3CF4Id5901KPcqle51D5OiNgR-F8nbee9Tsxi6r8hb-YD07p8Nyvd1Zu-eS7DVwp9rHyWaaN1z9WMyx4vT0FRrrMSG_B3OboXVR-7RQ2DDKJAoZ9aP-uGaVFZUAhjbbhWILIj0FuSQgcWpC26tYtoKwre5JRMcwtBd2EXZkDNiBJ4eg9Qb7xD2H7bqn57PAHB_UpFvlilG_-O3g" target="_blank" rel="noopener noreferrer"><picture><source media="(prefers-color-scheme: dark)" srcset="https://cursor.com/assets/images/fix-in-web-dark.png"><source media="(prefers-color-scheme: light)" srcset="https://cursor.com/assets/images/fix-in-web-light.png"><img alt="Fix in Web" width="99" height="28" src="https://cursor.com/assets/images/fix-in-web-dark.png"></picture></a></p>

**@petyaslavova** on `redis/connection.py`:

Since the data is added separately in both connection pool, it is ok to have those separate as well. The arguments in both objects are not completely in sync.

## Files Changed in Fix

- `.github/workflows/integration.yaml` (modified, +1/-0)
- `redis/asyncio/connection.py` (modified, +16/-1)
- `redis/connection.py` (modified, +16/-1)
- `tests/test_asyncio/test_connection_pool.py` (modified, +25/-0)
- `tests/test_connection_pool.py` (modified, +25/-0)

## `redis/asyncio/connection.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

### `redis/connection.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify the source files listed above (not test files)
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
