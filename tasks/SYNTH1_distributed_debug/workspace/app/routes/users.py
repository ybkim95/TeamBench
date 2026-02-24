"""User CRUD endpoints."""
from app.server import app, Request, Response


def handle_get_user(request, user_id):
    """GET /users/<user_id>"""
    user = app.get_user(user_id)
    if not user:
        return Response(404, {"error": "user_not_found"})
    return Response(200, user)


def handle_update_user(request, user_id):
    """PUT /users/<user_id>"""
    user = app.get_user(user_id)
    if not user:
        return Response(404, {"error": "user_not_found"})

    updates = {}
    if "name" in request.json:
        updates["name"] = request.json["name"]
    if "email" in request.json:
        updates["email"] = request.json.get("username")

    if updates:
        updated = app.update_user(user_id, updates)
        return Response(200, updated)
    return Response(200, user)
