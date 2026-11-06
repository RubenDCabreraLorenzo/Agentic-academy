from academy_sim import ScriptedModel

from memory import ConversationMemory


def test_keeps_system_and_recent():
    mem = ConversationMemory("You are a support agent.", 2, ScriptedModel(["s1", "s2", "s3"]))
    for i in range(4):
        mem.add("user", f"message {i}")
    msgs = mem.messages()
    assert msgs[0].role == "system" and msgs[0].content == "You are a support agent."
    assert [m.content for m in msgs if m.role == "user"] == ["message 2", "message 3"]


def test_summarizes_dropped_messages():
    summarizer = ScriptedModel(["The customer reported a login problem."])
    mem = ConversationMemory("sys", 2, summarizer)
    mem.add("user", "I cannot log in")
    mem.add("assistant", "Which browser?")
    assert summarizer.call_count == 0
    mem.add("user", "Firefox")
    assert summarizer.call_count == 1
    assert "I cannot log in" in summarizer.calls[0][-1].content
    msgs = mem.messages()
    assert msgs[1].role == "system" and msgs[1].content.startswith("Summary of earlier conversation:")
    assert "login problem" in msgs[1].content and len(msgs) == 4


def test_summary_accumulates():
    summarizer = ScriptedModel(["first summary", "second summary"])
    mem = ConversationMemory("sys", 1, summarizer)
    mem.add("user", "a")
    mem.add("user", "b")
    mem.add("user", "c")
    assert summarizer.call_count == 2
    assert "first summary" in summarizer.calls[1][-1].content
    assert "second summary" in mem.messages()[1].content


def test_redacts_secrets():
    # Fake keys are assembled at runtime so the content secret scanner does not flag this file.
    fake_openai_style = "sk-" + "abcdefghijklmnopqrstuvwx"
    fake_aws_style = "AKIA" + "ABCDEFGHIJKLMNOP"
    mem = ConversationMemory("sys", 5, ScriptedModel([]))
    mem.add("user", f"my key is {fake_openai_style} and {fake_aws_style} thanks")
    stored = mem.messages()[-1].content
    assert fake_openai_style not in stored and fake_aws_style not in stored
    assert stored.count("[REDACTED]") == 2
