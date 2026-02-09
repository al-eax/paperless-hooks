from abc import ABC, abstractmethod
from typing import Any, Callable


class BackendInterface(ABC):
    """Abstract base class for HTTP backends (FastAPI, Flask, Django-Ninja, ...)
    PaperlessHooks only depends on this interface, so swapping frameworks
    is as simple as providing a different concrete implementation.
    """

    @abstractmethod
    def add_json_endpoint(self, path: str, json_handler: Callable[[dict], Any]) -> None:
        """Register a POST endpoint for paperless-ngx at *path* that parses a JSON body and
        passes the resulting dict to *json_handler*.
        """
        ...
