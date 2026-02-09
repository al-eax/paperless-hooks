import logging
from typing import Any, Callable

from fastapi import BackgroundTasks, FastAPI, Request

from backends.base import BackendInterface

logger = logging.getLogger(__name__)


class FastApiBackend(BackendInterface):

    def __init__(self, app: FastAPI):
        self.app = app

    def add_json_endpoint(self, path: str, json_handler: Callable[[dict], Any]) -> None:
        logger.info("Registering FastAPI webhook endpoint: %s", path)

        @self.app.post(path)
        async def _webhook(request: Request, background_tasks: BackgroundTasks):
            data = await request.json()
            background_tasks.add_task(json_handler, data)
            return {"status": "ok"}
