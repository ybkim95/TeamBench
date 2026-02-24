"""Batch API client with retry logic."""
import requests
from requests.exceptions import ConnectionError


class BatchClient:
    """Client for batch operations with retry."""

    def __init__(self, base_url, max_retries=3):
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries

    def send_batch(self, items):
        """Send a batch of items with retry on connection errors."""
        url = f"{self.base_url}/batch"
        for attempt in range(self.max_retries):
            try:
                response = requests.post(url, json={"items": items}, timeout=30)
                response.raise_for_status()
                return response.json()
            except ConnectionError:
                if attempt == self.max_retries - 1:
                    raise
        return None
