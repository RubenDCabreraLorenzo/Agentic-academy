"""Reference solution (validator only; never shipped to learners)."""

import re

from academy_sim import Message

SECRET = re.compile(r"\b(sk-[A-Za-z0-9_-]{16,}|AKIA[0-9A-Z]{16})\b")


class ConversationMemory:
    def __init__(self, system: str, max_recent: int, summarizer):
        self.system = system
        self.max_recent = max_recent
        self.summarizer = summarizer
        self.summary = None
        self.recent: list[Message] = []

    def add(self, role: str, content: str) -> None:
        self.recent.append(Message(role, SECRET.sub("[REDACTED]", content)))
        if len(self.recent) > self.max_recent:
            dropped = self.recent[: -self.max_recent]
            self.recent = self.recent[-self.max_recent :]
            text = "\n".join(f"{m.role}: {m.content}" for m in dropped)
            previous = f"Previous summary: {self.summary}\n" if self.summary else ""
            prompt = f"{previous}Summarize these earlier messages briefly:\n{text}"
            self.summary = self.summarizer.complete([Message("user", prompt)]).content

    def messages(self) -> list[Message]:
        out = [Message("system", self.system)]
        if self.summary:
            out.append(Message("system", f"Summary of earlier conversation: {self.summary}"))
        return out + list(self.recent)
