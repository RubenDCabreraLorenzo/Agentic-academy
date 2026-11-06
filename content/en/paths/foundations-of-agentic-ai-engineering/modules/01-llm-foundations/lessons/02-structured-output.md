---
id: structured-output
version: 1.0.0
lang: en
last_reviewed: 2026-11-06
title: Structured output you can trust
---

Agents connect models to code. Code needs data with a known shape: a priority from a fixed set, an
id that exists, a number in range. Free text is fine for people; programs need **structured
output**.

## Why ask for structure {#why-structure}

When a model's output drives the next step — calling a tool, routing a ticket, updating a record —
ambiguity becomes a bug. Asking for a precise structure (usually JSON that follows a schema) gives
you something you can check mechanically.

A good request for structured output:

- states the exact fields, their types and allowed values;
- explains what to do when information is missing (for example `null` instead of guessing);
- asks for **only** the structure, with no surrounding prose.

## Validate before you use it {#validate}

A model can return syntactically invalid JSON, an unexpected field, or a value outside the allowed
set. Treat model output exactly like input from an external system: **parse, validate, and only
then use it.**

```python title="validate_ticket.py"
import json
from dataclasses import dataclass

PRIORITIES = {"low", "medium", "high"}

@dataclass(frozen=True)
class Ticket:
    priority: str
    category: str
    summary: str

class InvalidOutput(ValueError):
    pass

def parse_ticket(raw: str) -> Ticket:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise InvalidOutput(f"not valid JSON: {exc.msg}") from exc
    if not isinstance(data, dict):
        raise InvalidOutput("expected a JSON object")
    missing = {"priority", "category", "summary"} - data.keys()
    if missing:
        raise InvalidOutput(f"missing fields: {sorted(missing)}")
    if data["priority"] not in PRIORITIES:
        raise InvalidOutput(f"priority must be one of {sorted(PRIORITIES)}")
    return Ticket(str(data["priority"]), str(data["category"]), str(data["summary"]))
```

:::maturity{level="established"}
Validating model output against an explicit schema before acting on it is established engineering
practice, independent of the model or provider.
:::

## Retry with feedback, then fail safely {#retry}

When validation fails, a **bounded** retry that tells the model what was wrong often succeeds: send
the validation error back as a new message and ask for corrected output. Bound the number of
attempts and, if it still fails, **fail in a controlled way** — raise a clear error, ask a human,
or fall back to a safe default. Never loop until it works: that hides problems and can run up cost
without limit.

```mermaid alt="Structured output flow: ask the model, validate the response; if valid, use it; if invalid and attempts remain, send the validation error back to the model and try again; if attempts are exhausted, fail safely."
flowchart TD
  A[Ask model for JSON] --> V{Valid?}
  V -->|yes| U[Use the data]
  V -->|no, attempts left| F[Send validation error back]
  F --> A
  V -->|no, attempts exhausted| X[Fail safely: raise or escalate]
```

:::maturity{level="emerging"}
Constrained decoding — where the runtime only allows tokens that keep the output valid against a
schema — reduces but does not remove the need for validation: values can still be wrong while being
well-formed.
:::

:::vendor{name="Model providers"}
Many providers offer a "JSON mode" or schema-constrained output feature. Coverage of schema features
and guarantees differ between providers and model versions; keep your own validation regardless.
:::
