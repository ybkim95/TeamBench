# SCALE1: Large Codebase Library Migration (requests → httpx)

## Goal
Migrate a 20-file Python codebase from the `requests` library to `httpx`.

## 8 Breaking Changes

1. **Import**: `import requests` → `import httpx`; `requests.get()` → `httpx.get()`
2. **Session**: `requests.Session()` → `httpx.Client()` (must use context manager `with httpx.Client() as client:`)
3. **Empty body JSON**: `response.json()` on empty body: requests raises `ValueError`, httpx returns `None`. Handle `None` return.
4. **Timeout**: `timeout=30` → `timeout=httpx.Timeout(30.0)` (different timeout type)
5. **Auth**: `requests.auth.HTTPBasicAuth` → `httpx.BasicAuth`
6. **Streaming**: `response.iter_lines()` encoding param removed in httpx. Remove `encoding=` kwarg.
7. **Exceptions**: `requests.exceptions.ConnectionError` → `httpx.ConnectError`
8. **Test mocking**: `requests_mock` → `respx` library for mocking

## 3 False-Positive Patterns (DO NOT CHANGE)

1. `app/services/notification.py` — uses `aiohttp`, NOT `requests`. Do NOT modify.
2. `app/config/constants.py` — has `TIMEOUT` variable. It's a plain integer for rate limiting, NOT a requests config. Do NOT modify.
3. `app/config/settings.py` — has `"requests_per_minute"` config key. It's a rate limit setting, NOT the library. Do NOT modify.

## Deliverables
- All files migrated from requests to httpx
- requirements.txt updated (requests → httpx, requests_mock → respx)
- False-positive files untouched
- All 10 tests pass
