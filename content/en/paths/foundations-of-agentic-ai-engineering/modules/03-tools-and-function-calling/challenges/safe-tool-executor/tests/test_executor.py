from academy_sim import ApprovalGate, FakeTool, ToolCall

from executor import ToolExecutor, close_ticket_schema

GET_SCHEMA = {"type": "object", "properties": {"ticket_id": {"type": "string"}}, "required": ["ticket_id"], "additionalProperties": False}


def setup(decisions=()):
    get_ticket = FakeTool("get_ticket", "read", handler=lambda ticket_id: {"id": ticket_id})
    close = FakeTool("close_ticket", "destructive", handler=lambda ticket_id: "closed")
    gate = ApprovalGate(decisions)
    executor = ToolExecutor({"get_ticket": (get_ticket, GET_SCHEMA), "close_ticket": (close, close_ticket_schema())}, gate)
    return executor, get_ticket, close, gate


def test_schema_is_strict():
    schema = close_ticket_schema()
    assert schema["type"] == "object"
    assert schema["required"] == ["ticket_id"]
    assert schema["properties"]["ticket_id"]["type"] == "string"
    assert schema["additionalProperties"] is False


def test_invalid_arguments_rejected():
    executor, get_ticket, close, _ = setup()
    for args in ({}, {"ticket_id": 1042}, {"ticket_id": "T-1", "all": True}, {"ticket_id": True}):
        outcome = executor.execute(ToolCall("c", "get_ticket", args))
        assert outcome.ok is False and outcome.value.startswith("invalid arguments"), args
    assert get_ticket.calls == []
    assert executor.execute(ToolCall("c", "get_ticket", {"ticket_id": "T-1"})).value == {"id": "T-1"}


def test_unknown_tool():
    executor, *_ = setup()
    outcome = executor.execute(ToolCall("c", "delete_all", {}))
    assert outcome.ok is False and "unknown tool" in outcome.value


def test_destructive_requires_approval():
    executor, _, close, gate = setup([True])
    outcome = executor.execute(ToolCall("c", "close_ticket", {"ticket_id": "T-1042"}))
    assert outcome.ok is True and outcome.value == "closed"
    assert gate.requests == [("close_ticket", {"ticket_id": "T-1042"})]
    assert close.invocations[0].approved is True


def test_rejection_does_not_run():
    executor, _, close, _ = setup([False])
    outcome = executor.execute(ToolCall("c", "close_ticket", {"ticket_id": "T-1042"}))
    assert (outcome.ok, outcome.value) == (False, "rejected by human")
    assert close.calls == []


def test_tool_errors_are_reported():
    failing = FakeTool("get_ticket", "read", handler=lambda ticket_id: 1 / 0)
    executor = ToolExecutor({"get_ticket": (failing, GET_SCHEMA)}, ApprovalGate([]))
    outcome = executor.execute(ToolCall("c", "get_ticket", {"ticket_id": "T-1"}))
    assert outcome.ok is False and outcome.value.startswith("tool error")
