#!/usr/bin/env python3
"""Compare the current checkout's public API against a published alpaca-py release.

Uses AexPy (https://github.com/StardustDL/aexpy) to extract APIs from wheels and
report breaking / alias / additive changes. AexPy tracks alias targets rather than
enum membership or Pydantic field metadata, so this script additionally snapshots:

* every publicly exported enum's ``name -> value`` map and defining target
* every publicly exported Pydantic model's field contract (type, requiredness,
  validation/serialization aliases) and defining target

Examples:
  tools/scripts/compare_api_breakage.py
  tools/scripts/compare_api_breakage.py --against 0.43.5
  tools/scripts/compare_api_breakage.py --workdir /tmp/aexpy-alpaca \\
      --fail-on-breaking --fail-on-unknown
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import venv
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_NAME = "alpaca-py"
TOP_MODULE = "alpaca"
AEXPY_VERSION = "0.4.3"
TOP_BREAKING_LIMIT = 20

# Runs inside the comparison venv with one alpaca-py wheel installed. Emits, for
# every public import path that exposes an SDK enum or Pydantic model, the target
# class plus membership / field contract. Keying on the public path (rather than
# on the defining module) keeps the comparison stable when a class moves.
_PUBLIC_DUMP_SOURCE = """
import enum
import importlib
import importlib.metadata
import json
import pkgutil
import typing

from pydantic import BaseModel
from pydantic.fields import AliasChoices, AliasPath

TOP_MODULE = {top_module!r}
PACKAGE_NAME = {package_name!r}


def _is_public(module_name):
    return not any(part.startswith("_") for part in module_name.split(".")[1:])


def _annotation_repr(annotation):
    if annotation is None:
        return "None"
    if isinstance(annotation, str):
        return annotation
    origin = typing.get_origin(annotation)
    args = typing.get_args(annotation)
    if origin is not None:
        name = getattr(origin, "__name__", None) or getattr(origin, "_name", None)
        if name is None:
            name = repr(origin)
        if args:
            return f"{{name}}[{{', '.join(_annotation_repr(a) for a in args)}}]"
        return str(name)
    if isinstance(annotation, type):
        module = getattr(annotation, "__module__", "")
        qual = getattr(annotation, "__qualname__", annotation.__name__)
        if module and module != "builtins":
            return f"{{module}}.{{qual}}"
        return qual
    return repr(annotation)


def _alias_strings(alias):
    if alias is None:
        return []
    if isinstance(alias, str):
        return [alias]
    if isinstance(alias, AliasPath):
        return [".".join(str(p) for p in alias.path)]
    if isinstance(alias, AliasChoices):
        out = []
        for choice in alias.choices:
            out.extend(_alias_strings(choice))
        return out
    return [repr(alias)]


def _field_snapshot(field_info):
    validation = sorted(set(_alias_strings(field_info.validation_alias)))
    serialization = field_info.serialization_alias
    if serialization is not None and not isinstance(serialization, str):
        serialization = repr(serialization)
    return {{
        "type": _annotation_repr(field_info.annotation),
        "required": bool(field_info.is_required()),
        "validation_aliases": validation,
        "serialization_alias": serialization,
    }}


def main():
    root = importlib.import_module(TOP_MODULE)
    module_names = [TOP_MODULE]
    for info in pkgutil.walk_packages(root.__path__, prefix=TOP_MODULE + "."):
        if _is_public(info.name):
            module_names.append(info.name)

    enums = {{}}
    models = {{}}
    errors = {{}}
    for module_name in sorted(module_names):
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:  # noqa: BLE001 - report and keep going
            errors[module_name] = f"{{type(exc).__name__}}: {{exc}}"
            continue
        for name, obj in vars(module).items():
            if name.startswith("_"):
                continue
            if not isinstance(obj, type):
                continue
            module_attr = getattr(obj, "__module__", "")
            if not module_attr.startswith(TOP_MODULE):
                continue
            path = f"{{module_name}}.{{name}}"
            if issubclass(obj, enum.Enum):
                enums[path] = {{
                    "target": f"{{obj.__module__}}.{{obj.__qualname__}}",
                    "members": {{
                        member_name: repr(member.value)
                        for member_name, member in obj.__members__.items()
                    }},
                }}
            elif issubclass(obj, BaseModel) and obj is not BaseModel:
                models[path] = {{
                    "target": f"{{obj.__module__}}.{{obj.__qualname__}}",
                    "fields": {{
                        field_name: _field_snapshot(field_info)
                        for field_name, field_info in obj.model_fields.items()
                    }},
                }}

    print(
        json.dumps(
            {{
                "version": importlib.metadata.version(PACKAGE_NAME),
                "location": root.__file__,
                "enums": enums,
                "models": models,
                "errors": errors,
            }},
            sort_keys=True,
        )
    )


