"""Reference solution (validator only; never shipped to learners)."""

from dataclasses import dataclass

from academy_sim import Message


@dataclass
class AgentResult:
    answer: str | None
    steps: int
    stopped: str


def run_agent(model, tools, task, max_steps=5) -> AgentResult:
    messages = [Message("user", task)]
    specs = [t.spec for t in tools.values()]
    for step in range(1, max_steps + 1):
        response = model.complete(messages, specs)
        if not response.tool_calls:
            return AgentResult(response.content, step, "answered")
        messages.append(Message("assistant", response.content or "", tool_calls=response.tool_calls))
        for call in response.tool_calls:
            tool = tools.get(call.name)
            if tool is None:
                content = f"error: unknown tool {call.name}"
            else:
                try:
                    content = str(tool(**call.arguments))
                except Exception as exc:  # report tool errors back to the model
                    content = f"error: {exc}"
            messages.append(Message("tool", content, tool_call_id=call.id, name=call.name))
    return AgentResult(None, max_steps, "step_limit")


def triage_workflow(email, classify, get_template, model) -> str:
    category = classify(text=email)
    template = get_template(category=category)
    prompt = f"Fill this template for the email below.\nTemplate: {template}\nEmail: {email}"
    return model.complete([Message("user", prompt)]).content
