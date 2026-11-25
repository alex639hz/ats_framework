"""Author: Alex Zvuluny | Email: alex.639hz@gmail.com"""

from project_example import ProjectExample
from ats_engine.framework import framework

project = ProjectExample()

# add project routers to the API server, then start it
framework.api_router_add(project.router, prefix="/example", tags=["example"])
framework.start_api_server()

try:
    framework.wait_shutdown()

except KeyboardInterrupt:
    framework.call_shutdown(" ----- KeyboardInterrupt ----- ")
except Exception as err:
    msg = f" ----- Main EXCEPTION: Error: {err}"
    print(f"main error: {msg}")
