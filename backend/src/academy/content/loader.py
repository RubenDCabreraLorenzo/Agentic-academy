"""Load the authored content tree (contracts/content-schema.md "Layout").

The loader never raises on bad content: it records :class:`Issue` objects so the validator can
report every problem in one run.
"""

from __future__ import annotations

import ast
import contextlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from markdown_it import MarkdownIt
from pydantic import BaseModel, ValidationError

from academy.content.schemas import (
    Challenge,
    CompetencyCatalog,
    DeprecationCatalog,
    KnowledgeCheck,
    LearningPath,
    LessonFrontMatter,
    Module,
)

FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n(.*)\Z", re.S)
HEADING_ANCHOR = re.compile(r"\{#([a-z0-9]+(?:-[a-z0-9]+)*)\}\s*$")
DIRECTIVE_OPEN = re.compile(r"^:::(\w+)(?:\{(.*)\})?\s*$")
ATTR = re.compile(r'(\w+)="([^"]*)"')
DIR_PREFIX = re.compile(r"^\d{2}-(.+)$")

#: Max size of any single text file included in a bundle.
MAX_FILE_BYTES = 64 * 1024


@dataclass(frozen=True)
class Issue:
    rule: str
    path: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"rule": self.rule, "path": self.path, "message": self.message}


@dataclass
class CodeBlock:
    language: str
    info: str
    content: str


@dataclass
class LoadedLesson:
    meta: LessonFrontMatter
    body: str
    path: Path
    anchors: set[str] = field(default_factory=set)
    code_blocks: list[CodeBlock] = field(default_factory=list)
    diagrams: list[dict[str, str]] = field(default_factory=list)
    directives: list[tuple[str, dict[str, str]]] = field(default_factory=list)


@dataclass
class LoadedChallenge:
    meta: Challenge
    path: Path
    starter: dict[str, str] = field(default_factory=dict)
    tests: dict[str, str] = field(default_factory=dict)
    solution: dict[str, str] = field(default_factory=dict)
    test_ids: list[str] = field(default_factory=list)


@dataclass
class LoadedModule:
    meta: Module
    path_id: str
    path: Path
    lessons: list[LoadedLesson] = field(default_factory=list)
    knowledge_check: KnowledgeCheck | None = None
    challenges: list[LoadedChallenge] = field(default_factory=list)


@dataclass
class LoadedPath:
    meta: LearningPath
    path: Path
    modules: list[LoadedModule] = field(default_factory=list)


@dataclass
class ContentTree:
    root: Path
    lang: str
    competencies: CompetencyCatalog | None = None
    paths: list[LoadedPath] = field(default_factory=list)
    lab_scenarios: dict[str, tuple[dict[str, Any], Path]] = field(default_factory=dict)
    deprecations: DeprecationCatalog = field(default_factory=DeprecationCatalog)
    issues: list[Issue] = field(default_factory=list)

    def issue(self, rule: str, path: Path | str, message: str) -> None:
        rel = str(path)
        with contextlib.suppress(ValueError):
            rel = str(Path(path).relative_to(self.root))
        self.issues.append(Issue(rule, rel, message))

    @property
    def modules(self) -> list[LoadedModule]:
        return [m for p in self.paths for m in p.modules]

    @property
    def challenges(self) -> list[LoadedChallenge]:
        return [c for m in self.modules for c in m.challenges]


def _parse[T: BaseModel](tree: ContentTree, model: type[T], data: Any, path: Path) -> T | None:
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        for err in exc.errors():
            loc = ".".join(str(p) for p in err["loc"])
            tree.issue("1-schema", path, f"{loc}: {err['msg']}" if loc else err["msg"])
        return None


