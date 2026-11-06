"""A bounded agent loop and a fixed workflow."""

from dataclasses import dataclass

from academy_sim import Message


@dataclass
class AgentResult:
    answer: str | None
    steps: int
    stopped: str  # "answered" | "step_limit"


def run_agent(model, tools, task, max_steps=5) -> AgentResult:
    raise NotImplementedError("implement run_agent")


def triage_workflow(email, classify, get_template, model) -> str:
    raise NotImplementedError("implement triage_workflow")
