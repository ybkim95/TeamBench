"""Flask-like application server (simplified for testing)."""
import json


class Request:
    def __init__(self, method, path, body=None):
        self.method = method
        self.path = path
        self.json = json.loads(body) if body else {}


class Response:
    def __init__(self, status=200, body=None):
        self.status = status
        self.body = body or {}

    def json(self):
        return self.body


class App:
    def __init__(self):
        self.routes = {}
        self._users = {
            "123": {"id": "123", "name": "Alice", "email": "alice@example.com"},
            "456": {"id": "456", "name": "Bob", "email": "bob@example.com"},
        }

    def route(self, path, methods=None):
        def decorator(func):
            self.routes[(path, tuple(methods or ["GET"]))] = func
            return func
        return decorator

    def handle(self, request):
        for (path_pattern, methods), handler in self.routes.items():
            if request.method in methods and self._match_path(path_pattern, request.path):
                params = self._extract_params(path_pattern, request.path)
                return handler(request, **params)
        return Response(404, {"error": "not_found"})

    def _match_path(self, pattern, path):
        p_parts = pattern.strip("/").split("/")
        r_parts = path.strip("/").split("/")
        if len(p_parts) != len(r_parts):
            return False
        return all(
            pp.startswith("<") or pp == rp
            for pp, rp in zip(p_parts, r_parts)
        )

    def _extract_params(self, pattern, path):
        p_parts = pattern.strip("/").split("/")
        r_parts = path.strip("/").split("/")
        params = {}
        for pp, rp in zip(p_parts, r_parts):
            if pp.startswith("<") and pp.endswith(">"):
                params[pp[1:-1]] = rp
        return params

    def get_user(self, user_id):
        return self._users.get(user_id)

    def update_user(self, user_id, data):
        if user_id in self._users:
            self._users[user_id].update(data)
            return self._users[user_id]
        return None


app = App()
