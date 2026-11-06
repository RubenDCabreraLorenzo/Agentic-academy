"""Reference solution (validator only; never shipped to learners)."""

from dataclasses import dataclass
from typing import Any

TYPES = {"string": str, "integer": int}


@dataclass
class Outcome:
    ok: bool
    value: Any


def close_ticket_schema() -> dict:
    return {
        "type": "object",
        "properties": {"ticket_id": {"type": "string", "description": "Ticket id such as 'T-1042'."}},
        "required": ["ticket_id"],
        "additionalProperties": False,
    }


def validate(arguments: dict, schema: dict) -> str | None:
    props = schema.get("properties", {})
    for name in schema.get("required", []):
        if name not in arguments:
            return f"missing {name}"
    for name, value in arguments.items():
        if name not in props:
            if schema.get("additionalProperties", True) is False:
                return f"unexpected argument {name}"
            continue
        expected = TYPES.get(props[name].get("type"))
        if expected is not None and (not isinstance(value, expected) or isinstance(value, bool)):
            return f"{name} must be {props[name]['type']}"
    return None


class ToolExecutor:
    def __init__(self, tools, gate):
        self.tools = tools
        self.gate = gate

    def execute(self, call) -> Outcome:
        if call.name not in self.tools:
            return Outcome(False, f"unknown tool {call.name}")
        tool, schema = self.tools[call.name]
        error = validate(call.arguments, schema)
        if error:
            return Outcome(False, f"invalid arguments: {error}")
        approved = False
        if tool.permission == "destructive":
            if not self.gate.request(call.name, call.arguments):
                return Outcome(False, "rejected by human")
            approved = True
        try:
            return Outcome(True, tool(approved=approved, **call.arguments))
        except Exception as exc:
            return Outcome(False, f"tool error: {exc}")
