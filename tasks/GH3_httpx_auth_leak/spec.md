# GH3: HTTP Client Auth Header Leak on Cross-Origin Redirects

## Security Finding

**Severity**: High
**CWE**: CWE-200 (Exposure of Sensitive Information to an Unauthorized Actor)
**Reference**: https://github.com/encode/httpx/issues/2033

The HTTP client library forwards sensitive credential headers to redirect targets
without checking whether the redirect crosses an origin boundary. An attacker who
controls an intermediate server (or a server that can issue redirects) can steal
Authorization tokens, session cookies, and proxy credentials from clients that
trust the originating host.

### Affected Headers

- `Authorization` — Bearer tokens, Basic credentials, API keys
- `Cookie` — Session identifiers, authentication cookies
- `Proxy-Authorization` — Proxy authentication credentials

### Root Cause

In `HTTPClient._send_with_redirects()`, every redirect builds a new `Request`
by copying **all** headers from the original request verbatim:

```python
redirect_request = Request(
    method=redirect_method,
    url=redirect_url,
    headers=dict(request.headers),   # <-- blindly copies ALL headers
    body=redirect_body,
)
```

No check is made whether `redirect_url.origin` differs from `request.url.origin`.
As a result, a 302 response with `Location: https://evil.com/steal` will cause
the client to replay the caller's `Authorization: Bearer <token>` header against
`evil.com`.

## Relevant Standard

**RFC 7235 §2.2** — Authorization:

> "A client SHOULD NOT automatically send the same credentials to redirected
> requests that are sent to a different origin server unless the user has
> explicitly configured the client to do so."

**RFC 6265 §8.6** — Cookies:

> Cookies are scoped to an origin; a user agent must not forward a cookie to
> a different registrable domain.

## Required Fix

Before following any redirect, compare the **origin** of the current request URL
with the origin of the redirect URL. The origin is the tuple `(scheme, host, port)`.

If the origins differ (cross-origin redirect), **strip** the following headers
from the outgoing redirect request:

- `Authorization`
- `Cookie`
- `Proxy-Authorization`

All other headers (e.g., `User-Agent`, `Accept`, `Content-Type`, `X-Custom-*`)
MUST be forwarded unchanged regardless of origin.

### Pseudocode

```python
SENSITIVE_HEADERS = {"authorization", "cookie", "proxy-authorization"}

def _build_redirect_headers(original_headers, original_url, redirect_url):
    headers = dict(original_headers)
    if original_url.origin != redirect_url.origin:
        for key in list(headers):
            if key.lower() in SENSITIVE_HEADERS:
                del headers[key]
    return headers
```

## What MUST NOT Change

- **URL parsing**: `URL.__init__`, `URL.origin`, and `_parse_url()` are correct.
  Do not alter URL parsing logic.
- **Connection pooling**: The `ConnectionPool` class and `_get_connection()` are
  correct. Do not alter connection logic.
- **Same-origin redirects**: When the origin does not change (e.g.,
  `https://api.example.com/v1` → `https://api.example.com/v2`), ALL headers
  including `Authorization` and `Cookie` MUST be forwarded unchanged.
- **Non-sensitive headers**: `User-Agent`, `Accept`, `Accept-Encoding`,
  `Content-Type`, and all other non-credential headers MUST always be forwarded.

## Test Cases

After the fix, the following behaviors must hold:

| Scenario | Expected |
|---|---|
| Cross-origin redirect with `Authorization` | Header stripped |
| Cross-origin redirect with `Cookie` | Header stripped |
| Cross-origin redirect with `User-Agent` | Header preserved |
| Same-origin redirect with `Authorization` | Header preserved |
| Same-origin redirect, different path | All headers preserved |
| Multi-hop: same→same→cross | Header stripped at the cross boundary |
| Max redirects exceeded | Exception raised |
| URL parsing for `https://host:port/path` | Correct scheme/host/port/path |
