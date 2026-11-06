"""Support ticket triage with validated structured output."""

from dataclasses import dataclass

from academy_sim import Message, ModelClient

PRIORITIES = {"low", "medium", "high"}

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


def extract_ticket(model: ModelClient, email_text: str) -> Ticket:
    """Ask the model for a ticket, validate it, retry once with feedback, then fail safely."""
    messages = [Message("system", SYSTEM_PROMPT), Message("user", email_text)]
    response = model.complete(messages)
    # TODO: parse and validate response.content, retry once with feedback, raise ExtractionError.
    raise NotImplementedError("implement extract_ticket")
