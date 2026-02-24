"""HTTP API client using requests library."""
import requests


class ApiClient:
    """Generic API client wrapping requests.Session."""

    def __init__(self, base_url, timeout=30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def get(self, path, params=None):
        """GET request."""
        url = f"{self.base_url}/{path.lstrip('/')}"
        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def post(self, path, data=None):
        """POST request."""
        url = f"{self.base_url}/{path.lstrip('/')}"
        response = self.session.post(url, json=data, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def delete(self, path):
        """DELETE request — may return empty body."""
        url = f"{self.base_url}/{path.lstrip('/')}"
        response = self.session.delete(url, timeout=self.timeout)
        response.raise_for_status()
        try:
            return response.json()
        except ValueError:
            return None

    def close(self):
        """Close the session."""
        self.session.close()
