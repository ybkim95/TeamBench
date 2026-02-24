"""HTTP service with request handling."""
import json
import time
import re
from http.server import BaseHTTPRequestHandler, HTTPServer
from service.middleware.validator import validate_input
from service.middleware.tls_handler import get_tls_context
from service.middleware.circuit_breaker import call_external_service


class Config:
    """Service configuration."""
    def __init__(self, config_path="service/config.json"):
        with open(config_path) as f:
            self._config = json.load(f)

    @property
    def port(self):
        return self._config.get("port", 8080)

    @property
    def tls_enabled(self):
        return self._config.get("tls_enabled", False)

    @property
    def validate_input(self):
        return self._config.get("validate_input", True)

    @property
    def api_token(self):
        return self._config.get("api_token", "")


config = Config()


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def log_message(self, format, *args):
        pass  # Suppress logs for benchmarking

    def do_POST(self):
        if self.path == "/process":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()

            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                self._send(400, {"error": "invalid_json"})
                return

            # Validate input
            if config.validate_input:
                start = time.time()
                is_valid, errors = validate_input(data)
                elapsed = time.time() - start
                if not is_valid:
                    self._send(400, {"error": "validation_failed", "details": errors})
                    return

            # Call external service (with circuit breaker if configured)
            ext_result = call_external_service(data)

            self._send(200, {"status": "processed", "result": ext_result})

        elif self.path == "/health":
            self._send(200, {"status": "ok"})
        else:
            self._send(404, {"error": "not_found"})


def main():
    server = HTTPServer(("127.0.0.1", config.port), Handler)
    print(f"Serving on 127.0.0.1:{config.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
