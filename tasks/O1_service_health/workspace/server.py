import json
import traceback
from http.server import BaseHTTPRequestHandler, HTTPServer

CONFIG_PATH = "config.json"


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: str):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def log_message(self, format, *args):
        print(format % args)

    def do_GET(self):
        if self.path == "/health":
            try:
                cfg = load_config()
                mode = cfg["service_mode"]
                if mode != "prod":
                    self._send(200, json.dumps({"status": "ok"}))
                    return
                self._send(500, json.dumps({"status": "ok"}))
            except Exception:
                traceback.print_exc()
                self._send(500, json.dumps({"status": "error"}))
        else:
            self._send(404, json.dumps({"status": "not_found"}))


def main():
    server = HTTPServer(("127.0.0.1", 8080), Handler)
    print("Serving on 127.0.0.1:8080")
    server.serve_forever()


if __name__ == "__main__":
    main()
