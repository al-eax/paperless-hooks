"""HTTP backend using Python's built-in http.server."""

import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any, Callable, Dict

from backends.base import BackendInterface

logger = logging.getLogger(__name__)


class _JsonRouteHandler(BaseHTTPRequestHandler):
    """Request handler that dispatches POST requests to registered routes."""

    routes: Dict[str, Callable[[dict], Any]] = {}

    def do_POST(self):
        handler = self.routes.get(self.path)
        if handler is None:
            self.send_error(404, "Not Found")
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body) if body else {}
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.send_error(400, "Invalid JSON")
            return

        try:
            handler(data)
        except Exception:
            logger.exception("Error in handler for %s", self.path)
            self._respond(500, {"status": "error"})
            return

        self._respond(200, {"status": "ok"})

    def _respond(self, code: int, body: dict) -> None:
        payload = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


class HttpServerBackend(BackendInterface):
    """HTTP backend wrapping a stdlib ``HTTPServer`` instance.

    Usage::

        from http.server import HTTPServer

        server = HTTPServer(("0.0.0.0", 8080), None)
        backend = HttpServerBackend(server)
        hooks = PaperlessHooks(..., backend=backend)
        hooks.init()
        server.serve_forever()
    """

    def __init__(self, server: HTTPServer) -> None:
        self._server = server
        self._server.RequestHandlerClass = _JsonRouteHandler

    def add_json_endpoint(self, path: str, json_handler: Callable[[dict], Any]) -> None:
        logger.info("Registering built-in HTTP webhook endpoint: %s", path)
        _JsonRouteHandler.routes[path] = json_handler