def _yaml(tree: ContentTree, path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        tree.issue("1-schema", path, f"cannot read YAML: {exc}")
        return None


def _read_tree(tree: ContentTree, base: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    if not base.is_dir():
        return files
    for f in sorted(base.rglob("*")):
        if not f.is_file() or "__pycache__" in f.parts or f.suffix == ".pyc":
            continue
        rel = f.relative_to(base).as_posix()
        if f.stat().st_size > MAX_FILE_BYTES:
            tree.issue("1-schema", f, f"file larger than {MAX_FILE_BYTES} bytes")
            continue
        try:
            files[rel] = f.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            tree.issue("1-schema", f, "files must be UTF-8 text")
    return files


def parse_test_ids(files: dict[str, str]) -> list[str]:
    """Static discovery of pytest test ids ``<file>::<function>`` (module-level functions)."""
    ids: list[str] = []
    for name, source in sorted(files.items()):
        base = name.rsplit("/", 1)[-1]
        if not (base.startswith("test_") and base.endswith(".py")):
            continue
        try:
            module = ast.parse(source)
        except SyntaxError:
            continue
        for node in module.body:
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name.startswith(
                "test_"
            ):
                ids.append(f"{name}::{node.name}")
    return ids


_md = MarkdownIt("commonmark")


def analyse_markdown(lesson: LoadedLesson) -> None:
    """Extract anchors, code blocks, diagrams and directives from a lesson body."""
    for line in lesson.body.splitlines():
        m = DIRECTIVE_OPEN.match(line.strip())
        if m and m.group(1):
            lesson.directives.append((m.group(1), dict(ATTR.findall(m.group(2) or ""))))
    tokens = _md.parse(lesson.body)
    for i, tok in enumerate(tokens):
        if tok.type == "heading_open" and i + 1 < len(tokens):
            text = tokens[i + 1].content
            am = HEADING_ANCHOR.search(text)
            if am:
                lesson.anchors.add(am.group(1))
        elif tok.type == "fence":
            info = tok.info.strip()
            language = info.split(" ", 1)[0] if info else ""
            if language == "mermaid":
                alt = dict(ATTR.findall(info)).get("alt", "")
                lesson.diagrams.append({"kind": "mermaid", "alt": alt})
            else:
                lesson.code_blocks.append(CodeBlock(language, info, tok.content))
        elif tok.type == "inline" and tok.children:
            for child in tok.children:
                if child.type == "image":
                    alt = "".join(c.content for c in child.children or [])
                    lesson.diagrams.append({"kind": "image", "alt": alt})


def _load_lesson(tree: ContentTree, path: Path) -> LoadedLesson | None:
    text = path.read_text(encoding="utf-8")
    m = FRONT_MATTER.match(text)
    if not m:
        tree.issue("1-schema", path, "lesson must start with a YAML front matter block")
        return None
    try:
        front = yaml.safe_load(m.group(1))
    except yaml.YAMLError as exc:
        tree.issue("1-schema", path, f"invalid front matter: {exc}")
        return None
    meta = _parse(tree, LessonFrontMatter, front, path)
    if meta is None:
        return None
    lesson = LoadedLesson(meta=meta, body=m.group(2), path=path)
    analyse_markdown(lesson)
    return lesson


def _load_challenge(tree: ContentTree, cdir: Path) -> LoadedChallenge | None:
    meta = _parse(tree, Challenge, _yaml(tree, cdir / "challenge.yaml"), cdir / "challenge.yaml")
    if meta is None:
        return None
    ch = LoadedChallenge(meta=meta, path=cdir)
    ch.starter = _read_tree(tree, cdir / "starter")
    ch.tests = _read_tree(tree, cdir / "tests")
    ch.solution = _read_tree(tree, cdir / "solution")
    ch.test_ids = parse_test_ids(ch.tests)
    if (cdir / "hidden").exists() or (cdir / "tests" / "hidden").exists():
        tree.issue("7-challenge", cdir, "hidden tests are not supported in the MVP (review D2)")
    return ch


def _load_module(tree: ContentTree, mdir: Path, path_id: str) -> LoadedModule | None:
    meta = _parse(tree, Module, _yaml(tree, mdir / "module.yaml"), mdir / "module.yaml")
    if meta is None:
        return None
    folder = DIR_PREFIX.match(mdir.name)
    if not folder or folder.group(1) != meta.id:
        tree.issue("1-schema", mdir, f"module folder must be named NN-{meta.id}")
    module = LoadedModule(meta=meta, path_id=path_id, path=mdir)
    for lf in sorted((mdir / "lessons").glob("*.md")):
        lesson = _load_lesson(tree, lf)
        if lesson:
            module.lessons.append(lesson)
    kc_file = mdir / "knowledge-check.yaml"
    if kc_file.exists():
        module.knowledge_check = _parse(tree, KnowledgeCheck, _yaml(tree, kc_file), kc_file)
    for cdir in sorted((mdir / "challenges").glob("*")):
        if cdir.is_dir():
            ch = _load_challenge(tree, cdir)
            if ch:
                module.challenges.append(ch)
    return module


def load_tree(root: Path, lang: str = "en") -> ContentTree:
    """Load ``root/competencies.yaml`` and ``root/<lang>/…``."""
    root = root.resolve()
    tree = ContentTree(root=root, lang=lang)
    comp_file = root / "competencies.yaml"
    if comp_file.exists():
        tree.competencies = _parse(tree, CompetencyCatalog, _yaml(tree, comp_file), comp_file)
    else:
        tree.issue("1-schema", comp_file, "missing competencies.yaml")
    base = root / lang
    for pdir in sorted((base / "paths").glob("*")):
        pf = pdir / "path.yaml"
        if not pf.exists():
            continue
        meta = _parse(tree, LearningPath, _yaml(tree, pf), pf)
        if meta is None:
            continue
        if pdir.name != meta.id:
            tree.issue("1-schema", pdir, f"path folder must be named {meta.id}")
        lp = LoadedPath(meta=meta, path=pdir)
        for mdir in sorted((pdir / "modules").glob("*")):
            if mdir.is_dir():
                mod = _load_module(tree, mdir, meta.id)
                if mod:
                    lp.modules.append(mod)
        tree.paths.append(lp)
    for sf in sorted((base / "lab").glob("*.json")):
        try:
            tree.lab_scenarios[sf.stem] = (json.loads(sf.read_text(encoding="utf-8")), sf)
        except (OSError, json.JSONDecodeError) as exc:
            tree.issue("8-lab", sf, f"cannot read JSON: {exc}")
    dep_file = base / "deprecations.yaml"
    if dep_file.exists():
        parsed = _parse(tree, DeprecationCatalog, _yaml(tree, dep_file) or {}, dep_file)
        if parsed:
            tree.deprecations = parsed
    return tree
