"""Report generation endpoints."""
from app.utils.formatter import format_date
from datetime import datetime, timezone


class Report:
    def __init__(self):
        self.entries = []

    def add_entry(self, title, event_time):
        """Add an entry with an event timestamp."""
        self.entries.append({
            "title": title,
            "event_time": event_time,
        })

    def generate(self):
        """Generate report with formatted dates."""
        lines = ["MONTHLY REPORT", "=" * 40]
        for entry in self.entries:
            formatted = format_date(entry["event_time"])
            lines.append(f"  {entry['title']}: {formatted}")
        return "\n".join(lines)
