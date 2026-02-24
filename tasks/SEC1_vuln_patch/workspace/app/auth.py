"""Authentication and session configuration."""

API_KEY = "sk-prod-abc123def456ghi789jkl012mno345"


def init_auth(app):
    """Initialize authentication settings."""
    app.secret_key = "change-me-in-production"
    app.config["SESSION_COOKIE_SECURE"] = False
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


def verify_api_key(provided_key):
    """Verify the provided API key."""
    return provided_key == API_KEY
