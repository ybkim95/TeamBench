"""Response parsing utilities."""


def safe_json(response):
    """Safely parse JSON from a response, handling empty bodies.

    With requests library, empty body raises ValueError.
    """
    try:
        return response.json()
    except ValueError:
        return None


def extract_data(response):
    """Extract data from API response."""
    body = safe_json(response)
    if body is None:
        return []
    return body.get("data", [])


def extract_error(response):
    """Extract error message from API response."""
    body = safe_json(response)
    if body is None:
        return "unknown error"
    return body.get("error", "unknown error")
