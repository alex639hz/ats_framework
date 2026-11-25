"""Author: Alex Zvuluny | Email: alex.639hz@gmail.com"""

import logging
import threading
from fastapi import FastAPI, Request, HTTPException
from ats_engine.constants import DEF_OK
from ats_engine.server.routes.routes_general import routerGeneral
from ats_engine.framework import framework

# import server_utils as server_utils

logger = logging.getLogger("[framework]")

server = FastAPI()


@server.post("/start/{proc_name}")
def start(proc_name: str):
    """Start a procedure by its label, e.g. POST /start/dut_test."""
    try:
        procedure = framework.procedure_get_by_label(proc_name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Procedure '{proc_name}' not found")

    # queue the start on the engine thread (the engine is single-threaded)
    procedure.push_start_request()
    logger.info(f"start requested via API: {proc_name}")
    return {"status": DEF_OK, "procedure": proc_name}


@server.post("/stop/{proc_name}")
def stop(proc_name: str):
    """Stop a procedure by its label, e.g. POST /stop/dut_test. Resume with /start."""
    try:
        procedure = framework.procedure_get_by_label(proc_name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Procedure '{proc_name}' not found")

    # queue the stop on the engine thread (the engine is single-threaded)
    procedure.push_stop_request()
    logger.info(f"stop requested via API: {proc_name}")
    return {"status": DEF_OK, "procedure": proc_name}


@server.get("/test")
def snapshot():
    threads = threading.enumerate()

    logger.info(f"Active threads: {len(threads)}")
    for t in threads:
        logger.info(f"Name: {t.name}, Alive: {t.is_alive()}, Daemon: {t.daemon}")

    return "test ok"


@server.get("/exit")
def exit():
    logger.info("shutdown requested via API")
    framework.call_shutdown()

    return "test ok"


server.include_router(routerGeneral)

# Station Management:


@server.post("/register")
def register(server_id: str):
    """register Set the server ID in the framework context."""
    if not server_id or not isinstance(server_id, str):
        raise HTTPException(
            status_code=400, detail="server_id must be a non-empty string"
        )

    try:
        framework.context.attribute_set("server_id", server_id)
        return {"status": "success", "server_id": server_id}
    except Exception as e:
        logger.error(f"Failed to set server_id: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to set server_id: {str(e)}"
        )


# TODO
@server.get("/config")
def get_config(server_id):
    """register Set the server ID in the framework context."""
    if not server_id or not isinstance(server_id, str):
        raise HTTPException(
            status_code=400, detail="server_id must be a non-empty string"
        )

    try:
        framework.context.attribute_set("server_id", server_id)
        return {"status": "success", "server_id": server_id}
    except Exception as e:
        logger.error(f"Failed to set server_id: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to set server_id: {str(e)}"
        )


# TODO
@server.get("/proc/{id}")
def get_procedure(id):
    if not id or not isinstance(id, str):
        raise HTTPException(
            status_code=400, detail="id must be a non-empty numeric string"
        )

    try:
        procedure_id = int(id)
        max = len(framework._procedure_list)
        if procedure_id < 0 or procedure_id > max:
            raise ValueError(f"id must be 0..{max}")
        procedure = framework._procedure_list[procedure_id]
        return {"status": "success", "procedure": procedure}
    except ValueError:
        raise HTTPException(
            status_code=400, detail="id must be a valid non-negative integer"
        )
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Procedure {id} not found")
    except Exception as e:
        logger.error(f"Failed to get procedure {id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get procedure: {str(e)}"
        )
