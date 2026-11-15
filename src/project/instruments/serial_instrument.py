import time
from typing import cast

import pyvisa
from pyvisa.resources import MessageBasedResource

DEF_SERIAL_RESPONSE_DELAY_SECONDS = 1
DEF_SERIAL_PORT_PREFIX = "ASRL"
DEF_SERIAL_PORT_INDEX = 0
DEF_TERMINATION_NEWLINE = "\n"


class InstrumentSerial:
    def __init__(self):
        resource_manager = pyvisa.ResourceManager()
        ports = [
            res
            for res in resource_manager.list_resources()
            if res.startswith(DEF_SERIAL_PORT_PREFIX)
        ]
        if not ports:
            raise Exception("No COM ports available")

        self.port = ports[DEF_SERIAL_PORT_INDEX]
        self.connection = cast(
            MessageBasedResource, resource_manager.open_resource(self.port)
        )
        self.connection.read_termination = DEF_TERMINATION_NEWLINE
        self.connection.write_termination = DEF_TERMINATION_NEWLINE

    def send_and_read(self, cmd: str) -> str:
        """Write a string over the pyvisa connection, wait 1 second, then read the reply."""
        self.connection.write(cmd)
        time.sleep(DEF_SERIAL_RESPONSE_DELAY_SECONDS)
        return self.connection.read()
