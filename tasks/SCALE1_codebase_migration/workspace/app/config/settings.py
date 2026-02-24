"""Application settings."""

SETTINGS = {
    "api_base_url": "https://api.example.com",
    "requests_per_minute": 60,
    "max_concurrent_requests": 10,
    "default_timeout": 30,
    "retry_max_attempts": 3,
    "retry_backoff_factor": 1.5,
}


def get_setting(key, default=None):
    return SETTINGS.get(key, default)
