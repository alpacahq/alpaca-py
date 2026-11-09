#!/usr/bin/env python3
"""Report which public client methods no consumer scenario checks.

Without usage data, coverage of the public client surface is the guide for
what to write next. A method counts as checked only when a scenario that
covers it has a recording: replay skips scenarios without one, so declaring
``covers`` alone checks nothing. Exits 1 when a scenario's ``covers`` names a
method that does not exist (a typo, or a public method that was removed), and
when checked coverage is below ``--fail-under``.

With ``--strict`` (CI) it also exits 1 when a public method has no recorded
scenario and is not listed in ``coverage_allowlist.txt``, or when an allowlist
entry is no longer needed. A PR that adds a public method therefore adds its
scenario too, or an allowlist entry reviewers can see.

  python consumer_checks/check_coverage.py
  python consumer_checks/check_coverage.py --fail-under 50 --show-uncovered
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List, Set

HERE = Path(__file__).resolve().parent
ALLOWLIST = HERE / "coverage_allowlist.txt"
sys.path.insert(0, str(HERE))

from scenarios import load_all  # noqa: E402

import _surface  # noqa: E402


def public_methods() -> Dict[str, List[str]]:
    """Every public client (any public RESTClient subclass) and its methods.

    Discovered, not listed, so a new client is covered by the gate too.
    """
    return dict(sorted(_surface.collect().methods.items()))


def load_allowlist(path: Path) -> Dict[str, str]:
    """Entry (``Client`` or ``Client.method``) to its reason."""
    entries: Dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        entry, _, reason = line.partition("#")
        if entry.strip():
            entries[entry.strip()] = reason.strip()
    return entries


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--fail-under",
        type=float,
        default=0.0,
        help="Exit 1 when checked coverage (percent) is below this.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 on public methods without a recorded scenario that are not "
        "in coverage_allowlist.txt, and on allowlist entries no longer needed.",
    )
    parser.add_argument(
        "--show-uncovered",
        action="store_true",
        help="List every uncovered method.",
    )
    args = parser.parse_args()

    methods = public_methods()
    known = {
        f"{client}.{method}" for client, names in methods.items() for method in names
    }
    recordings_dir = Path(
        os.environ.get("CONSUMER_RECORDINGS_DIR", HERE / "recordings")
    )
    recorded = {path.stem for path in recordings_dir.glob("*.json")}
    declared: Set[str] = set()
    checked: Set[str] = set()
    unknown: List[str] = []
    for scn in load_all().values():
        for target in scn.covers:
            if target not in known:
                unknown.append(f"{target} (in {scn.name})")
                continue
            declared.add(target)
            if scn.name in recorded:
                checked.add(target)

    total = len(known)
    print(
        f"Consumer scenario coverage: {len(checked)}/{total} public client methods "
        f"checked ({len(declared)} have a scenario, "
        f"{len(declared - checked)} of those not recorded yet)"
    )
    print(f"  {'client':<28} {'checked':>7}  {'scenario':>8}  {'total':>5}")
    for client, names in methods.items():
        has_check = [name for name in names if f"{client}.{name}" in checked]
        has_scenario = [name for name in names if f"{client}.{name}" in declared]
        print(
            f"  {client:<28} {len(has_check):>7}  {len(has_scenario):>8}  {len(names):>5}"
        )
        if args.show_uncovered:
            for name in names:
                target = f"{client}.{name}"
                if target in declared and target not in checked:
                    print(f"      - {name} (scenario not recorded)")
                elif target not in declared:
                    print(f"      - {name}")

    status = 0
    if unknown:
        print("\nScenarios cover methods that do not exist on the current SDK:")
        for target in sorted(unknown):
            print(f"  - {target}")
        status = 1
    if args.strict:
        allowlist = load_allowlist(ALLOWLIST)
        unchecked = known - checked

        def allowed(target: str) -> bool:
            return target in allowlist or target.split(".", 1)[0] in allowlist

        missing = sorted(target for target in unchecked if allowed(target) is False)
        stale = sorted(
            entry
            for entry in allowlist
            if not any(
                target == entry or target.split(".", 1)[0] == entry
                for target in unchecked
            )
        )
        if missing:
            print(
                "\nPublic methods without a recorded scenario (add one, or an entry "
                f"with a reason to {ALLOWLIST.name}):"
            )
            for target in missing:
                note = " (scenario not recorded)" if target in declared else ""
                print(f"  - {target}{note}")
            status = 1
        if stale:
            print(f"\n{ALLOWLIST.name} entries no longer needed (remove them):")
            for entry in stale:
                print(f"  - {entry}")
            status = 1

    percent = 100.0 * len(checked) / total if total else 100.0
    if percent < args.fail_under:
        print(f"\nCoverage {percent:.1f}% is below --fail-under {args.fail_under}%")
        status = 1
    return status


if __name__ == "__main__":
    sys.exit(main())
