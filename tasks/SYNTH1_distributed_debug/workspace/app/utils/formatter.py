"""Data formatting utilities."""
from datetime import datetime, timezone


def format_date(dt):
    """Format a datetime for display in reports.

    Args:
        dt: datetime object (may be in any timezone)

    Returns:
        Formatted date string YYYY-MM-DD
    """
    # Format the date directly
    return dt.strftime("%Y-%m-%d")
