"""Report checked-in generated artifacts that no longer match the pinned specification.

Public modules are checked as well: each must re-export every generated name, and none
may re-export a name the specification dropped. Nothing is edited.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from tools.scripts.openapi.generate import (  # noqa: E402
    TARGETS,
    ToolchainError,
    dotted_name,
    generate,
    missing_reexports,
    reject_dropped_reexports,
)


def _files(root: Path) -> dict[str, bytes]:
    if not root.is_dir():
        return {}
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    }


def check(target: str, output_root: Path) -> tuple[list[str], list[str]]:
    """Return what generation would change for ``target``.

    The first list holds the artifact paths, relative to ``output_root``, that would
    change. The second holds the public re-export problems generation would report.
    """
    settings = TARGETS[target]
    output = output_root / settings["output"].relative_to(REPOSITORY_ROOT)
    with tempfile.TemporaryDirectory(prefix="alpaca-openapi-check-") as workspace:
        expected_root = Path(workspace) / "expected"
        generate(
            spec=settings["spec"],
            output=expected_root,
            surface=settings["surface"],
            generator=settings.get("generator"),
        )
        expected = _files(expected_root)
        reexports = _reexport_problems(settings, expected_root)
    actual = _files(output)

    relative_output = output.relative_to(output_root)
    changed = sorted(
        str(relative_output / name)
        for name in set(expected) | set(actual)
        if expected.get(name) != actual.get(name)
    )
    return changed, reexports


def _reexport_problems(settings: dict, expected_root: Path) -> list[str]:
    public = settings["public"]
    try:
        reject_dropped_reexports(public, dotted_name(settings["output"]), expected_root)
        # The public modules import the checked-in package, so artifact drift can make
        # this import fail; the drift itself is reported alongside.
        missing = missing_reexports(public, expected_root)
    except ValueError as error:
        return [str(error)]
    return [
        f"{path.relative_to(REPOSITORY_ROOT)} does not re-export "
        f"{', '.join(names)}; run `make generate-openapi` to add them"
        for path, names in sorted(missing.items())
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", choices=TARGETS)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=REPOSITORY_ROOT,
        help="directory holding the generated package, defaults to the repository",
    )
    args = parser.parse_args()

    try:
        changed, reexports = check(args.target, args.output_root.resolve())
    except ToolchainError as error:
        # A missing tool is a setup problem, so report it without a traceback.
        print(error, file=sys.stderr)
        return 1
    if changed:
        print(
            "Generated OpenAPI artifacts are out of date; run `make generate-openapi`."
        )
        for path in changed:
            print(path)
    if reexports:
        print("Public re-exports are out of date.")
        for problem in reexports:
            print(problem)
    if changed or reexports:
        return 1
    print(f"Generated OpenAPI artifacts are current: {args.target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
