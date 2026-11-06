from academy_sim import FakeTool, ScriptedModel

from agent import run_agent, triage_workflow


def search_tool():
    return FakeTool("search", "read", handler=lambda query: f"facts about {query}")


def test_answers_without_tools():
    model = ScriptedModel(["Paris"])
    result = run_agent(model, {"search": search_tool()}, "Capital of France?")
    assert (result.answer, result.steps, result.stopped) == ("Paris", 1, "answered")
    assert [s.name for s in model.tools_seen[0]] == ["search"]


def test_runs_tool_and_feeds_result():
    tool = search_tool()
    model = ScriptedModel([{"tool_calls": [{"id": "c1", "name": "search", "arguments": {"query": "Lisbon"}}]}, "About 545,000"])
    result = run_agent(model, {"search": tool}, "Population of Lisbon?")
    assert result.answer == "About 545,000" and result.steps == 2
    assert tool.calls == [{"query": "Lisbon"}]
    tool_messages = [m for m in model.calls[1] if m.role == "tool"]
    assert len(tool_messages) == 1 and tool_messages[0].tool_call_id == "c1"
    assert "facts about Lisbon" in tool_messages[0].content


def test_unknown_tool_is_reported():
    model = ScriptedModel([{"tool_calls": [{"id": "c1", "name": "delete_everything", "arguments": {}}]}, "Sorry, I cannot do that."])
    result = run_agent(model, {"search": search_tool()}, "Do something")
    assert result.stopped == "answered"
    assert any(m.role == "tool" and "unknown tool" in m.content for m in model.calls[1])


def test_stops_at_step_limit():
    looping = {"tool_calls": [{"id": "c", "name": "search", "arguments": {"query": "again"}}]}
    model = ScriptedModel([looping] * 10)
    result = run_agent(model, {"search": search_tool()}, "Loop forever", max_steps=3)
    assert (result.answer, result.stopped) == (None, "step_limit")
    assert model.call_count == 3


def test_workflow_fixed_sequence():
    order = []
    classify = FakeTool("classify", "read", handler=lambda text: order.append("classify") or "billing")
    get_template = FakeTool("get_template", "read", handler=lambda category: order.append(f"template:{category}") or "Hi {name}")
    model = ScriptedModel(["Hi Ana, sorry about the double charge."])
    reply = triage_workflow("I was charged twice", classify, get_template, model)
    assert reply == "Hi Ana, sorry about the double charge."
    assert order == ["classify", "template:billing"]
    assert model.call_count == 1
