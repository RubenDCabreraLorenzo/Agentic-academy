"""Bounded conversation memory with summaries and redaction."""

import re

from academy_sim import Message


class ConversationMemory:
    def __init__(self, system: str, max_recent: int, summarizer):
        self.system = system
        self.max_recent = max_recent
        self.summarizer = summarizer
        self.summary = None
        self.recent: list[Message] = []

    def add(self, role: str, content: str) -> None:
        raise NotImplementedError("implement add")

    def messages(self) -> list[Message]:
        raise NotImplementedError("implement messages")
