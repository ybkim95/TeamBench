"""
Flask app for P3_access_control.
Enforces RBAC using the check_permission function from rbac.py.
Uses X-Role header to identify the role of the requester.
Maintains an audit_trail list of all access decisions.
"""
from flask import Flask, request, jsonify, abort
from rbac import check_permission, PERMISSIONS

app = Flask(__name__)

# Audit trail: list of dicts with keys: role, endpoint, method, allowed
audit_trail = []


def _enforce_rbac():
    """Before-request hook to enforce RBAC on all routes."""
    role = request.headers.get('X-Role', '')
    # Strip leading slash from path
    endpoint = request.path.lstrip('/')
    method = request.method.upper()

    allowed = check_permission(role, endpoint, method)

    # Record in audit trail
    audit_trail.append({
        'role': role,
        'endpoint': endpoint,
        'method': method,
        'allowed': allowed,
    })

    if not allowed:
        abort(403)


app.before_request(_enforce_rbac)


def _make_routes():
    """Dynamically register routes for all endpoints in PERMISSIONS."""
    # Collect all unique endpoints from PERMISSIONS
    endpoints = set()
    for allowed_set in PERMISSIONS.values():
        for (ep, _method) in allowed_set:
            endpoints.add(ep)

    # Also add some common endpoints in case PERMISSIONS is empty at import time
    common_endpoints = [
        'users', 'reports', 'settings', 'logs', 'items', 'data',
        'admin', 'profile', 'documents', 'files', 'records',
    ]
    for ep in common_endpoints:
        endpoints.add(ep)

    for ep in endpoints:
        # Create a unique view function for each endpoint
        def make_view(endpoint_name):
            def view_func(**kwargs):
                return jsonify({'endpoint': endpoint_name, 'status': 'ok'}), 200
            view_func.__name__ = f'route_{endpoint_name}'
            return view_func

        app.add_url_rule(
            f'/{ep}',
            endpoint=f'route_{ep}',
            view_func=make_view(ep),
            methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'],
        )


_make_routes()


@app.route('/health')
def health():
    return jsonify({'status': 'ok'}), 200


if __name__ == '__main__':
    app.run(debug=False)
