"""Print ``name==version`` pins for the record venv, taken from ``poetry.lock``.

The record venv gets the released SDK from BASELINE plus the same third-party
versions CI installs, so snapshots differ from CI's replay only because of the
SDK. The pins come from the lock file, not from the local poetry env, which can
lag behind it (a pandas bump changes DataFrame dtypes in every snapshot).

Where the lock has several versions of a package, their environment markers
pick the one for this interpreter.
"""

import importlib.metadata
import re
import sys
import tomllib
from pathlib import Path
from typing import Dict, List

from packaging.markers import Marker

LOCK_FILE = Path(__file__).resolve().parent.parent / "poetry.lock"
PIN_ALSO = ("numpy", "pytest")


def _canonical(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _applies(entry: Dict) -> bool:
    markers = entry.get("markers")
    if not markers:
        return True
    groups = markers.values() if isinstance(markers, dict) else [markers]
    return any(Marker(group).evaluate() for group in groups)


def locked_versions() -> Dict[str, str]:
    lock = tomllib.loads(LOCK_FILE.read_text(encoding="utf-8"))
    versions: Dict[str, str] = {}
    for entry in lock["package"]:
        if _applies(entry):
            versions[_canonical(entry["name"])] = entry["version"]
    return versions


def runtime_requirements() -> List[str]:
    names = []
    for requirement in importlib.metadata.requires("alpaca-py") or []:
        if "extra ==" in requirement:
            continue
        match = re.match(r"[A-Za-z0-9_.\-]+", requirement)
        if match:
            names.append(match.group(0))
    return [*names, *PIN_ALSO]


def main() -> int:
    locked = locked_versions()
    missing = []
    for name in runtime_requirements():
        version = locked.get(_canonical(name))
        if version is None:
            missing.append(name)
        else:
            print(f"{name}=={version}")
    if missing:
        print(f"not in {LOCK_FILE.name}: {', '.join(missing)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
