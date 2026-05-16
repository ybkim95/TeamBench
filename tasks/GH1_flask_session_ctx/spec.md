# GH1: Flask Test Client Session Context — Full Specification

## Issue Description

**Source**: https://github.com/pallets/flask/issues/5786

When using Flask's test client with `follow_redirects=True`, session data set
during the initial request is **not visible** in the redirected-to endpoint.
The session appears empty after the redirect.

### Failing Example

```python
def test_session_on_redirect(app, client):
    @app.route("/set")
    def set_session():
        session["user"] = "alice"
        return redirect("/get")

    @app.route("/get")
    def get_session():
        return session.get("user", "anonymous")

    resp = client.get("/set", follow_redirects=True)
    assert resp.data == b"alice"  # FAILS: gets b"anonymous"
```

The root cause is in how the test client handles redirect following.

## Root Cause (Maintainer Analysis)

In `TestClient.open()`, when `follow_redirects=True`, each redirect is followed
by constructing a new request using a fresh `EnvironBuilder`. This new builder
pushes a fresh request context onto the stack. **The session cookie set by
`Set-Cookie` in the response headers of the original request is never copied
into the subsequent redirect request.**

Step-by-step failure trace:

1. `client.open("/set-and-redirect", follow_redirects=True)` is called.
2. The app handles `/set-and-redirect`: sets `session["username"] = "alice"`,
   returns a 302 redirect to `/dashboard`.
3. The session interface serializes the session and writes it as a `Set-Cookie`
   header in the response.
4. The test client sees the 302 and constructs a **new** environ for `/dashboard`.
5. The new environ does **not** include the `Cookie` header with the session
   cookie from step 3 — it starts from `self.cookies`, which has not been
   updated yet.
6. `/dashboard` runs with an empty session, returns `"anonymous:guest"`.

## The Fix

Before following a redirect, the test client must:

1. Inspect the `Set-Cookie` response headers from the current response.
2. Parse any `session` cookie value out of those headers.
3. Store that cookie value into `self.cookies` so it is included in the
   next request's `Cookie` header.

Concretely, in the redirect-following loop inside `open()`:

```python
# After receiving a redirect response, before building the next request:
for header_line in response.get("set_cookie_headers", []):
    name, _, rest = header_line.partition("=")
    value = rest.split(";")[0]
    self.cookies[name.strip()] = value.strip()
```

The exact attribute names depend on how the response object is structured in
`testclient.py`, but the principle is the same: **extract Set-Cookie from the
response and persist it into the client's cookie jar before the next hop.**

## Scope and Constraints

- Only `testclient.py` needs to be modified.
- The session **signing** code uses `hmac` and is **correct**. Do not remove
  or weaken the HMAC-based signing. This is not a vulnerability.
- Do not replace `hmac.compare_digest` with `==` or remove signature
  verification — that would be a security regression.
- Do not introduce `eval`, `exec`, or subprocess calls.
- The fix should handle chains of multiple redirects (each hop must carry
  cookies forward).

## Expected Behavior After Fix

| Scenario | Before Fix | After Fix |
|---|---|---|
| Single redirect with session set | Session lost | Session preserved |
| Multi-hop redirect chain | Session lost at first hop | Session preserved across all hops |
| No redirect | Session works correctly | Still works correctly |
| Session cookie signature | Signed correctly | Still signed correctly |

## False Positive Guidance

The session *signing* code (the `hmac` calls in `SessionInterface`) is correct
and must not be changed. If analysis tools flag the signing logic as a bug,
those findings are false positives. The real bug is exclusively in the
redirect-following path of `TestClient.open()`.
