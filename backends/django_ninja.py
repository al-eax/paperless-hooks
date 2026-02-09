import logging
from typing import Any, Callable

from backends.base import BackendInterface

logger = logging.getLogger(__name__)


class DjangoNinjaBackend(BackendInterface):

    def __init__(self, api):
        self.api = api

    def add_json_endpoint(self, path: str, json_handler: Callable[[dict], Any]) -> None:
        logger.info("Registering Django-Ninja webhook endpoint: %s", path)

        @self.api.post(path)
        def _webhook(request, payload: dict):
            json_handler(payload)
            return {"status": "ok"}
