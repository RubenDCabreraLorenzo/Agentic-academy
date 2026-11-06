---
id: agent-loop
version: 1.0.0
lang: en
last_reviewed: 2026-11-06
title: The agent loop
---

An **agent** is a system in which a model decides, step by step, which actions to take — usually
by calling tools — and observes their results before deciding again. The model does not execute
anything itself: **your code** runs the tools and feeds the results back.

## The loop {#the-loop}

```mermaid alt="Agent loop: code sends messages and tool definitions to the model; if the model requests tool calls, code validates and executes them, appends the results and calls the model again; if the model returns an answer or the step limit is reached, the loop stops."
flowchart TD
  S[Messages + tool definitions] --> M[Model call]
  M --> D{Tool calls requested?}
  D -->|yes| X[Code validates and runs tools]
  X --> R[Append tool results]
  R --> L{Step limit reached?}
  L -->|no| M
  L -->|yes| STOP[Stop: step limit]
  D -->|no| A[Final answer]
```

Each iteration appends the model's request and the tool results to the conversation, so the next
call sees what happened. The loop ends when the model answers without requesting tools.

```python title="loop.py" annotate
from academy_sim import Message

def run(model, tools, task, max_steps=5):
    messages = [Message("user", task)]
    for step in range(1, max_steps + 1):  # note: a hard bound — never loop "until done"
        response = model.complete(messages, [t.spec for t in tools.values()])
        if not response.tool_calls:
            return response.content  # note: no tool calls means the model has answered
        messages.append(Message("assistant", response.content or "", tool_calls=response.tool_calls))
        for call in response.tool_calls:
            tool = tools.get(call.name)
            result = tool(**call.arguments) if tool else f"unknown tool {call.name}"
            messages.append(Message("tool", str(result), tool_call_id=call.id, name=call.name))
    return None  # note: the caller decides what a step-limit stop means
```

:::maturity{level="established"}
The tool-calling loop with explicit stop conditions is the established core of agent runtimes.
:::

## Stopping conditions {#stopping}

An agent without a hard limit can loop forever, repeat the same call, or burn through budget.
Always combine:

- a **step limit** (and in production, time and cost budgets);
- a clear **success condition** (an answer, or a specific tool such as `submit_answer`);
- handling for **unknown tools and tool errors**: report them back to the model as tool results
  instead of crashing, so it can recover.

:::vendor{name="Model providers"}
Providers expose tool calling with different message formats (for example how tool results are
identified). The loop is the same; isolate the format behind a small client interface such as the
`ModelClient` protocol used in this course.
:::
