"""HTTP helper functions wrapping the requests library."""
import requests


def fetch_json(url, timeout=30):
    """Fetch JSON from a URL."""
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.json()


def post_json(url, data, timeout=30):
    """POST JSON to a URL."""
    response = requests.post(url, json=data, timeout=timeout)
    response.raise_for_status()
    return response.json()


def download_file(url, dest_path, timeout=60):
    """Download a file from URL."""
    response = requests.get(url, stream=True, timeout=timeout)
    response.raise_for_status()
    with open(dest_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    return dest_path
