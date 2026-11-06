"""Validation of learner-submitted files (runner protocol §2).

Learner files can never overwrite, shadow or replace the trusted evaluation tests or the harness.
The runner applies the same rules again before launching a sandbox; checking here as well gives the
learner immediate feedback. This blocks accidental and trivial shadowing; it does not make the
in-process harness tamper-proof (review D1).
"""

from __future__ import annotations

import fnmatch
import posixpath

MAX_FILES_BYTES = 256 * 1024
MAX_FILES = 50
RESERVED_BASENAMES = {"conftest.py", "sitecustomize.py", "usercustomize.py", "pytest.py"}
RESERVED_TOP = {"tests", "manifest.json", "pytest", "_pytest"}
RESERVED_PATTERNS = ("academy_sim*", "*.pth")


class InvalidFilesError(ValueError):
    pass


def test_module_names(test_files: dict[str, str]) -> set[str]:
    return {
        posixpath.splitext(posixpath.basename(name))[0]
        for name in test_files
        if name.endswith(".py")
    }


def validate_files(files: dict[str, str], test_files: dict[str, str]) -> None:
    if not isinstance(files, dict) or not files:
        raise InvalidFilesError("submit at least one file")
    if len(files) > MAX_FILES:
        raise InvalidFilesError(f"at most {MAX_FILES} files")
    total = sum(len(k.encode()) + len(v.encode()) for k, v in files.items())
    if total > MAX_FILES_BYTES:
        raise InvalidFilesError("files exceed 256 KB")
    reserved_modules = test_module_names(test_files)
    for name in files:
        if not isinstance(name, str) or not name or "\\" in name or "\x00" in name:
            raise InvalidFilesError("invalid file name")
        if name.startswith("/") or posixpath.normpath(name) != name or ".." in name.split("/"):
            raise InvalidFilesError(f"invalid path '{name}'")
        parts = name.split("/")
        base = parts[-1]
        if parts[0] in RESERVED_TOP or base in RESERVED_BASENAMES:
            raise InvalidFilesError(f"'{name}' uses a reserved name")
        if any(fnmatch.fnmatch(p, pat) for p in parts for pat in RESERVED_PATTERNS):
            raise InvalidFilesError(f"'{name}' uses a reserved name")
        module = posixpath.splitext(base)[0]
        if base.endswith(".py") and module in reserved_modules:
            raise InvalidFilesError(f"'{name}' would shadow an evaluation test module")
