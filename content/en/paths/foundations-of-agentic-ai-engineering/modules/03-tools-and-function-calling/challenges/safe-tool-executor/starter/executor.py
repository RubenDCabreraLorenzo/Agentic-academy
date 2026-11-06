"""Safe execution of model-proposed tool calls."""

from dataclasses import dataclass
from typing import Any


@dataclass
class Outcome:
    ok: bool
    value: Any


def close_ticket_schema() -> dict:
    raise NotImplementedError("implement close_ticket_schema")


class ToolExecutor:
    def __init__(self, tools, gate):
        self.tools = tools  # {name: (FakeTool, schema)}
        self.gate = gate

    def execute(self, call) -> Outcome:
        raise NotImplementedError("implement execute")
