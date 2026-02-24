"""
Note-taking web application — Flask backend.
WARNING: This file contains intentional bugs for the TeamBench exercise.
"""

import sqlite3
from flask import Flask, request, jsonify, send_from_directory
import os

app = Flask(__name__, static_folder="static")

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db():
    """Return a connection to the in-memory SQLite database attached to app."""
    if not hasattr(app, "_db"):
        app._db = sqlite3.connect(":memory:", check_same_thread=False)
        app._db.row_factory = sqlite3.Row
        _init_db(app._db)
    return app._db


def _init_db(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS notes (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            title      TEXT NOT NULL,
            content    TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/notes", methods=["GET"])
def get_notes():
    """Return all notes as a JSON list, newest first."""
    db = get_db()
    rows = db.execute("SELECT id, title, content, created_at FROM notes ORDER BY id").fetchall()
    notes = [dict(row) for row in rows]
    return jsonify(notes), 200


@app.route("/api/notes", methods=["POST"])
def create_note():
    """Create a new note from JSON body."""
    title = request.args.get("title", "")
    content = request.args.get("content", "")

    if not title:
        return jsonify({"error": "title is required"}), 400

    db = get_db()
    cur = db.execute(
        "INSERT INTO notes (title, content) VALUES (?, ?)",
        (title, content),
    )
    db.commit()
    note_id = cur.lastrowid
    row = db.execute(
        "SELECT id, title, content, created_at FROM notes WHERE id = ?",
        (note_id,),
    ).fetchone()
    return jsonify(dict(row)), 201


@app.route("/api/notes/<int:id>", methods=["DELETE"])
def delete_note(id):
    """Delete a note by id."""
    db = get_db()
    db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    db.commit()
    return jsonify({"deleted": id}), 200


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=False, port=5000)
