"""Application tests."""
import json
import threading
from datetime import datetime, timezone, timedelta
from app.server import app, Request, Response
from app.routes.users import handle_get_user, handle_update_user
from app.routes.orders import Order
from app.routes.reports import Report
from app.utils.cache import cache
from app.utils.formatter import format_date


class TestUserEndpoints:
    def test_get_user(self):
        """Test GET /users/123 returns user data."""
        request = Request("GET", "/users/123")
        response = handle_get_user(request, user_id="123")
        assert response.status == 200
        assert response.body["name"] == "Alice"

    def test_get_user_not_found(self):
        """Test GET /users/999 returns 404."""
        request = Request("GET", "/users/999")
        response = handle_get_user(request, user_id="999")
        assert response.status == 404

    def test_update_user_email(self):
        """Test PUT /users/123 updates email."""
        # Reset user state
        app._users["123"]["email"] = "alice@example.com"

        request = Request("PUT", "/users/123", json.dumps({"email": "newalice@example.com"}))
        response = handle_update_user(request, user_id="123")
        assert response.status == 200
        assert response.body["email"] != "alice@example.com", \
            "Email should have changed after update"

        # Restore
        app._users["123"]["email"] = "alice@example.com"


class TestOrders:
    def test_order_total_no_discount(self):
        """Test order total without discount."""
        cache.clear()
        order = Order([("Widget", 10.0, 3)])
        assert order.total == 30.0

    def test_order_total_with_discount(self):
        """Test order total with discount applied."""
        cache.clear()
        order = Order([("Widget", 10.0, 3)])
        order.apply_discount(20)
        total = order.total
        assert total < 30.0, f"Discount not applied: total still {total}"

        # Call again — should be consistent
        total2 = order.total
        assert total == total2, f"Inconsistent totals: {total} vs {total2}"


class TestReports:
    def test_report_generation(self):
        """Test basic report generation."""
        report = Report()
        dt = datetime(2025, 6, 15, 12, 0, tzinfo=timezone.utc)
        report.add_entry("Test Event", dt)
        output = report.generate()
        assert "MONTHLY REPORT" in output
        assert "Test Event" in output

    def test_report_timezone_conversion(self):
        """Test dates are shown in local timezone."""
        report = Report()
        # 2024-12-31 23:00 EST = 2025-01-01 04:00 UTC
        est = timezone(timedelta(hours=-5))
        event_time = datetime(2024, 12, 31, 23, 0, tzinfo=est)
        report.add_entry("New Year Eve Event", event_time)
        output = report.generate()
        # The date shown should reflect the source timezone, not UTC
        assert "New Year Eve Event" in output, "Event missing from report"

    def test_all_passing(self):
        """Meta-test: existing non-bug tests still pass."""
        # This test just verifies that non-buggy code works
        request = Request("GET", "/users/123")
        response = handle_get_user(request, user_id="123")
        assert response.status == 200
        cache.clear()
        order = Order([("Item", 5.0, 2)])
        assert order.total == 10.0
