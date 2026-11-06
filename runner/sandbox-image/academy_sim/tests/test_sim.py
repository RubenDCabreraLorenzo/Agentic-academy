import pytest

from academy_sim import (
    ApprovalGate,
    FakeTool,
    Message,
    ModelClient,
    ModelResponse,
    PermissionDeniedError,
    ScriptedModel,
    ScriptExhaustedError,
    ToolCall,
    TraceRecorder,
    assert_approval_requested,
    assert_tool_called,
    assert_tool_not_called,
)


def test_scripted_model_returns_turns_in_order_and_records_calls():
    model = ScriptedModel(["hello", {"tool_calls": [{"name": "search", "arguments": {"q": "x"}}]}])
    assert isinstance(model, ModelClient)
    first = model.complete([Message("user", "hi")])
    assert first.content == "hello" and not first.wants_tools
    second = model.complete([Message("user", "find x")])
    assert second.tool_calls == (ToolCall("call-0", "search", {"q": "x"}),)
    assert model.call_count == 2
    assert model.calls[0][0].content == "hi"


def test_scripted_model_raises_when_exhausted():
    model = ScriptedModel([ModelResponse(content="only")])
    model.complete([])
    with pytest.raises(ScriptExhaustedError):
        model.complete([])


def test_scripted_model_callable_turn_sees_messages():
    model = ScriptedModel([lambda msgs: f"echo {msgs[-1].content}"])
    assert model.complete([Message("user", "ping")]).content == "echo ping"


def test_fake_tool_records_and_enforces_destructive_permission():
    search = FakeTool("search", "read", handler=lambda q: [q])
    assert search(q="agents") == ["agents"]
    assert search.calls == [{"q": "agents"}]
    delete = FakeTool("delete_ticket", "destructive", handler=lambda ticket_id: "deleted")
    with pytest.raises(PermissionDeniedError):
        delete(ticket_id="T-1")
    assert delete(approved=True, ticket_id="T-1") == "deleted"
    with pytest.raises(ValueError):
        FakeTool("x", "admin")  # type: ignore[arg-type]


def test_approval_gate_consumes_decisions():
    gate = ApprovalGate([False, True])
    assert gate.request("delete_ticket", {"ticket_id": "1"}) is False
    assert gate.request("delete_ticket") is True
    assert_approval_requested(gate, "delete_ticket")
    with pytest.raises(AssertionError):
        gate.request("delete_ticket")


def test_trace_recorder_and_assertions():
    trace = TraceRecorder()
    trace.event("run_started")
    trace.tool_call("search", {"q": "x"}, result=["r"])
    trace.state_transition({"step": 0}, {"step": 1})
    assert trace.events == ["run_started"]
    assert trace.of_kind("state_transition")[0]["changed_keys"] == ["step"]
    assert_tool_called(trace, "search", q="x")
    assert_tool_not_called(trace, "delete")
    with pytest.raises(AssertionError):
        assert_tool_called(trace, "search", q="y")
    with pytest.raises(AssertionError):
        assert_tool_called(trace, "delete")
