# Production-grade Python Automation Framework

A Python framework and runtime engine for industrial automation. Build highly configurable automation from well-organized procedures and steps, with plug-and-play drivers and APIs. The runtime engine supports programmable logic, executes on a single-threaded architecture, and includes a built-in API server for system connectivity.

## Installation

```bash
pip install .            # regular install
pip install -e .         # editable install for development
pip install -e .[dev]    # plus pytest tooling
```

The import name is `ats_engine`:

```python
from ats_engine.framework import framework
from ats_engine.procedure_builder import ProcedureBuilder
from ats_engine.types import StepInterface
from ats_engine.utils import Utils
```

See [examples/main.py](examples/main.py) and [examples/example.py](examples/example.py) for a full project.