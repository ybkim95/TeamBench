"""Authenticated API client."""
import requests
from requests.auth import HTTPBasicAuth


class AuthClient:
    """API client with basic authentication."""

    def __init__(self, base_url, username, password):
        self.base_url = base_url.rstrip("/")
        self.auth = HTTPBasicAuth(username, password)
        self.session = requests.Session()
        self.session.auth = self.auth

    def get_protected(self, path):
        """GET a protected resource."""
        url = f"{self.base_url}/{path.lstrip('/')}"
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return response.json()

    def close(self):
        self.session.close()
