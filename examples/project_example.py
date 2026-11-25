"""Author: Alex Zvuluny | Email: alex.639hz@gmail.com"""

import logging

from fastapi import APIRouter

# from engine.framework import framework
from ats_engine.constants import *
from ats_engine.framework import framework
from ats_engine.procedure_builder import ProcedureBuilder
from ats_engine.types import StepInterface
from ats_engine.utils import Utils

logger = logging.getLogger("[user]")


class ProjectExample:

    def __init__(self):
        self.config = {
            "name": "Alex",
            "description": "Example project",
        }
        self.router = self.build_router()

        dut_test = self.build_dut_test()
        final_procedure = dut_test

        final_procedure.start()
        framework.procedure_append(final_procedure)

    def build_router(self) -> APIRouter:
        """Project-specific API routes; registered by main.py via framework.api_router_add."""
        router = APIRouter()

        @router.get("/config")
        def get_config():
            return self.config

        @router.get("/counter")
        def get_counter():
            procedure = framework.procedure_get_by_label("dut_test")
            return {"counter": procedure.context.attribute_get("counter", 0)}

        return router

    def build_dut_test(self):
        dut_flow_build = ProcedureBuilder("dut_test")
        dut_flow_build.step_call(self.runtime_example)
        dut_flow = dut_flow_build.generate_procedure()
        return dut_flow

    def runtime_example(self, step_interface: StepInterface):
        procedure, args = Utils.extract_step_interface(step_interface)
        counter = procedure.context.attribute_get("counter", 0)
        counter = counter + 1
        procedure.context.attribute_set("counter", counter)
        msg = f"counter: {counter}"
        sleep_seconds = 1
        max_count = 5

        operation = ["forever", "count"][0]

        if operation == "forever":
            procedure.nextstate_sleep_and_repeat(sleep_seconds)
        elif operation == "count":
            if counter < max_count:
                procedure.nextstate_sleep_and_repeat(sleep_seconds)
            else:
                msg = f"completed: {counter}"
                procedure.nextstate_exit()

        return msg
