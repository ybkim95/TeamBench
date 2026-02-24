"""Integration tests using requests_mock."""
import json
import pytest
import requests
import requests_mock


def test_get_users():
    """Test fetching users."""
    from app.api.client import ApiClient
    with requests_mock.Mocker() as m:
        m.get("https://api.example.com/users", json=[{"id": 1, "name": "Alice"}])
        client = ApiClient("https://api.example.com")
        users = client.get("/users")
        assert len(users) == 1
        assert users[0]["name"] == "Alice"
        client.close()


def test_post_user():
    """Test creating a user."""
    from app.api.client import ApiClient
    with requests_mock.Mocker() as m:
        m.post("https://api.example.com/users", json={"id": 2, "name": "Bob"})
        client = ApiClient("https://api.example.com")
        result = client.post("/users", data={"name": "Bob"})
        assert result["name"] == "Bob"
        client.close()


def test_delete_user_empty_body():
    """Test deleting a user returns None for empty body."""
    from app.api.client import ApiClient
    with requests_mock.Mocker() as m:
        m.delete("https://api.example.com/users/1", text="", status_code=204)
        client = ApiClient("https://api.example.com")
        result = client.delete("/users/1")
        assert result is None
        client.close()


def test_auth_client():
    """Test authenticated client."""
    from app.api.auth_client import AuthClient
    with requests_mock.Mocker() as m:
        m.get("https://api.example.com/protected", json={"secret": "data"})
        client = AuthClient("https://api.example.com", "user", "pass")
        result = client.get_protected("/protected")
        assert result["secret"] == "data"
        client.close()


def test_batch_client():
    """Test batch client with retry."""
    from app.api.batch_client import BatchClient
    with requests_mock.Mocker() as m:
        m.post("https://api.example.com/batch", json={"processed": 3})
        client = BatchClient("https://api.example.com")
        result = client.send_batch([1, 2, 3])
        assert result["processed"] == 3


def test_fetch_json_helper():
    """Test fetch_json helper."""
    from app.utils.http_helpers import fetch_json
    with requests_mock.Mocker() as m:
        m.get("https://example.com/data", json={"key": "value"})
        result = fetch_json("https://example.com/data")
        assert result["key"] == "value"


def test_post_json_helper():
    """Test post_json helper."""
    from app.utils.http_helpers import post_json
    with requests_mock.Mocker() as m:
        m.post("https://example.com/submit", json={"ok": True})
        result = post_json("https://example.com/submit", {"data": 1})
        assert result["ok"] is True


def test_retry_on_connection_error():
    """Test retry logic on connection errors."""
    from app.utils.retry import retry_request
    with requests_mock.Mocker() as m:
        m.get("https://example.com/flaky", [
            {"exc": requests.exceptions.ConnectionError},
            {"json": {"ok": True}},
        ])
        response = retry_request("GET", "https://example.com/flaky", max_retries=3, backoff=0.01)
        assert response.json()["ok"] is True


def test_response_parser():
    """Test response parser safe_json."""
    from app.utils.response_parser import safe_json, extract_data

    class MockResponse:
        def json(self):
            raise ValueError("No JSON")

    result = safe_json(MockResponse())
    assert result is None

    class MockResponse2:
        def json(self):
            return {"data": [1, 2, 3]}

    data = extract_data(MockResponse2())
    assert data == [1, 2, 3]


def test_notification_service_untouched():
    """Test that notification service still uses aiohttp (not migrated)."""
    import inspect
    from app.services.notification import NotificationService
    source = inspect.getsource(NotificationService)
    assert "aiohttp" in source, "NotificationService should still use aiohttp"
    assert "requests" not in source.lower() or "requests_per" in source.lower(), \
        "NotificationService should NOT have been migrated to httpx"
