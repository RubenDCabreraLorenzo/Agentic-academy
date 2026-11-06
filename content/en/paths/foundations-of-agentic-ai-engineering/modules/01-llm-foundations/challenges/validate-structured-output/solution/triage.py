"""Reference solution (validator only; never shipped to learners)."""

import json
from dataclasses import dataclass

from academy_sim import Message, ModelClient

PRIORITIES = {"low", "medium", "high"}
REQUIRED = ("priority", "category", "summary")

SYSTEM_PROMPT = (
    "You triage support emails. Reply with JSON only, no prose, using exactly these fields: "
    '{"priority": "low" | "medium" | "high", "category": string, "summary": string}.'
)


@dataclass(frozen=True)
class Ticket:
    priority: str
    category: str
    summary: str


class ExtractionError(Exception):
    """The model did not produce a valid ticket after one retry."""


def parse_ticket(raw: str | None) -> Ticket:
    try:
        data = json.loads(raw or "")
    except json.JSONDecodeError as exc:
        raise ValueError(f"not valid JSON ({exc.msg})") from exc
    if not isinstance(data, dict):
        raise ValueError("expected a JSON object")
    missing = [f for f in REQUIRED if f not in data]
    if missing:
        raise ValueError(f"missing fields: {', '.join(missing)}")
    if data["priority"] not in PRIORITIES:
        raise ValueError(f"priority must be one of {sorted(PRIORITIES)}")
    return Ticket(str(data["priority"]), str(data["category"]), str(data["summary"]))


def extract_ticket(model: ModelClient, email_text: str) -> Ticket:
    messages = [Message("system", SYSTEM_PROMPT), Message("user", email_text)]
    response = model.complete(messages)
    try:
        return parse_ticket(response.content)
    except ValueError as error:
        messages += [
            Message("assistant", response.content or ""),
            Message("user", f"Your previous answer was invalid: {error}. Reply with corrected JSON only."),
        ]
    retry = model.complete(messages)
    try:
        return parse_ticket(retry.content)
    except ValueError as error:
        raise ExtractionError(str(error)) from error