main()
"""


class ToolError(RuntimeError):
    pass


Findings = list[tuple[str, list[str]]]


def _normalize_version(version: str) -> str:
    """Normalize wheel-filename vs metadata local-version encoding (PEP 427).

    Wheel filenames replace ``+`` in the local version with ``_``, and ``.``
    inside the local label with ``_``. Metadata keeps the PEP 440 ``+`` form.
    """
    if "+" in version or "_" not in version:
        return version
    public, local = version.split("_", 1)
    return f"{public}+{local.replace('_', '.')}"


def _versions_equal(left: str, right: str) -> bool:
    return _normalize_version(left) == _normalize_version(right)


def _require_no_dump_errors(payload: dict) -> None:
    errors = payload.get("errors") or {}
    if not errors:
        return
    details = "; ".join(
        f"{name}: {message}" for name, message in sorted(errors.items())
    )
    raise ToolError(f"dump import errors ({len(errors)}): {details}")


def _run(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    check: bool = True,
    verbose: bool = True,
    echo_stdout: bool | None = None,
    echo_stderr: bool | None = None,
    echo_cmd: bool | None = None,
) -> subprocess.CompletedProcess[str]:
    if echo_cmd is None:
        echo_cmd = verbose
    if echo_stdout is None:
        echo_stdout = verbose
    if echo_stderr is None:
        echo_stderr = verbose
    if echo_cmd:
        print("+", " ".join(cmd), flush=True)
    result = subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
    )
    if result.stdout and echo_stdout:
        sys.stdout.write(result.stdout)
    if result.stderr and (echo_stderr or result.returncode != 0):
        sys.stderr.write(result.stderr)
    if check and result.returncode != 0:
        raise ToolError(f"command failed ({result.returncode}): {' '.join(cmd)}")
    return result


def _latest_pypi_version(package: str) -> str:
    url = f"https://pypi.org/pypi/{package}/json"
    with urllib.request.urlopen(url, timeout=30) as response:
        payload = json.load(response)
    version = payload["info"]["version"]
    if not version:
        raise ToolError(f"could not resolve latest version for {package}")
    return version


def _ensure_venv(venv_dir: Path, *, verbose: bool = True) -> Path:
    python = venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.exists():
        if verbose:
            print(f"Creating virtualenv at {venv_dir}", flush=True)
        builder = venv.EnvBuilder(with_pip=True)
        builder.create(venv_dir)
    return python


def _pip(python: Path, *args: str, verbose: bool = True) -> None:
    _run([str(python), "-m", "pip", *args], verbose=verbose)


def _download_release_wheel(
    python: Path, version: str, wheels_dir: Path, *, verbose: bool = True
) -> Path:
    wheels_dir.mkdir(parents=True, exist_ok=True)
    _pip(
        python,
        "download",
        f"{PACKAGE_NAME}=={version}",
        "-d",
        str(wheels_dir),
        "--no-deps",
        verbose=verbose,
    )
    matches = sorted(wheels_dir.glob(f"alpaca_py-{version}-*.whl"))
    exact = [
        path
        for path in matches
        if _versions_equal(_wheel_version(path), version)
    ]
    if not exact:
        raise ToolError(f"failed to download wheel for {PACKAGE_NAME}=={version}")
    return exact[0]


def _build_current_wheel(
    wheels_dir: Path, *, exclude: Path | None = None, verbose: bool = True
) -> Path:
    wheels_dir.mkdir(parents=True, exist_ok=True)
    poetry = shutil.which("poetry")
    if not poetry:
        raise ToolError("poetry is required to build the current branch wheel")
    before_mtime = {path: path.stat().st_mtime for path in wheels_dir.glob("*.whl")}
    _run(
        [poetry, "build", "-f", "wheel", "-o", str(wheels_dir)],
        cwd=REPOSITORY_ROOT,
        verbose=verbose,
    )
    candidates = []
    for path in wheels_dir.glob("*.whl"):
        if exclude is not None and path.resolve() == exclude.resolve():
            continue
        mtime = path.stat().st_mtime
        if path not in before_mtime or mtime > before_mtime[path]:
            candidates.append(path)
    if not candidates:
        candidates = [
            path
            for path in wheels_dir.glob("*.whl")
            if exclude is None or path.resolve() != exclude.resolve()
        ]
    if not candidates:
        raise ToolError("poetry build did not produce a wheel")
    return sorted(candidates, key=lambda p: p.stat().st_mtime)[-1]


def _wheel_version(wheel: Path) -> str:
    parts = wheel.stem.split("-")
    if len(parts) < 2:
        raise ToolError(f"unexpected wheel name: {wheel.name}")
    return parts[1]


def _aexpy(
    python: Path, *args: str, echo_stderr: bool | None = None, verbose: bool = True
) -> None:
    _run(
        [str(python), "-m", "aexpy", *args],
        echo_stderr=echo_stderr,
        verbose=verbose,
    )


def _extract(
    python: Path, wheel: Path, api_json: Path, *, verbose: bool = True
) -> None:
    # Install with dependencies so AexPy's dynamic import sees a working package.
    _pip(python, "install", "--force-reinstall", str(wheel), verbose=verbose)
    _aexpy(
        python, "extract", str(wheel), str(api_json), "-w", "--no-temp", verbose=verbose
    )


def _venv_site_packages(python: Path, *, verbose: bool = True) -> Path:
    result = _run(
        [str(python), "-c", "import sysconfig; print(sysconfig.get_path('purelib'))"],
        verbose=verbose,
        echo_stdout=False,
        echo_cmd=False,
    )
    site_packages = Path(result.stdout.strip())
    if not site_packages.is_dir():
        raise ToolError(f"could not resolve site-packages for {python}")
    return site_packages


def _require_snapshot_location(location: object, site_packages: Path) -> None:
    if not isinstance(location, str) or not location:
        raise ToolError("public API snapshot is missing import location")
    imported = Path(location).resolve()
    try:
        imported.relative_to(site_packages.resolve())
    except ValueError as exc:
        raise ToolError(
            f"public API snapshot imported from {location}, expected installed "
            f"package under {site_packages}"
        ) from exc


def _dump_public_api(
    python: Path,
    snapshot_json: Path,
    run_dir: Path,
    expected_version: str,
    *,
    verbose: bool = True,
) -> dict:
    """Snapshot public enums/models of the currently installed alpaca-py.

    Runs in isolated mode from an empty nested directory so a ``--workdir`` that
    contains the checkout (for example ``WORKDIR=$PWD``) cannot shadow the wheel
    on Python 3.10, where ``PYTHONSAFEPATH`` is unsupported.
    """
    source = _PUBLIC_DUMP_SOURCE.format(
        top_module=TOP_MODULE, package_name=PACKAGE_NAME
    )
    env = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
    site_packages = _venv_site_packages(python, verbose=verbose)
    snapshot_run_dir = run_dir / ".snapshot_run"
    snapshot_run_dir.mkdir(parents=True, exist_ok=True)
    if verbose:
        print(f"+ {python} -I -c <public api snapshot>", flush=True)
    result = _run(
        [str(python), "-I", "-c", source],
        cwd=snapshot_run_dir,
        env=env,
        verbose=verbose,
        echo_stdout=False,
        echo_cmd=False,
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ToolError(f"could not parse public API snapshot: {exc}") from exc

    _require_snapshot_location(payload.get("location"), site_packages)

    version = payload.get("version")
    if not isinstance(version, str) or not _versions_equal(version, expected_version):
        raise ToolError(
            f"public API snapshot imported {PACKAGE_NAME} {version} from "
            f"{payload.get('location')}, expected {expected_version}"
        )

    snapshot_json.write_text(json.dumps(payload, indent=2, sort_keys=True))
    if verbose:
        for module_name, message in sorted(payload.get("errors", {}).items()):
            print(f"  warning: skipped {module_name} ({message})", flush=True)
        print(
            f"  captured {len(payload.get('enums', {}))} enum paths and "
            f"{len(payload.get('models', {}))} model paths "
            f"from {PACKAGE_NAME} {version}",
            flush=True,
        )
    return payload


def _sorted_findings(findings: dict[str, list[str]]) -> Findings:
    return [(message, sorted(paths)) for message, paths in sorted(findings.items())]


def _compare_enums(old: dict, new: dict) -> tuple[Findings, Findings]:
    """Return (breaking, additive) enum findings as ``(message, public paths)`` pairs.

    Removing an exported enum, dropping a member, changing a member's value, or
    swapping the defining target class all break consumers; new members do not.
    """
    old_enums = old.get("enums", {})
    new_enums = new.get("enums", {})

    breaking: dict[str, list[str]] = {}
    additive: dict[str, list[str]] = {}

    for path in sorted(old_enums):
        short_name = path.rsplit(".", 1)[-1]
        if path not in new_enums:
            message = f"{short_name}: no longer exported as an SDK enum"
            breaking.setdefault(message, []).append(path)
            continue

        old_entry = old_enums[path]
        new_entry = new_enums[path]
        old_target = old_entry.get("target")
        new_target = new_entry.get("target")
        if old_target != new_target:
            message = f"{short_name}: target changed: {old_target} -> {new_target}"
            breaking.setdefault(message, []).append(path)

        old_members = old_entry.get("members", {})
        new_members = new_entry.get("members", {})
        for name, value in sorted(old_members.items()):
            if name not in new_members:
                message = f"{short_name}.{name} removed (was {value})"
                breaking.setdefault(message, []).append(path)
            elif new_members[name] != value:
                message = (
                    f"{short_name}.{name} value changed: "
                    f"{value} -> {new_members[name]}"
                )
                breaking.setdefault(message, []).append(path)
        for name, value in sorted(new_members.items()):
            if name not in old_members:
                message = f"{short_name}.{name} added ({value})"
                additive.setdefault(message, []).append(path)

    return _sorted_findings(breaking), _sorted_findings(additive)


def _compare_models(old: dict, new: dict) -> tuple[Findings, Findings]:
    """Return (breaking, additive) Pydantic model findings.

    Breaking: removed export/field, required field added, requiredness tightened,
    type or alias changes, defining-target swaps.
    Additive: optional field added, requiredness relaxed.
    """
    old_models = old.get("models", {})
    new_models = new.get("models", {})

    breaking: dict[str, list[str]] = {}
    additive: dict[str, list[str]] = {}

    for path in sorted(old_models):
        short_name = path.rsplit(".", 1)[-1]
        if path not in new_models:
            message = f"{short_name}: no longer exported as an SDK model"
            breaking.setdefault(message, []).append(path)
            continue

        old_entry = old_models[path]
        new_entry = new_models[path]
        old_target = old_entry.get("target")
        new_target = new_entry.get("target")
        if old_target != new_target:
            message = f"{short_name}: target changed: {old_target} -> {new_target}"
            breaking.setdefault(message, []).append(path)

        old_fields = old_entry.get("fields", {})
        new_fields = new_entry.get("fields", {})
        for field_name, old_field in sorted(old_fields.items()):
            if field_name not in new_fields:
                message = f"{short_name}.{field_name} removed"
                breaking.setdefault(message, []).append(path)
                continue
            new_field = new_fields[field_name]
            if old_field.get("type") != new_field.get("type"):
                message = (
                    f"{short_name}.{field_name} type changed: "
                    f"{old_field.get('type')} -> {new_field.get('type')}"
                )
                breaking.setdefault(message, []).append(path)
            old_required = bool(old_field.get("required"))
            new_required = bool(new_field.get("required"))
            if not old_required and new_required:
                message = f"{short_name}.{field_name} became required"
                breaking.setdefault(message, []).append(path)
            elif old_required and not new_required:
                message = f"{short_name}.{field_name} became optional"
                additive.setdefault(message, []).append(path)
            if old_field.get("validation_aliases") != new_field.get(
                "validation_aliases"
            ):
                message = (
                    f"{short_name}.{field_name} validation_aliases changed: "
                    f"{old_field.get('validation_aliases')} -> "
                    f"{new_field.get('validation_aliases')}"
                )
                breaking.setdefault(message, []).append(path)
            if old_field.get("serialization_alias") != new_field.get(
                "serialization_alias"
            ):
                message = (
                    f"{short_name}.{field_name} serialization_alias changed: "
                    f"{old_field.get('serialization_alias')} -> "
                    f"{new_field.get('serialization_alias')}"
                )
                breaking.setdefault(message, []).append(path)

        for field_name, new_field in sorted(new_fields.items()):
            if field_name in old_fields:
                continue
            if new_field.get("required"):
                message = f"{short_name}: required field {field_name} added"
                breaking.setdefault(message, []).append(path)
            else:
                message = f"{short_name}.{field_name} added (optional)"
                additive.setdefault(message, []).append(path)

    return _sorted_findings(breaking), _sorted_findings(additive)


def _rank_value(entry: dict) -> int:
    rank = entry.get("rank", 0)
    if isinstance(rank, dict):
        rank = rank.get("rank", 0)
    try:
        return int(rank)
    except (TypeError, ValueError):
        return 0


def _change_entries(changes_json: Path) -> list[dict]:
    payload = json.loads(changes_json.read_text())
    entries = payload.get("entries", {})
    if isinstance(entries, dict):
        return list(entries.values())
    return list(entries)


def _summarize_changes(changes_json: Path) -> tuple[int, int, int]:
    """Return (breaking, compatible, unknown) counts using AexPy ranks."""
    breaking = compatible = unknown = 0
    for entry in _change_entries(changes_json):
        rank = _rank_value(entry)
        if rank > 0:
            breaking += 1
        elif rank == 0:
            compatible += 1
        else:
            unknown += 1
    return breaking, compatible, unknown


def _entry_message(entry: dict) -> str:
    for key in ("message", "msg", "kind", "id"):
        value = entry.get(key)
        if isinstance(value, str) and value:
            return value
    return json.dumps(entry, sort_keys=True)


def _top_breaking_entries(
    changes_json: Path, *, limit: int | None = TOP_BREAKING_LIMIT
) -> list[dict]:
    breaking = [
        {"rank": _rank_value(entry), "message": _entry_message(entry)}
        for entry in _change_entries(changes_json)
        if _rank_value(entry) > 0
    ]
    breaking.sort(key=lambda item: (-item["rank"], item["message"]))
    if limit is None:
        return breaking
    return breaking[:limit]


def _unknown_entries(changes_json: Path) -> list[dict]:
    unknown = [
        {"rank": _rank_value(entry), "message": _entry_message(entry)}
        for entry in _change_entries(changes_json)
        if _rank_value(entry) < 0
    ]
    unknown.sort(key=lambda item: (item["rank"], item["message"]))
    return unknown


def _print_findings(title: str, findings: Findings) -> None:
    if not findings:
        return
    print(f"{title} ({len(findings)}):", flush=True)
    for message, paths in findings:
        print(f"  {message}", flush=True)
        print(f"      exposed via: {', '.join(paths)}", flush=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Compare the current branch public API against a published alpaca-py "
            "release using AexPy plus enum/model contract snapshots."
        )
    )
    parser.add_argument(
        "--against",
        metavar="VERSION",
        help="Published version to compare against (default: latest on PyPI)",
    )
    parser.add_argument(
        "--workdir",
        type=Path,
        help="Directory for wheels/JSON output (default: temporary directory)",
    )
    parser.add_argument(
        "--keep-workdir",
        action="store_true",
        help="Keep the work directory even when it was auto-created",
    )
    parser.add_argument(
        "--skip-contracts",
        action="store_true",
        help="Skip the public enum/model contract comparison",
    )
    parser.add_argument(
        "--skip-enums",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--allow-dump-errors",
        action="store_true",
        help="Do not fail when public modules fail to import during the snapshot",
    )
    parser.add_argument(
        "--fail-on-breaking",
        action="store_true",
        help="Exit with status 1 when a breaking change is reported",
    )
    parser.add_argument(
        "--fail-on-unknown",
        action="store_true",
        help="Exit with status 1 when AexPy reports unknown-ranked changes",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print progress, full AexPy view, and additive enum/model changes",
    )
    args = parser.parse_args(argv)
    skip_contracts = args.skip_contracts or args.skip_enums
    verbose = args.verbose

    against = args.against or _latest_pypi_version(PACKAGE_NAME)
    print(f"Comparing current tree against {PACKAGE_NAME}=={against}", flush=True)

    cleanup_workdir = False
    if args.workdir:
        workdir = args.workdir.resolve()
        workdir.mkdir(parents=True, exist_ok=True)
    else:
        workdir = Path(tempfile.mkdtemp(prefix="alpaca-aexpy-"))
        cleanup_workdir = not args.keep_workdir

    keep_after_failure = False
    try:
        wheels_dir = workdir / "wheels"
        venv_dir = workdir / "venv"
        api_old = workdir / "api_old.json"
        api_new = workdir / "api_new.json"
        changes = workdir / "changes.json"
        report = workdir / "report.json"
        snapshot_old = workdir / "public_old.json"
        snapshot_new = workdir / "public_new.json"

        python = _ensure_venv(venv_dir, verbose=verbose)
        _pip(python, "install", "-U", "pip", f"aexpy=={AEXPY_VERSION}", verbose=verbose)

        old_wheel = _download_release_wheel(
            python, against, wheels_dir, verbose=verbose
        )
        new_wheel = _build_current_wheel(wheels_dir, exclude=old_wheel, verbose=verbose)
        if verbose:
            print(f"Old wheel: {old_wheel.name}", flush=True)
            print(f"New wheel: {new_wheel.name}", flush=True)
            print("\n=== Extracting old API ===", flush=True)
        _extract(python, old_wheel, api_old, verbose=verbose)
        old_snapshot = (
            None
            if skip_contracts
            else _dump_public_api(
                python,
                snapshot_old,
                workdir,
                _wheel_version(old_wheel),
                verbose=verbose,
            )
        )

        if verbose:
            print("\n=== Extracting new API ===", flush=True)
        _extract(python, new_wheel, api_new, verbose=verbose)
        new_snapshot = (
            None
            if skip_contracts
            else _dump_public_api(
                python,
                snapshot_new,
                workdir,
                _wheel_version(new_wheel),
                verbose=verbose,
            )
        )

        if old_snapshot is not None and new_snapshot is not None:
            if not args.allow_dump_errors:
                _require_no_dump_errors(old_snapshot)
                _require_no_dump_errors(new_snapshot)

        if verbose:
            print("\n=== Diffing ===", flush=True)
        _aexpy(
            python, "diff", str(api_old), str(api_new), str(changes), verbose=verbose
        )
        # `aexpy report` echoes the whole rendered report to stderr; `aexpy view`
        # below prints the same text on stdout, so keep only the latter copy.
        _aexpy(
            python,
            "report",
            str(changes),
            str(report),
            echo_stderr=False,
            verbose=verbose,
        )

        if verbose:
            print("\n=== Report ===", flush=True)
            _aexpy(python, "view", str(report), verbose=verbose)

        enum_breaking: Findings = []
        model_breaking: Findings = []
        if old_snapshot is not None and new_snapshot is not None:
            enum_breaking, enum_added = _compare_enums(old_snapshot, new_snapshot)
            new_enum_paths = sorted(
                set(new_snapshot.get("enums", {})) - set(old_snapshot.get("enums", {}))
            )
            model_breaking, model_added = _compare_models(old_snapshot, new_snapshot)
            new_model_paths = sorted(
                set(new_snapshot.get("models", {}))
                - set(old_snapshot.get("models", {}))
            )
            if verbose:
                print("\n=== Enum membership ===", flush=True)
                if enum_breaking:
                    _print_findings("Breaking", enum_breaking)
                else:
                    print(
                        "No members/targets removed or changed on existing enums.",
                        flush=True,
                    )
                if enum_added:
                    print(f"Added members ({len(enum_added)}):", flush=True)
                    for message, _ in enum_added:
                        print(f"  {message}", flush=True)
                if new_enum_paths:
                    print(f"Newly exported enums ({len(new_enum_paths)}):", flush=True)
                    for path in new_enum_paths:
                        print(f"  {path}", flush=True)

                print("\n=== Model field contracts ===", flush=True)
                if model_breaking:
                    _print_findings("Breaking", model_breaking)
                else:
                    print(
                        "No field/alias/target breakages on existing models.",
                        flush=True,
                    )
                if model_added:
                    print(
                        f"Compatible field changes ({len(model_added)}):",
                        flush=True,
                    )
                    for message, _ in model_added:
                        print(f"  {message}", flush=True)
                if new_model_paths:
                    print(
                        f"Newly exported models ({len(new_model_paths)}):",
                        flush=True,
                    )
                    for path in new_model_paths:
                        print(f"  {path}", flush=True)
            else:
                _print_findings("Enum breakings", enum_breaking)
                _print_findings("Model breakings", model_breaking)

        breaking, compatible, unknown = _summarize_changes(changes)

        if verbose:
            top_breaking = _top_breaking_entries(changes)
            if top_breaking:
                print(
                    f"\nTop AexPy breakings (up to {TOP_BREAKING_LIMIT}):",
                    flush=True,
                )
                for entry in top_breaking:
                    print(
                        f"  [rank={entry['rank']}] {entry['message']}",
                        flush=True,
                    )
        else:
            all_breaking = _top_breaking_entries(changes, limit=None)
            if all_breaking:
                print(f"\nAexPy breakings ({len(all_breaking)}):", flush=True)
                for entry in all_breaking:
                    print(
                        f"  [rank={entry['rank']}] {entry['message']}",
                        flush=True,
                    )

        print(
            f"\nSummary vs {PACKAGE_NAME}=={against}: "
            f"aexpy_breaking={breaking} aexpy_compatible={compatible} "
            f"aexpy_unknown={unknown} enum_breaking={len(enum_breaking)} "
            f"model_breaking={len(model_breaking)}",
            flush=True,
        )

        failed = False
        if args.fail_on_breaking and (breaking or enum_breaking or model_breaking):
            failed = True
        if args.fail_on_unknown and unknown:
            failed = True
            if not verbose:
                unknowns = _unknown_entries(changes)
                if unknowns:
                    print(f"\nAexPy unknown ({len(unknowns)}):", flush=True)
                    for entry in unknowns:
                        print(
                            f"  [rank={entry['rank']}] {entry['message']}",
                            flush=True,
                        )

        show_artifacts = verbose or failed or bool(args.workdir) or args.keep_workdir
        if show_artifacts:
            print(f"Artifacts: {workdir}", flush=True)
            for artifact in (
                api_old,
                api_new,
                changes,
                report,
                snapshot_old,
                snapshot_new,
            ):
                if artifact.exists():
                    print(f"  {artifact}", flush=True)

        if failed:
            keep_after_failure = True
            return 1
        return 0
    except Exception:
        keep_after_failure = True
        raise
    finally:
        if cleanup_workdir and not keep_after_failure:
            shutil.rmtree(workdir, ignore_errors=True)
        elif cleanup_workdir and keep_after_failure:
            print(f"Kept workdir after failure: {workdir}", flush=True)
        elif not args.workdir:
            print(f"Kept workdir: {workdir}", flush=True)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ToolError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
