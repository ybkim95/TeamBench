"""Retry logic for HTTP requests."""
import time
import requests
from requests.exceptions import ConnectionError


def retry_request(method, url, max_retries=3, backoff=1.0, **kwargs):
    """Execute an HTTP request with retry logic."""
    last_error = None
    for attempt in range(max_retries):
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except ConnectionError as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(backoff * (2 ** attempt))
    raise last_error
