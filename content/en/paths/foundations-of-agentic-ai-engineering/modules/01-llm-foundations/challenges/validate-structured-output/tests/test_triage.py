"""Tests for extract_ticket. The model is scripted, so no real model is ever called."""

import json

import pytest
from academy_sim import ScriptedModel

from triage import ExtractionError, Ticket, extract_ticket

EMAIL = "Hi, the checkout page has crashed for every customer since 9am. Please help!"
VALID = json.dumps({"priority": "high", "category": "outage", "summary": "Checkout is down"})


def test_valid_response_becomes_ticket():
    model = ScriptedModel([VALID])
    ticket = extract_ticket(model, EMAIL)
    assert ticket == Ticket("high", "outage", "Checkout is down")
    assert model.call_count == 1
    first_call = model.calls[0]
    assert any(m.role == "user" and EMAIL in m.content for m in first_call), "send the email as a user message"


def test_invalid_response_is_retried_with_feedback():
    model = ScriptedModel(["Sure! The priority is high.", VALID])
    ticket = extract_ticket(model, EMAIL)
    assert ticket.priority == "high"
    assert model.call_count == 2, "retry exactly once after an invalid response"
    retry_messages = model.calls[1]
    assert retry_messages[-1].role == "user"
    assert "invalid" in retry_messages[-1].content.lower(), "tell the model its answer was invalid"


def test_unknown_priority_is_rejected():
    bad = json.dumps({"priority": "urgent!!", "category": "outage", "summary": "Down"})
    model = ScriptedModel([bad, VALID])
    assert extract_ticket(model, EMAIL).priority == "high"
    assert model.call_count == 2


def test_two_invalid_responses_raise_and_stop():
    model = ScriptedModel(["not json", json.dumps({"priority": "high"}), VALID])
    with pytest.raises(ExtractionError):
        extract_ticket(model, EMAIL)
    assert model.call_count == 2, "never call the model more than twice"
