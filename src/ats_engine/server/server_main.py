"""Author: Alex Zvuluny | Email: alex.639hz@gmail.com"""

import logging

# Note: IN_CODE_IMPORT from engine.server.server_api import server

try:
    import uvicorn
except ModuleNotFoundError:
    uvicorn = None


from ats_engine.utils import Utils

logger = logging.getLogger("[framework]")

HOST = "127.0.0.1"
PORT = 8088


class Server:
    pass

    def __init__(self) -> None:
        self.host = HOST
        self.port = PORT
        self.server_thread = Utils.thread_define("server", self._run_server)

    def _run_server(self):
        if uvicorn is None:
            logger.warning("uvicorn is not installed; API server was not started")
            return

        from ats_engine.server.server_api import server

        # log_config=None: keep uvicorn from installing its own handlers, so its logs
        # propagate to the root QueueHandler set up in ats_engine.logger
        uvicorn.run(server, host=HOST, port=PORT, log_level="info", log_config=None)
        logger.info("API server stopped")

    def run_server(self):
        self.server_thread.start()
