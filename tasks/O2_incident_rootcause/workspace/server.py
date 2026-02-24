"""
Simple data API server.
Serves items from the data store via /api/data endpoint.
"""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

DATA_PATH = "data.json"


def load_data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
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
        if self.path == "/api/data":
            try:
                raw = load_data()
                items = raw["items"]
                self._send(200, json.dumps({"data": items, "count": len(items)}))
            except KeyError:
                self._send(500, json.dumps({"error": "internal"}))
        elif self.path == "/health":
            self._send(200, json.dumps({"status": "ok"}))
        else:
            self._send(404, json.dumps({"error": "not_found"}))


def main():
    server = HTTPServer(("127.0.0.1", 8080), Handler)
    print("Serving on 127.0.0.1:8080")
    server.serve_forever()


if __name__ == "__main__":
    main()
