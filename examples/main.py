"""Author: Alex Zvuluny | Email: alex.639hz@gmail.com"""

from example import ProjectExample
from ats_engine.framework import framework

config = {
    "name": "Alex",
    "description": "Example project",
}


project = ProjectExample(config)

try:

    framework.wait_shutdown()

except KeyboardInterrupt:
    framework.call_shutdown(" ----- KeyboardInterrupt ----- ")
except Exception as err:
    msg = f" ----- Main EXCEPTION: Error: {err}"
    print(f"main error: {msg}")
