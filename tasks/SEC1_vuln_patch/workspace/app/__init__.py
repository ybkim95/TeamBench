"""Flask web application."""
from flask import Flask


def create_app():
    app = Flask(__name__)
    app.config.from_object("app.config")

    from app.routes import bp as routes_bp
    app.register_blueprint(routes_bp)

    from app.auth import init_auth
    init_auth(app)

    return app
