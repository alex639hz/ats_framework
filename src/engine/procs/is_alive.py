"""Heartbeat procedure: logs an 'alive' message at a fixed interval while the engine runs."""

from engine.procedure import Procedure
from engine.procedure_builder import ProcedureBuilder
from engine.types import StepInterface
from engine.utils import Utils

PROCEDURE_LABEL = "is_alive"
HEARTBEAT_SECONDS = 1.0


def runtime_heartbeat(step_interface: StepInterface):
    procedure, _ = Utils.extract_step_interface(step_interface)
    count = procedure.context.attribute_get("alive_count", 0) + 1
    procedure.context.attribute_set("alive_count", count)

    # repeat this step forever, once per HEARTBEAT_SECONDS
    procedure.nextstate_sleep_and_repeat(HEARTBEAT_SECONDS)
    return f"alive: {count}"


def build_is_alive_procedure() -> Procedure:
    builder = ProcedureBuilder(PROCEDURE_LABEL)
    builder.step_call(runtime_heartbeat, label="heartbeat")
    return builder.generate_procedure()
