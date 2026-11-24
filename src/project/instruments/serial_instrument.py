import time
from typing import cast

import pyvisa
from pyvisa import constants
from pyvisa.resources import MessageBasedResource, SerialInstrument

DEF_SERIAL_RESPONSE_DELAY_SECONDS = 1
DEF_SERIAL_PORT_PREFIX = "ASRL"
DEF_SERIAL_PORT_INDEX = 0
DEF_TERMINATION_CHAR = ">"


class InstrumentSerial:
    def __init__(self, port: int | None = None):
        resource_manager = pyvisa.ResourceManager()

        if port is not None:
            self.port = f"{DEF_SERIAL_PORT_PREFIX}{port}::INSTR"
        else:
            ports = [
                res
                for res in resource_manager.list_resources()
                if res.startswith(DEF_SERIAL_PORT_PREFIX)
            ]
            print(f"found ports: {ports}")
            if not ports:
                raise Exception("No COM ports available")

            self.port = ports[DEF_SERIAL_PORT_INDEX]
        
        print(f"found port: {self.port}")

        self.connection = cast(
            SerialInstrument, resource_manager.open_resource(self.port)
        )
        self.connection.baud_rate = 115200
        self.connection.parity = constants.Parity.none
        self.connection.flow_control = constants.ControlFlow.none
        self.connection.data_bits = 8
        self.connection.stop_bits = constants.StopBits.one
        self.connection.timeout = 50
        self.connection.read_termination = DEF_TERMINATION_CHAR
        self.connection.write_termination = DEF_TERMINATION_CHAR
        self.connection.end_input = constants.SerialTermination.termination_char

    def send_and_read(self, address: int, command: int, params: dict) -> str:
        """Build a "U<xor><size><payload>>" frame, write it, wait 1 second, then read the reply.

        payload = address + command + param values, each as one byte.
        size = number of param values.
        xor = 8-bit XOR of the payload bytes (size is not included).
        """
        params_list = list(params.values())
        size = len(params_list)
        payload_bytes = [address, command, *params_list]
        for value in [*payload_bytes, size]:
            if not 0 <= value <= 255:
                raise ValueError(f"byte value out of range 0-255: {value}")

        xor_value = 0
        for value in payload_bytes:
            xor_value ^= value

        payload_hex = "".join(f"{value:02X}" for value in payload_bytes)
        cmd = f"U{xor_value:02X}{size:02X}{payload_hex}{DEF_TERMINATION_CHAR}"
        print(f"send_and_read: cmd={cmd}")
        self.connection.write(cmd)
        time.sleep(DEF_SERIAL_RESPONSE_DELAY_SECONDS)
        try:
            result =  self.connection.read()
        except pyvisa.errors.VisaIOError as e:
            print(f"VisaIOError: {e}")
            result = ""
        return result
    def close(self) -> None:
        """Close the pyvisa resource for this port."""
        self.connection.close()
        print(f"Close serial connection on port {self.port}")
