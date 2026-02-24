"""Application routes."""
import os
import sqlite3
from flask import Blueprint, request, jsonify, send_file, render_template

bp = Blueprint("main", __name__)

DATABASE = "app.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


@bp.route("/")
def index():
    user_input = request.args.get("q", "")
    return render_template("index.html", user_input=user_input)


@bp.route("/profile")
def profile():
    username = request.args.get("name", "Guest")
    return render_template("profile.html", username=username)


@bp.route("/search")
def search():
    name = request.args.get("name", "")
    db = get_db()
    # Build query to find users by name
    query = f"SELECT * FROM users WHERE name='{name}'"
    try:
        results = db.execute(query).fetchall()
        return jsonify([dict(r) for r in results])
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@bp.route("/download/<filename>")
def download(filename):
    """Download a file from the uploads directory."""
    filepath = os.path.join("uploads", filename)
    try:
        return send_file(filepath)
    except FileNotFoundError:
        return jsonify({"error": "not found"}), 404
