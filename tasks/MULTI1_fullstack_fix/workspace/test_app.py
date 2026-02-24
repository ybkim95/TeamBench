"""
Test suite for MULTI1_fullstack_fix.
Uses Flask's built-in test client — no live server required.
Do NOT modify this file.
"""

import json
import os
import re
import unittest


# ---------------------------------------------------------------------------
# Flask test client setup
# ---------------------------------------------------------------------------

class NoteAppTestCase(unittest.TestCase):

    def setUp(self):
        """Create a fresh app and in-memory database for each test."""
        # Import here so each test gets a clean module state via app._db reset
        import importlib
        import app as app_module
        importlib.reload(app_module)          # fresh in-memory DB every test
        self.app_module = app_module
        self.client = app_module.app.test_client()
        app_module.app.testing = True

    # ------------------------------------------------------------------
    # Test 1: Create a note — expects 201 and JSON body with correct fields
    # ------------------------------------------------------------------
    def test_create_note(self):
        """POST /api/notes with JSON body should return 201 and the new note."""
        res = self.client.post(
            "/api/notes",
            data=json.dumps({"title": "Hello", "content": "World"}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 201, msg=f"Expected 201, got {res.status_code}")
        data = json.loads(res.data)
        self.assertEqual(data["title"], "Hello", msg=f"title mismatch: {data}")
        self.assertEqual(data["content"], "World", msg=f"content mismatch: {data}")
        self.assertIn("id", data)
        self.assertIn("created_at", data)

    # ------------------------------------------------------------------
    # Test 2: Get notes — expects 200 and a JSON list
    # ------------------------------------------------------------------
    def test_get_notes(self):
        """GET /api/notes should return 200 and a JSON list."""
        # Seed one note
        self.client.post(
            "/api/notes",
            data=json.dumps({"title": "A", "content": "B"}),
            content_type="application/json",
        )
        res = self.client.get("/api/notes")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIsInstance(data, list, msg="Expected a list of notes")
        self.assertGreater(len(data), 0, msg="Expected at least one note")

    # ------------------------------------------------------------------
    # Test 3: Notes sorted newest-first
    # ------------------------------------------------------------------
    def test_notes_sorted(self):
        """GET /api/notes should return notes sorted by created_at DESC."""
        import time

        self.client.post(
            "/api/notes",
            data=json.dumps({"title": "First", "content": "oldest"}),
            content_type="application/json",
        )
        # Small sleep so SQLite datetime differs
        time.sleep(0.05)
        self.client.post(
            "/api/notes",
            data=json.dumps({"title": "Second", "content": "newest"}),
            content_type="application/json",
        )

        res = self.client.get("/api/notes")
        data = json.loads(res.data)
        self.assertGreaterEqual(len(data), 2, msg="Expected at least 2 notes")
        self.assertEqual(
            data[0]["title"],
            "Second",
            msg=f"Expected newest note first, got: {[n['title'] for n in data]}",
        )

    # ------------------------------------------------------------------
    # Test 4: Delete a note — expects 200
    # ------------------------------------------------------------------
    def test_delete_note(self):
        """DELETE /api/notes/<id> should return 200 and remove the note."""
        # Create
        res = self.client.post(
            "/api/notes",
            data=json.dumps({"title": "ToDelete", "content": "bye"}),
            content_type="application/json",
        )
        note = json.loads(res.data)
        note_id = note["id"]

        # Delete
        del_res = self.client.delete(f"/api/notes/{note_id}")
        self.assertEqual(del_res.status_code, 200, msg=f"Expected 200, got {del_res.status_code}")

        # Confirm gone
        list_res = self.client.get("/api/notes")
        notes = json.loads(list_res.data)
        ids = [n["id"] for n in notes]
        self.assertNotIn(note_id, ids, msg="Deleted note still present in list")

    # ------------------------------------------------------------------
    # Test 5: deploy.sh has correct FLASK_APP value
    # ------------------------------------------------------------------
    def test_deploy_script_env(self):
        """deploy.sh must export FLASK_APP=app.py (not application.py)."""
        deploy_path = os.path.join(os.path.dirname(__file__), "deploy.sh")
        self.assertTrue(os.path.exists(deploy_path), msg="deploy.sh not found")
        with open(deploy_path) as f:
            content = f.read()
        self.assertIn(
            "FLASK_APP=app.py",
            content,
            msg="deploy.sh does not contain FLASK_APP=app.py",
        )
        self.assertNotIn(
            "FLASK_APP=application.py",
            content,
            msg="deploy.sh still contains the buggy FLASK_APP=application.py",
        )

    # ------------------------------------------------------------------
    # Test 6: static/app.js uses application/json Content-Type
    # ------------------------------------------------------------------
    def test_frontend_content_type(self):
        """static/app.js fetch POST must use Content-Type: application/json."""
        js_path = os.path.join(os.path.dirname(__file__), "static", "app.js")
        self.assertTrue(os.path.exists(js_path), msg="static/app.js not found")
        with open(js_path) as f:
            content = f.read()
        self.assertIn(
            "application/json",
            content,
            msg="static/app.js does not contain 'application/json' in Content-Type",
        )
        self.assertNotIn(
            "text/plain",
            content,
            msg="static/app.js still contains the buggy 'text/plain' Content-Type",
        )


if __name__ == "__main__":
    unittest.main()
