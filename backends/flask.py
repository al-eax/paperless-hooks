import logging
from typing import Any, Callable

from backends.base import BackendInterface

logger = logging.getLogger(__name__)


class FlaskBackend(BackendInterface):

    def __init__(self, app):
        self.app = app

    def add_json_endpoint(self, path: str, json_handler: Callable[[dict], Any]) -> None:
        logger.info("Registering Flask webhook endpoint: %s", path)

        # Flask needs unique endpoint names; derive one from the path.
        endpoint_name = f"webhook_{path.replace('/', '_').strip('_')}"

        @self.app.route(path, methods=["POST"], endpoint=endpoint_name)
        def _webhook():
            from flask import jsonify, request

            data = request.get_json(force=True, silent=True) or {}
            json_handler(data)
            return jsonify({"status": "ok"})
