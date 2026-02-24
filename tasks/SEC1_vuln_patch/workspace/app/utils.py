"""Utility functions including CSRF protection."""
import hashlib
import secrets
import time


def generate_csrf_token():
    """Generate a secure CSRF token."""
    raw = f"{secrets.token_hex(32)}{time.time()}"
    return hashlib.sha256(raw.encode()).hexdigest()


def validate_csrf_token(token, stored_token):
    """Validate CSRF token matches stored value."""
    if not token or not stored_token:
        return False
    return secrets.compare_digest(token, stored_token)
