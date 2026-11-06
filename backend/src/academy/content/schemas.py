"""Pydantic schemas for educational content files (data-model.md §1, contracts/content-schema.md).

These models describe the *authored* files. Cross-file rules (references, ordering, completeness)
live in :mod:`academy.content.validate`.
"""

from __future__ import annotations

import re
from datetime import date
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

ID_PATTERN = r"^[a-z0-9]+(-[a-z0-9]+)*$"
SEMVER_PATTERN = r"^\d+\.\d+\.\d+$"

ContentId = Annotated[str, Field(pattern=ID_PATTERN, min_length=1, max_length=80)]

#: Platform maximums for challenge execution (runner protocol §4).
MAX_WALL_SECONDS = 10
MAX_MEMORY_MB = 256


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Level(StrEnum):
    foundational = "foundational"
    intermediate = "intermediate"
    advanced = "advanced"


class Maturity(StrEnum):
    established = "established"
    emerging = "emerging"
    experimental = "experimental"


class Deprecation(Strict):
    reason: str = Field(min_length=1)
    replacement: str | None = None
    since: date


class Header(Strict):
    """Common header of every content item (content-schema.md "Common header")."""

    id: ContentId
    version: str = Field(pattern=SEMVER_PATTERN)
    lang: str = Field(min_length=2, max_length=16)
    last_reviewed: date
    deprecation: Deprecation | None = None


class Competency(Strict):
    id: ContentId
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    level: Level


class CompetencyCatalog(Strict):
    competencies: list[Competency] = Field(min_length=1)


class EntryPrerequisite(Strict):
    label: str = Field(min_length=1)
    resource_url: HttpUrl


class LearningPath(Header):
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    level: Level
    status: Literal["available", "planned"]
    order: int = Field(ge=0)
    objectives: list[str] = Field(min_length=1)
    entry_prerequisites: list[EntryPrerequisite] = Field(default_factory=list)
    prerequisite_paths: list[ContentId] = Field(default_factory=list)
    competencies: list[ContentId] = Field(default_factory=list)
    estimated_hours: float = Field(gt=0)
    modules: list[ContentId] = Field(default_factory=list)

    @model_validator(mode="after")
    def _available_has_modules(self) -> LearningPath:
        if self.status == "available" and not self.modules:
            raise ValueError("an available path must list at least one module")
        return self


class LearningObjective(Strict):
    id: ContentId
    statement: str = Field(min_length=1)
    competencies: list[ContentId] = Field(min_length=1)


class Reference(Strict):
    title: str = Field(min_length=1)
    url: HttpUrl
    vendor: str | None = None


class Module(Header):
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    order: int = Field(ge=1)
    objectives: list[LearningObjective] = Field(min_length=1)
    prerequisites: list[ContentId] = Field(default_factory=list)
    competencies: list[ContentId] = Field(min_length=1)
    lab_scenarios: list[ContentId] = Field(default_factory=list)
    references: list[Reference] = Field(min_length=1)
    multi_agent: bool = False


class LessonFrontMatter(Header):
    title: str = Field(min_length=1)


class Option(Strict):
    id: ContentId
    text: str = Field(min_length=1)
    explanation: str | None = None


class QuestionType(StrEnum):
    single_choice = "single_choice"
    multiple_choice = "multiple_choice"
    ordering = "ordering"
    matching = "matching"


LESSON_ANCHOR = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*#[a-z0-9]+(-[a-z0-9]+)*$")


class Question(Strict):
    id: ContentId
    type: QuestionType
    prompt: str = Field(min_length=1)
    explanation: str = Field(min_length=1)
    objective_id: ContentId
    lesson_anchor: str
    # single_choice / multiple_choice
    options: list[Option] = Field(default_factory=list)
    correct: list[ContentId] = Field(default_factory=list)
    # ordering: items listed in the correct order (presented shuffled)
    items: list[Option] = Field(default_factory=list)
    # matching
    left: list[Option] = Field(default_factory=list)
    right: list[Option] = Field(default_factory=list)
    pairs: dict[str, str] = Field(default_factory=dict)

    @field_validator("lesson_anchor")
    @classmethod
    def _anchor(cls, value: str) -> str:
        if not LESSON_ANCHOR.match(value):
            raise ValueError("lesson_anchor must be '<lesson-id>#<anchor>'")
        return value

    @model_validator(mode="after")
    def _shape(self) -> Question:
        t = self.type
        if t in (QuestionType.single_choice, QuestionType.multiple_choice):
            if len(self.options) < 2:
                raise ValueError("choice questions need at least 2 options")
            ids = {o.id for o in self.options}
            if not self.correct or not set(self.correct) <= ids:
                raise ValueError("'correct' must reference existing options")
            if t is QuestionType.single_choice and len(self.correct) != 1:
                raise ValueError("single_choice needs exactly one correct option")
        elif t is QuestionType.ordering:
            if len(self.items) < 2:
                raise ValueError("ordering questions need at least 2 items")
        elif t is QuestionType.matching:
            if len(self.left) < 2 or len(self.right) < 2:
                raise ValueError("matching questions need at least 2 items per side")
            left_ids = {o.id for o in self.left}
            right_ids = {o.id for o in self.right}
            if set(self.pairs) != left_ids or not set(self.pairs.values()) <= right_ids:
                raise ValueError("'pairs' must map every left item to a right item")
        return self


class KnowledgeCheck(Header):
    pass_threshold: float = Field(default=0.70, ge=0, le=1)
    questions: list[Question] = Field(min_length=5)


class Criterion(Strict):
    id: ContentId
    description: str = Field(min_length=1)
    mandatory: bool = True
    tests: list[str] = Field(min_length=1)
    feedback: str = Field(min_length=1, description="Shown when the criterion is not met")


class Limits(Strict):
    wall_seconds: int = Field(default=MAX_WALL_SECONDS, ge=1, le=MAX_WALL_SECONDS)
    memory_mb: int = Field(default=MAX_MEMORY_MB, ge=32, le=MAX_MEMORY_MB)


class Challenge(Header):
    """Challenge metadata. Tests are all visible (D2); ``solution/`` is validator-only."""

    title: str = Field(min_length=1)
    difficulty_rank: int = Field(ge=1)
    scenario: str = Field(min_length=1)
    problem: str = Field(min_length=1)
    expected_outcome: str = Field(min_length=1)
    instructions: str = Field(min_length=1)
    criteria: list[Criterion] = Field(min_length=1)
    hints: list[str] = Field(min_length=2)
    reference_explanation: str = Field(min_length=1)
    competencies: list[ContentId] = Field(min_length=1)
    limits: Limits = Field(default_factory=Limits)

    @model_validator(mode="after")
    def _criteria(self) -> Challenge:
        if not any(c.mandatory for c in self.criteria):
            raise ValueError("a challenge needs at least one mandatory criterion")
        seen: set[str] = set()
        for c in self.criteria:
            for t in c.tests:
                if t in seen:
                    raise ValueError(f"test '{t}' belongs to more than one criterion")
                seen.add(t)
        return self


class DeprecationEntry(Strict):
    target: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    replacement: str | None = None
    since: date


class DeprecationCatalog(Strict):
    deprecations: list[DeprecationEntry] = Field(default_factory=list)
