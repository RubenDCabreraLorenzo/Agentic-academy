"""Learner file validation, applied again on the runner before launching a sandbox.

Same rules as the API (backend ``academy.challenges.files``): learner files can never overwrite,
shadow or replace the trusted evaluation tests, the manifest or the harness.
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
    return {posixpath.splitext(posixpath.basename(n))[0] for n in test_files if n.endswith(".py")}


def validate_files(files: object, test_files: dict[str, str]) -> dict[str, str]:
    if not isinstance(files, dict) or not files:
        raise InvalidFilesError("no files submitted")
    if len(files) > MAX_FILES:
        raise InvalidFilesError(f"at most {MAX_FILES} files")
    total = 0
    reserved_modules = test_module_names(test_files)
    for name, content in files.items():
        if not isinstance(name, str) or not isinstance(content, str):
            raise InvalidFilesError("file names and contents must be text")
        total += len(name.encode()) + len(content.encode())
        if not name or "\\" in name or "\x00" in name or "\x00" in content:
            raise InvalidFilesError("invalid file name")
        if name.startswith("/") or posixpath.normpath(name) != name or ".." in name.split("/"):
            raise InvalidFilesError(f"invalid path '{name}'")
        parts = name.split("/")
        if parts[0] in RESERVED_TOP or parts[-1] in RESERVED_BASENAMES:
            raise InvalidFilesError(f"'{name}' uses a reserved name")
        if any(fnmatch.fnmatch(p, pat) for p in parts for pat in RESERVED_PATTERNS):
            raise InvalidFilesError(f"'{name}' uses a reserved name")
        if parts[-1].endswith(".py") and posixpath.splitext(parts[-1])[0] in reserved_modules:
            raise InvalidFilesError(f"'{name}' would shadow an evaluation test module")
    if total > MAX_FILES_BYTES:
        raise InvalidFilesError("files exceed 256 KB")
    return files
