"""Tests for the web application. All should pass after the fix."""
from testclient import App, TestClient

app = App(secret_key="test-secret-key")

@app.route("/set-and-redirect")
def set_and_redirect(ctx):
    ctx.session["username"] = "alice"
    ctx.session["role"] = "admin"
    return {"status": 302, "headers": {"Location": "/dashboard"}}

@app.route("/dashboard")
def dashboard(ctx):
    user = ctx.session.get("username", "anonymous")
    role = ctx.session.get("role", "guest")
    return {"status": 200, "body": f"{user}:{role}"}

@app.route("/multi-redirect")
def multi_redirect(ctx):
    ctx.session["step"] = "1"
    return {"status": 302, "headers": {"Location": "/step2"}}

@app.route("/step2")
def step2(ctx):
    ctx.session["step"] = "2"
    return {"status": 302, "headers": {"Location": "/step3"}}

@app.route("/step3")
def step3(ctx):
    return {"status": 200, "body": ctx.session.get("step", "none")}

@app.route("/no-redirect")
def no_redirect(ctx):
    ctx.session["key"] = "value"
    return {"status": 200, "body": "ok"}

def test_session_persists_on_redirect():
    client = TestClient(app)
    resp = client.open("/set-and-redirect", follow_redirects=True)
    assert resp.body == "alice:admin", f"Expected 'alice:admin', got {resp.body!r}"

def test_session_persists_multi_redirect():
    client = TestClient(app)
    resp = client.open("/multi-redirect", follow_redirects=True)
    assert resp.body == "2", f"Expected '2', got {resp.body!r}"

def test_session_works_without_redirect():
    """This should already pass (no redirect involved)."""
    client = TestClient(app)
    resp = client.open("/no-redirect")
    assert resp.body == "ok"

def test_session_signing_intact():
    """Session signing must not be broken."""
    client = TestClient(app)
    client.open("/set-and-redirect")  # Don't follow redirect
    # Cookie should be signed
    assert "session" in client.cookies
    assert "." in client.cookies["session"]  # signature separator

if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            try:
                fn()
                print(f"  PASS: {name}")
            except AssertionError as e:
                print(f"  FAIL: {name}: {e}")
