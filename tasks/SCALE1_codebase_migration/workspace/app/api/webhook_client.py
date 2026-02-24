"""Webhook client with streaming support."""
import requests


class WebhookClient:
    """Client for consuming webhook event streams."""

    def __init__(self, stream_url):
        self.stream_url = stream_url

    def consume_events(self, callback):
        """Consume streaming events."""
        response = requests.get(self.stream_url, stream=True, timeout=60)
        response.raise_for_status()

        for line in response.iter_lines(encoding="utf-8"):
            if line:
                callback(line)

    def close(self):
        pass
