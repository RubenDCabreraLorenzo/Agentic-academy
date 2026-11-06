---
id: what-to-keep
version: 1.0.0
lang: en
last_reviewed: 2026-11-06
title: Deciding what to keep
---

## Working state versus memory {#state-vs-memory}

- **Working state**: what the current task needs — the current step, collected facts, the plan.
  Keep it explicit in code (a dict or an object), not only implicit in the conversation.
- **Long-term memory**: facts worth reusing across sessions. Persist only what a future task will
  actually need, with an expiry, and make it inspectable and deletable.

## Data minimization {#minimize}

Conversations often contain secrets and personal data pasted by users: API keys, passwords, emails.
Storing them in memory spreads them into logs, summaries and later prompts. Redact before storing.

```python title="redact.py"
import re

SECRET = re.compile(r"\b(sk-[A-Za-z0-9_-]{16,}|AKIA[0-9A-Z]{16})\b")

def redact(text: str) -> str:
    return SECRET.sub("[REDACTED]", text)
```

:::vendor{name="Model providers"}
Some providers offer server-side conversation state or memory features. Check what they store,
where, and for how long before using them for personal or confidential data.
:::
