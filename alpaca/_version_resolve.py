"""Derive a useful ``__version__`` for local checkouts.

Published builds have the ``0.0.0`` placeholder substituted by
poetry-dynamic-versioning, so :func:`resolve_version` returns immediately with
no I/O. In an editable checkout the placeholder remains, so we derive
``<latest-tag>-dev+g<short-sha>`` from a single ``git describe --tags --long``
call to distinguish development commits in the User-Agent. If git is
unavailable we fall back to ``0.0.0-dev``.

Named ``_version_resolve`` (not ``_version``) to avoid colliding with
poetry-dynamic-versioning's default ``*/_version.py`` substitution glob.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Optional

_PLACEHOLDER_VERSIONS = frozenset({"0.0.0", "0.0.0.dev0"})
_FALLBACK = "0.0.0-dev"
# git describe --tags --long → v0.43.5-16-g0bc1e2d (or v0.43.5-0-g… on the tag)
_DESCRIBE_LONG_RE = re.compile(r"^(?P<tag>.+)-(?P<distance>\d+)-g(?P<sha>[0-9a-f]+)$")


def _strip_leading_v(value: str) -> str:
    if value.startswith("v") and len(value) > 1 and value[1].isdigit():
        return value[1:]
    return value


def version_from_git() -> Optional[str]:
    root = Path(__file__).resolve().parent.parent
    try:
        described = subprocess.check_output(
            ["git", "describe", "--tags", "--long"],
            cwd=root,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (OSError, subprocess.SubprocessError):
        return None

    match = _DESCRIBE_LONG_RE.match(described)
    if not match:
        return None

    tag = _strip_leading_v(match.group("tag"))
    sha = match.group("sha")
    return f"{tag}-dev+g{sha}"


def resolve_version(current: str) -> str:
    """Return the substituted build version, or a git-derived dev version."""
    if current not in _PLACEHOLDER_VERSIONS:
        return _strip_leading_v(current)
    return version_from_git() or _FALLBACK
