---
id: limitations
version: 1.0.0
lang: en
last_reviewed: 2026-11-06
title: Where models fail and what to do about it
---

Agents amplify model behavior: a single wrong output can trigger tool calls with real effects.
Knowing the typical failure modes lets you design checks in the right places instead of hoping the
model behaves.

## Hallucination {#hallucination}

A model can produce fluent, confident statements that are false or unsupported: invented citations,
non-existent API parameters, wrong numbers. This follows from next-token prediction — the model
generates plausible continuations, and plausibility is not truth.

Mitigations, from most to least reliable:

1. **Verify in code** anything that can be verified: does the order id exist, does the function
   exist, is the number within range.
2. **Ground** the model in supplied sources (retrieval, tool results) and ask it to answer only from
   them, citing which source supports each claim (Module 5 and the RAG path go deeper).
3. **Allow "I don't know"** explicitly in the instructions and in the output schema, so the model is
   not forced to invent a value.

:::maturity{level="experimental"}
Asking a model to check its own answer, or sampling several answers and comparing them, can reduce
some errors, but results vary widely by task. Treat it as an experiment to measure, not a guarantee.
:::

## Knowledge cut-off {#cutoff}

Training data ends at some date. A model does not know about later events, library versions or
policy changes unless you provide them in context. When freshness matters, fetch current
information with a tool and pass it in.

## Context limits {#context-limits}

Output quality degrades when the context is overloaded or when key instructions compete with large
amounts of irrelevant text. Keep prompts focused, put the most important constraints where they are
clearly stated, and prefer passing **only the relevant parts** of large documents.

## Non-determinism and prompt sensitivity {#non-determinism}

Small changes in wording, ordering or sampling can change the output. Do not build logic that relies
on an exact phrase from the model. Instead:

- ask for structured output and validate it (previous lesson);
- write **tests with scripted model responses** for your agent code, so you can check your logic
  deterministically — you will do this in every challenge of this path;
- evaluate real model behavior separately, on representative examples (Module 5).

```python title="no_magic_strings.py"
# Fragile: depends on the model saying exactly "APPROVED".
def is_approved_fragile(model_text: str) -> bool:
    return model_text.strip() == "APPROVED"

# Robust: the model returns JSON; the code validates an explicit field.
import json

def is_approved(model_json: str) -> bool:
    data = json.loads(model_json)
    decision = data.get("decision")
    if decision not in {"approved", "rejected", "needs_review"}:
        raise ValueError("unexpected decision value")
    return decision == "approved"
```
