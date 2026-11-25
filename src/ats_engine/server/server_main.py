"""Author: Alex Zvuluny | Email: alex.639hz@gmail.com"""

import logging
import threading
from typing import TYPE_CHECKING, Any

# Note: IN_CODE_IMPORT from engine.server.server_api import server

try:
    import uvicorn
except ModuleNotFoundError:
    uvicorn = None


from ats_engine.utils import Utils

if TYPE_CHECKING:
    from fastapi import APIRouter, FastAPI

logger = logging.getLogger("[framework]")

HOST = "127.0.0.1"
PORT = 8088


class Server:

    def __init__(self) -> None:
        self.host = HOST
        self.port = PORT
        self.server_thread = Utils.thread_define("server", self._run_server)
        self._lock = threading.Lock()
        self._app: "FastAPI | None" = None
        # routers added before the server starts; included right before uvicorn runs
        self._pending_routers: list[tuple["APIRouter", dict[str, Any]]] = []

    def router_add(self, router: "APIRouter", **include_kwargs: Any) -> None:
        """Add a user APIRouter to the API server.

        include_kwargs are passed to FastAPI.include_router (prefix, tags, dependencies, ...).
        Can be called before or after the server starts.
        """
        with self._lock:
            if self._app is None:
                self._pending_routers.append((router, include_kwargs))
                return
            self._include(self._app, router, include_kwargs)
            # routes added at runtime: drop the cached /docs schema so it is rebuilt
            self._app.openapi_schema = None

    @staticmethod
    def _include(app: "FastAPI", router: "APIRouter", include_kwargs: dict[str, Any]):
        app.include_router(router, **include_kwargs)
        prefix = include_kwargs.get("prefix", "")
        paths = [getattr(r, "path", "?") for r in router.routes]
        logger.info(f"API router added: prefix='{prefix}' routes={paths}")

    def _run_server(self):
        if uvicorn is None:
            logger.warning("uvicorn is not installed; API server was not started")
            return

        from ats_engine.server.server_api import server

        with self._lock:
            for router, include_kwargs in self._pending_routers:
                self._include(server, router, include_kwargs)
            self._pending_routers.clear()
            self._app = server

        # log_config=None: keep uvicorn from installing its own handlers, so its logs
        # propagate to the root QueueHandler set up in ats_engine.logger
        uvicorn.run(server, host=HOST, port=PORT, log_level="info", log_config=None)
        logger.info("API server stopped")

    def run_server(self):
        if self.server_thread.ident is not None:
            logger.info("API server already started (ENGINE_FLAGS start_api_server)")
            return
        self.server_thread.start()
