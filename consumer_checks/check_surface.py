#!/usr/bin/env python3
"""Check that what is new in the public SDK surface since BASELINE is exercised.

New surface is the current SDK's items (see _surface.py: clients, methods,
method parameters, request fields, response fields) minus those of the
BASELINE release, stored in ``surface_baseline.json``. This replays every
recorded scenario, observes what they exercise (see _exercised.py), and lists
the new items nothing exercises:

* a method parameter no scenario passes,
* a request field no scenario sets,
* a response field no scenario sees with a value other than None.

With ``--strict`` (CI), it exits 1 when such an item is not covered by
``surface_allowlist.txt``, or when an exact allowlist entry is no longer
needed. ``--show-all`` also reports how much of the whole surface is
exercised, new or not.

  python consumer_checks/check_surface.py [--strict] [--show-all]
"""

from __future__ import annotations

import argparse
import collections
import fnmatch
import json
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Set

HERE = Path(__file__).resolve().parent
BASELINE_SURFACE = HERE / "surface_baseline.json"
ALLOWLIST = HERE / "surface_allowlist.txt"
sys.path.insert(0, str(HERE))

import _surface  # noqa: E402

KINDS = ("client", "method", "param", "request", "response")
HINTS = {
    "client": "a scenario that uses it",
    "method": "a scenario that calls it",
    "param": "a scenario that passes it",
    "request": "a scenario that sets it",
    "response": "a scenario whose response has a value for it",
}


def load_allowlist() -> Dict[str, str]:
    """Pattern (fnmatch, on item ids) to its reason."""
    entries: Dict[str, str] = {}
    for line in ALLOWLIST.read_text(encoding="utf-8").splitlines():
        pattern, _, reason = line.partition("#")
        if pattern.strip():
            entries[pattern.strip()] = reason.strip()
    return entries


def exercised_by_replay() -> Dict:
    import pytest

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "exercised.json"
        status = pytest.main(
            [
                str(HERE),
                "-q",
                "--no-header",
                "-p",
                "no:warnings",
                "--consumer-strict",
                f"--consumer-surface-out={out}",
            ]
        )
        if status != 0 or not out.exists():
            print("\nReplay failed: fix it first (`make consumer-replay`).")
            sys.exit(1)
        return json.loads(out.read_text(encoding="utf-8"))


def by_kind(items: Set[str]) -> Dict[str, List[str]]:
    grouped: Dict[str, List[str]] = collections.defaultdict(list)
    for item in sorted(items):
        grouped[item.split(":", 1)[0]].append(item)
    return grouped


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 on new items nothing exercises that are not allowlisted, "
        "and on exact allowlist entries no longer needed.",
    )
    parser.add_argument(
        "--show-all",
        action="store_true",
        help="Also report how much of the whole surface is exercised.",
    )
    args = parser.parse_args()

    baseline_version = (HERE / "BASELINE").read_text(encoding="utf-8").strip()
    stored = json.loads(BASELINE_SURFACE.read_text(encoding="utf-8"))
    if stored["sdk"] != baseline_version:
        print(
            f"{BASELINE_SURFACE.name} describes alpaca-py {stored['sdk']}, but "
            f"BASELINE is {baseline_version}. Regenerate it with "
            "`make consumer-surface-baseline`."
        )
        return 1

    current = _surface.collect().items
    new = current - set(stored["items"])
    removed = set(stored["items"]) - current

    replay = exercised_by_replay()
    if not replay["complete"]:
        print("\nNot every scenario replayed, so the result would be partial.")
        return 1
    exercised = set(replay["exercised"])

    allowlist = load_allowlist()
    unexercised = new - exercised
    allowed = {
        item
        for item in unexercised
        if any(fnmatch.fnmatchcase(item, pattern) for pattern in allowlist)
    }
    missing = unexercised - allowed

    print(
        f"\nPublic surface new since alpaca-py {baseline_version}: {len(new)} items, "
        f"{len(new & exercised)} exercised, {len(allowed)} allowlisted, "
        f"{len(missing)} not exercised"
    )
    for kind in KINDS:
        items = [item for item in new if item.startswith(f"{kind}:")]
        if items:
            done = len([item for item in items if item in exercised])
            print(f"  {kind:<9} {done:>4}/{len(items):<4} exercised")
    if removed:
        print(
            f"  ({len(removed)} items of {baseline_version} are gone; "
            "`make check-api-breakage` reports removals)"
        )

    status = 0
    if missing:
        print(
            "\nNew public surface no recorded scenario exercises (add a scenario, or a "
            f"pattern with a reason to {ALLOWLIST.name}):"
        )
        for kind, items in by_kind(missing).items():
            print(f"  {kind}: needs {HINTS[kind]}")
            for item in items:
                print(f"    - {item.split(':', 1)[1]}")
        status = 1 if args.strict else 0

    # Glob patterns are standing rules (a client not wired in yet); an exact
    # entry is for one item and goes once that item is exercised.
    stale = sorted(
        pattern
        for pattern in allowlist
        if not any(char in pattern for char in "*?[")
        and not any(fnmatch.fnmatchcase(item, pattern) for item in unexercised)
    )
    if stale:
        print(f"\n{ALLOWLIST.name} entries no longer needed (remove them):")
        for pattern in stale:
            print(f"  - {pattern}")
        status = 1 if args.strict else status

    if args.show_all:
        print("\nWhole public surface exercised by the recorded scenarios:")
        for kind in KINDS:
            items = {item for item in current if item.startswith(f"{kind}:")}
            print(f"  {kind:<9} {len(items & exercised):>4}/{len(items):<4}")
    return status


if __name__ == "__main__":
    sys.exit(main())
