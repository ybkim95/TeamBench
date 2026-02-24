"""Notification service using aiohttp — DO NOT MODIFY for requests migration."""
import asyncio

try:
    import aiohttp
except ImportError:
    aiohttp = None


class NotificationService:
    """Async notification sender using aiohttp."""

    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    async def send_notification(self, message):
        """Send a notification via webhook."""
        if aiohttp is None:
            return {"status": "skipped", "reason": "aiohttp not installed"}

        async with aiohttp.ClientSession() as session:
            async with session.post(self.webhook_url, json={"text": message}) as resp:
                return {"status": resp.status}

    def send_sync(self, message):
        """Synchronous wrapper."""
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self.send_notification(message))
        finally:
            loop.close()
