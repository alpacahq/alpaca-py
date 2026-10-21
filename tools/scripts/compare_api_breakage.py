#!/usr/bin/env python3
"""Compare the current checkout's public API against a published alpaca-py release.

Uses AexPy (https://github.com/StardustDL/aexpy) to extract APIs from wheels and
report breaking / alias / additive changes. AexPy tracks alias targets rather than
enum membership or Pydantic field metadata, and it leaves ``returnType`` empty for
annotations it cannot resolve (including ``RawData`` unions). This script
additionally compares:

* every publicly exported enum's ``name -> value`` map and defining target
* every publicly exported Pydantic model's field contract (type, requiredness,
  validation/serialization aliases) and defining target
* public callable ``returnAnnotation`` strings when AexPy did not already report
  a resolved return-type change, and when AexPy ranked that change compatible
  but a ``dict``, ``Mapping``, or ``MutableMapping`` key changed or a ``RawData``
  / ``List[RawData]`` member was dropped. A narrower return (fewer union
  members, or a subclass of the old type), or a ``None`` return that gains a
  value, is listed under ``--verbose`` and does not fail the check, except
  dropping ``RawData`` (``dict[str, Any]``) or ``List[RawData]``
  (``list[dict[str, Any]]``)

Examples:
  tools/scripts/compare_api_breakage.py
  tools/scripts/compare_api_breakage.py --against 0.43.5
  tools/scripts/compare_api_breakage.py --baseline-ref origin/master \\
      --workdir /tmp/aexpy-alpaca
  tools/scripts/compare_api_breakage.py --workdir /tmp/aexpy-alpaca \\
      --fail-on-breaking --fail-on-unknown
"""

from __future__ import annotations

import argparse
import json
import os
import re
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
# AexPy ranks these as breaking only because a subclass overriding the method
# with the old signature would reject the new argument. Callers are unaffected,
# and SDK clients are used rather than subclassed, so they count as compatible.
CALLER_COMPATIBLE_KINDS = frozenset({"AddOptionalParameter"})

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
    exact = [path for path in matches if _versions_equal(_wheel_version(path), version)]
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


def _resolve_ref(git: str, ref: str, *, verbose: bool = True) -> str:
    result = _run(
        [git, "rev-parse", "--verify", f"{ref}^{{commit}}"],
        cwd=REPOSITORY_ROOT,
        verbose=verbose,
        echo_stdout=False,
        echo_cmd=False,
    )
    sha = result.stdout.strip()
    if not sha:
        raise ToolError(f"could not resolve git ref: {ref}")
    return sha


def _build_ref_wheel(ref: str, cache_root: Path, *, verbose: bool = True) -> Path:
    """Build (and cache) a wheel from an arbitrary git ref via a throwaway worktree.

    The wheel is cached under ``cache_root/<sha>`` so repeated iterations against a
    stable baseline (for example ``origin/master``) reuse it instead of rebuilding. The
    worktree is detached at the resolved commit so poetry-dynamic-versioning stamps
    the ref's own version, then removed once the wheel is built.
    """
    git = shutil.which("git")
    if not git:
        raise ToolError("git is required to build a baseline wheel from a ref")
    poetry = shutil.which("poetry")
    if not poetry:
        raise ToolError("poetry is required to build a baseline wheel from a ref")

    sha = _resolve_ref(git, ref, verbose=verbose)
    wheel_dir = cache_root / sha
    cached = sorted(wheel_dir.glob("*.whl"))
    if cached:
        print(f"Reusing cached baseline wheel for {ref} ({sha[:12]})", flush=True)
        return cached[0]

    wheel_dir.mkdir(parents=True, exist_ok=True)
    worktree = cache_root / f".worktree-{sha[:12]}"
    print(
        f"Building baseline wheel from {ref} ({sha[:12]}); first run only, "
        "this can take a minute...",
        flush=True,
    )
    # Clear a leftover directory from an interrupted run. `add --force` reclaims
    # a registration whose directory is already gone. Do not `git worktree prune`:
    # with no `--expire` it is repo-wide and drops every unlocked worktree whose
    # directory is missing, including ones this script did not create.
    # `remove --force` is not a substitute for this up-front step: on a first run
    # the path is not a worktree, and `_run` still prints that error.
    shutil.rmtree(worktree, ignore_errors=True)
    _run(
        [git, "worktree", "add", "--force", "--detach", str(worktree), sha],
        cwd=REPOSITORY_ROOT,
        verbose=verbose,
    )
    try:
        _run(
            [poetry, "build", "-f", "wheel", "-o", str(wheel_dir)],
            cwd=worktree,
            verbose=verbose,
        )
    finally:
        _run(
            [git, "worktree", "remove", "--force", str(worktree)],
            cwd=REPOSITORY_ROOT,
            check=False,
            verbose=verbose,
            echo_stderr=False,
        )
    built = sorted(wheel_dir.glob("*.whl"))
    if not built:
        raise ToolError(f"poetry build produced no wheel for ref {ref}")
    return built[0]


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


# inspect.signature stringifies typing aliases differently from builtins
# (``typing.List[int]`` vs ``list[int]``, ``Optional[str]`` vs ``str | None``).
# Both wheels are extracted by one interpreter, but source can mix the forms.
_ANNOTATION_NAMES = {
    "Any": "Any",
    "List": "list",
    "Dict": "dict",
    "Set": "set",
    "FrozenSet": "frozenset",
    "Tuple": "tuple",
    "Type": "type",
    "Optional": "Optional",
    "Union": "Union",
    "typing.Any": "Any",
    "typing.List": "list",
    "typing.Dict": "dict",
    "typing.Set": "set",
    "typing.FrozenSet": "frozenset",
    "typing.Tuple": "tuple",
    "typing.Type": "type",
    "typing.Optional": "Optional",
    "typing.Union": "Union",
    "typing.Iterable": "collections.abc.Iterable",
    "typing.Iterator": "collections.abc.Iterator",
    "typing.Sequence": "collections.abc.Sequence",
    "typing.Mapping": "collections.abc.Mapping",
    "typing.MutableMapping": "collections.abc.MutableMapping",
    "typing.MutableSequence": "collections.abc.MutableSequence",
    "typing.Callable": "collections.abc.Callable",
    "typing.Generator": "collections.abc.Generator",
    "typing.Awaitable": "collections.abc.Awaitable",
    "typing.Coroutine": "collections.abc.Coroutine",
    "typing.AsyncIterator": "collections.abc.AsyncIterator",
    "typing.AsyncIterable": "collections.abc.AsyncIterable",
    "NoneType": "None",
    "types.NoneType": "None",
    "builtins.NoneType": "None",
}
_BUILTIN_NAMES = {
    "list",
    "dict",
    "set",
    "frozenset",
    "tuple",
    "type",
    "int",
    "str",
    "bool",
    "float",
    "bytes",
    "object",
    "complex",
}


def _canonicalize_annotation_name(name: str) -> str:
    if name in _ANNOTATION_NAMES:
        return _ANNOTATION_NAMES[name]
    if name.startswith("builtins."):
        bare = name.removeprefix("builtins.")
        if bare in _BUILTIN_NAMES or bare == "None":
            return "None" if bare == "None" else bare
    return name


def _split_top_level(text: str, separator: str) -> list[str]:
    """Split on ``separator`` outside any ``[...]`` nesting."""
    parts: list[str] = []
    depth = 0
    start = 0
    for index, char in enumerate(text):
        if char == "[":
            depth += 1
        elif char == "]":
            depth = max(0, depth - 1)
        elif char == separator and depth == 0:
            parts.append(text[start:index].strip())
            start = index + 1
    parts.append(text[start:].strip())
    return [part for part in parts if part]


def _split_top_level_union(text: str) -> list[str]:
    return _split_top_level(text, "|")


def _union_of(parts: list[str]) -> str:
    flat: list[str] = []
    for part in parts:
        for item in _split_top_level_union(part):
            if item not in flat:
                flat.append(item)
    if len(flat) == 1:
        return flat[0]
    return " | ".join(sorted(flat))


def _tokenize_annotation(text: str) -> list[str]:
    tokens: list[str] = []
    index = 0
    length = len(text)
    while index < length:
        char = text[index]
        if char.isspace():
            index += 1
            continue
        if char in "[]|,":
            tokens.append(char)
            index += 1
            continue
        if text.startswith("...", index):
            tokens.append("...")
            index += 3
            continue
        if char in "'\"":
            end = text.find(char, index + 1)
            if end == -1:
                raise ValueError("unterminated string literal")
            tokens.append(text[index : end + 1])
            index = end
            if index < length:
                index += 1
            continue
        if char.isidentifier() or char in "._":
            start = index
            index += 1
            while index < length and (text[index].isalnum() or text[index] in "._"):
                index += 1
            tokens.append(text[start:index])
            continue
        raise ValueError(f"unsupported annotation character {char!r}")
    return tokens


class _AnnotationParser:
    def __init__(self, tokens: list[str]) -> None:
        self.tokens = tokens
        self.index = 0

    def peek(self) -> str | None:
        if self.index >= len(self.tokens):
            return None
        return self.tokens[self.index]

    def eat(self, expected: str | None = None) -> str:
        token = self.peek()
        if token is None or (expected is not None and token != expected):
            raise ValueError(f"expected {expected!r}, found {token!r}")
        self.index += 1
        return token

    def parse(self) -> str:
        parsed = self.parse_union()
        if self.peek() is not None:
            raise ValueError(f"trailing annotation token {self.peek()!r}")
        return parsed

    def parse_union(self) -> str:
        parts = [self.parse_term()]
        while self.peek() == "|":
            self.eat("|")
            parts.append(self.parse_term())
        return _union_of(parts)

    def parse_term(self) -> str:
        if self.peek() == "[":
            return self.parse_bracket_list()
        if self.peek() == "...":
            self.eat("...")
            return "..."
        name = _canonicalize_annotation_name(self.eat())
        if self.peek() != "[":
            return name
        self.eat("[")
        args = self.parse_arg_list()
        self.eat("]")
        return self.apply_generic(name, args)

    def parse_arg_list(self) -> list[str]:
        if self.peek() == "]":
            return []
        args = [self.parse_arg()]
        while self.peek() == ",":
            self.eat(",")
            if self.peek() == "]":
                break
            args.append(self.parse_arg())
        return args

    def parse_arg(self) -> str:
        if self.peek() == "[":
            return self.parse_bracket_list()
        return self.parse_union()

    def parse_bracket_list(self) -> str:
        self.eat("[")
        args = self.parse_arg_list()
        self.eat("]")
        return "[" + ", ".join(args) + "]"

    def apply_generic(self, name: str, args: list[str]) -> str:
        if name == "Optional":
            if len(args) != 1:
                raise ValueError("Optional expects one argument")
            return _union_of([args[0], "None"])
        if name == "Union":
            return _union_of(args)
        if not args:
            return name
        return f"{name}[{', '.join(args)}]"


# inspect.signature sometimes stores a live object instead of a type. Its repr
# includes the process address, which changes on every extract.
_OBJECT_ADDRESS = re.compile(r" at 0x[0-9a-fA-F]+")
# A bare class is stored as str(cls), e.g. "<class 'alpaca.trading.models.Clock'>".
# Unions stringify the same class without that wrapper, so members only match
# after the wrapper is removed. The tokenizer rejects "<".
_CLASS_REPR = re.compile(r"<class '([^']+)'>")
# RawData = Dict[str, Any]. List endpoints annotate the raw branch as
# List[RawData], which normalizes to list[dict[str, Any]]. Dropping either
# means raw_data=True stopped being honored.
_RAW_DATA_ANNOTATION = "dict[str, Any]"
_RAW_DATA_LIST_ANNOTATION = f"list[{_RAW_DATA_ANNOTATION}]"


def _normalize_type_annotation(annotation: str) -> str:
    """Canonical form for equivalent typing spellings.

    Unparseable text falls back to collapsed whitespace so a real change is
    still reported. Object addresses are stripped first, then ``<class '...'>``
    wrappers are unwrapped so a bare class matches that class inside a union.
    """
    text = _CLASS_REPR.sub(r"\1", _OBJECT_ADDRESS.sub("", " ".join(annotation.split())))
    if not text:
        return ""
    try:
        return _AnnotationParser(_tokenize_annotation(text)).parse()
    except ValueError:
        return text


def _is_public_callable_id(api_id: str) -> bool:
    return bool(api_id) and not any(part.startswith("_") for part in api_id.split("."))


def _function_index(api: dict) -> dict[str, dict]:
    functions = api.get("functions") or {}
    if isinstance(functions, dict):
        return {
            key: value for key, value in functions.items() if isinstance(value, dict)
        }
    indexed = {}
    for entry in functions:
        if isinstance(entry, dict) and entry.get("id"):
            indexed[entry["id"]] = entry
    return indexed


def _change_return_ids(entry: dict) -> list[str]:
    """Function ids named by one AexPy ``ChangeReturnType`` entry."""
    kind = entry.get("kind") or ""
    message = entry.get("message") or ""
    if kind != "ChangeReturnType" and not message.startswith("Change return type ("):
        return []
    ids: list[str] = []
    for side in ("old", "new"):
        payload = entry.get(side)
        if isinstance(payload, dict) and isinstance(payload.get("id"), str):
            ids.append(payload["id"])
    if message.startswith("Change return type (") and "):" in message:
        ids.append(message.split("(", 1)[1].split("):", 1)[0])
    return ids


def _reported_return_type_ids(entries: list[dict]) -> set[str]:
    """Function ids whose return type AexPy already resolved and diffed."""
    reported: set[str] = set()
    for entry in entries:
        reported.update(_change_return_ids(entry))
    return reported


def _aexpy_compatible_return_ids(entries: list[dict]) -> set[str]:
    """ChangeReturnType ids AexPy explicitly ranked compatible (rank 0).

    A missing rank is not compatible: the annotation check then stays out of
    the way, which is what an entry without a rank used to mean. An id that
    also appears in a rank above 0 is already failing the build.
    """
    grouped: dict[str, list[dict]] = {}
    for entry in entries:
        for api_id in _change_return_ids(entry):
            grouped.setdefault(api_id, []).append(entry)
    return {
        api_id
        for api_id, group in grouped.items()
        if group and all("rank" in entry and _rank_value(entry) == 0 for entry in group)
    }


def _drops_raw_data(old_members: set[str], new_members: set[str]) -> bool:
    """True when a removed union member is ``RawData`` or ``List[RawData]``."""
    removed = old_members - new_members
    return bool(removed.intersection({_RAW_DATA_ANNOTATION, _RAW_DATA_LIST_ANNOTATION}))


def _class_ancestry(api: dict) -> dict[str, set[str]]:
    """Map each extracted class id to its AexPy MRO ids (itself included)."""
    classes = api.get("classes") or {}
    entries = classes.values() if isinstance(classes, dict) else classes
    ancestry: dict[str, set[str]] = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
            continue
        mros = entry.get("mros") or []
        ancestry[entry["id"]] = {entry["id"], *(m for m in mros if isinstance(m, str))}
    return ancestry


def _split_generic(member: str) -> tuple[str, list[str]] | None:
    """``list[a.B]`` -> ``("list", ["a.B"])``; ``None`` for a non-generic member."""
    bracket = member.find("[")
    if bracket <= 0 or not member.endswith("]"):
        return None
    return member[:bracket], _split_top_level(member[bracket + 1 : -1], ",")


def _annotation_drops_raw_data(new: str, old: str) -> bool:
    """True when ``new`` removes a ``RawData`` or ``List[RawData]`` ``old`` had.

    Checked at every union, including inside a generic argument, so a resolved
    return AexPy ranked compatible still fails when ``raw_data=True`` stopped
    being honored. Only generic arguments with one old and one new member of
    the same origin are walked. That avoids pairing unrelated arms that merely
    share ``list`` or ``Mapping``. This is not the full narrowing check, which
    would also reject callable-parameter changes AexPy correctly accepts.
    """
    old_members = _split_top_level_union(old)
    new_members = _split_top_level_union(new)
    if _drops_raw_data(set(old_members), set(new_members)):
        return True
    if len(old_members) == 1 and len(new_members) == 1:
        return _generic_args_drop_raw_data(new_members[0], old_members[0])
    old_by_origin: dict[str, list[str]] = {}
    new_by_origin: dict[str, list[str]] = {}
    for member in old_members:
        generic = _split_generic(member)
        if generic is not None:
            old_by_origin.setdefault(generic[0], []).append(member)
    for member in new_members:
        generic = _split_generic(member)
        if generic is not None:
            new_by_origin.setdefault(generic[0], []).append(member)
    for origin, old_group in old_by_origin.items():
        new_group = new_by_origin.get(origin)
        if (
            new_group
            and len(old_group) == 1
            and len(new_group) == 1
            and _generic_args_drop_raw_data(new_group[0], old_group[0])
        ):
            return True
    return False


def _generic_args_drop_raw_data(new: str, old: str) -> bool:
    new_generic = _split_generic(new)
    old_generic = _split_generic(old)
    if (
        new_generic is None
        or old_generic is None
        or new_generic[0] != old_generic[0]
        or len(new_generic[1]) != len(old_generic[1])
    ):
        return False
    return any(
        _annotation_drops_raw_data(new_arg, old_arg)
        for new_arg, old_arg in zip(new_generic[1], old_generic[1])
    )


# Generics whose arguments only flow out to a caller reading an SDK result,
# so ``list[Sub]`` narrows ``list[Base]``. Mutable containers are invariant to
# a type checker, but callers read these results rather than writing base
# instances back. Callable parameters and Generator/Coroutine send types flow
# in (contravariant), so anything not listed needs an exact match.
# ``dict`` and ``Mapping`` are included for their values only. Their keys are
# invariant: callers look values up with ``result[key]``, and a narrower key
# rejects keys the old return type accepted. See ``_MAPPING_GENERICS``.
_COVARIANT_GENERICS = frozenset(
    {
        "list",
        "tuple",
        "set",
        "frozenset",
        "dict",
        "type",
        "collections.abc.Iterable",
        "collections.abc.Iterator",
        "collections.abc.Sequence",
        "collections.abc.Mapping",
        "collections.abc.AsyncIterable",
        "collections.abc.AsyncIterator",
        "collections.abc.Awaitable",
    }
)
# Key parameter is invariant; the value parameter may narrow.
# ``MutableMapping`` is not in ``_COVARIANT_GENERICS``, so the annotation
# fallback already rejects every change to it. AexPy still compares its
# arguments covariantly when mypy resolves the return, so the veto below
# includes it.
_MAPPING_GENERICS = frozenset({"dict", "collections.abc.Mapping"})
_INVARIANT_KEY_GENERICS = _MAPPING_GENERICS | {"collections.abc.MutableMapping"}
# A top-level ``Any`` or ``object`` return accepts any narrower type. Only the
# top level: inside ``dict[str, Any]`` that would hide a RawData change.
_TOP_TYPES = frozenset({"Any", "object"})


def _mapping_key_differs(new_args: list[str], old_args: list[str]) -> bool:
    """Mapping keys are invariant: ``result[old_key]`` must still type-check."""
    return len(new_args) != 2 or new_args[0] != old_args[0]


def _is_subtype(new: str, old: str, ancestry: dict[str, set[str]]) -> bool:
    """True when every value of normalized type ``new`` is also an ``old``.

    Classes follow the new wheel's MRO. Arguments of ``_COVARIANT_GENERICS``
    are compared covariantly, except mapping keys, which must match exactly.
    Any other generic needs an exact match.
    """
    if new == old:
        return True
    new_generic = _split_generic(new)
    old_generic = _split_generic(old)
    if new_generic is None and old_generic is None:
        return old in ancestry.get(new, ())
    if new_generic is None or old_generic is None:
        return False
    (new_origin, new_args), (old_origin, old_args) = new_generic, old_generic
    if (
        new_origin != old_origin
        or new_origin not in _COVARIANT_GENERICS
        or len(new_args) != len(old_args)
    ):
        return False
    if new_origin in _MAPPING_GENERICS:
        if _mapping_key_differs(new_args, old_args):
            return False
        return _union_narrows(new_args[1], old_args[1], ancestry)
    return all(
        _union_narrows(new_arg, old_arg, ancestry)
        for new_arg, old_arg in zip(new_args, old_args)
    )


def _union_narrows(new: str, old: str, ancestry: dict[str, set[str]]) -> bool:
    """True when ``new`` narrows ``old`` without dropping a RawData branch.

    The RawData guard applies at every union level, so dropping the raw branch
    inside a generic (``Iterator[List[RawData] | List[Model]]`` ->
    ``Iterator[List[Model]]``) is not a narrowing either.
    """
    old_members = _split_top_level_union(old)
    new_members = _split_top_level_union(new)
    if _drops_raw_data(set(old_members), set(new_members)):
        return False
    return all(
        any(_is_subtype(member, old_member, ancestry) for old_member in old_members)
        for member in new_members
    )


def _bracket_items(text: str) -> list[str] | None:
    """``[int, str]`` -> ``["int", "str"]``; None when ``text`` is not a list."""
    if len(text) < 2 or not text.startswith("[") or not text.endswith("]"):
        return None
    inner = text[1:-1].strip()
    if not inner:
        return []
    return _split_top_level(inner, ",")


def _key_relation(new: str, old: str, ancestry: dict[str, set[str]]) -> str:
    """How ``new`` relates to ``old`` for mapping-key invariance.

    ``ok``: same keys along the shared generic spine, including subclass values.
    ``break``: a ``dict`` / ``Mapping`` / ``MutableMapping`` key differs.
    ``unrelated``: no shared spine, so this pair cannot explain a union arm.

    AexPy 0.4.3 compares every generic argument covariantly, including these
    keys. This walk only looks for that disagreement. Callable parameter
    widening and other caller-safe changes stay ``ok`` or ``unrelated``.

    An ``old`` branch of ``Any``/``object`` matches here at any depth, not
    just the top level like ``_TOP_TYPES`` elsewhere: a mapping value typed
    ``object`` already accepted anything, so no key disagreement can hide
    behind it. The RawData veto this skips for the overall annotation is
    checked separately by ``_annotation_drops_raw_data``.
    """
    if new == old or old in ancestry.get(new, ()):
        return "ok"
    if old in _TOP_TYPES:
        return "ok"
    new_params = _bracket_items(new)
    old_params = _bracket_items(old)
    if new_params is not None or old_params is not None:
        if (
            new_params is None
            or old_params is None
            or len(new_params) != len(old_params)
        ):
            return "unrelated"
        relations = [
            _key_relation(item, other, ancestry)
            for item, other in zip(new_params, old_params)
        ]
        if any(relation == "break" for relation in relations):
            return "break"
        if "unrelated" in relations:
            return "unrelated"
        return "ok"
    new_members = _split_top_level_union(new)
    old_members = _split_top_level_union(old)
    if len(new_members) != 1 or len(old_members) != 1:
        saw_break = False
        saw_unrelated = False
        for new_member in new_members:
            relations = [
                _key_relation(new_member, old_member, ancestry)
                for old_member in old_members
            ]
            if "ok" in relations:
                continue
            if "break" in relations:
                saw_break = True
            else:
                saw_unrelated = True
        if saw_break:
            return "break"
        return "unrelated" if saw_unrelated else "ok"
    new_generic = _split_generic(new)
    old_generic = _split_generic(old)
    if (
        new_generic is None
        or old_generic is None
        or new_generic[0] != old_generic[0]
        or len(new_generic[1]) != len(old_generic[1])
    ):
        return "unrelated"
    origin, new_args = new_generic
    old_args = old_generic[1]
    if origin in _INVARIANT_KEY_GENERICS:
        if _mapping_key_differs(new_args, old_args):
            return "break"
        return _key_relation(new_args[1], old_args[1], ancestry)
    relations = [
        _key_relation(arg, other, ancestry) for arg, other in zip(new_args, old_args)
    ]
    if any(relation == "break" for relation in relations):
        return "break"
    # Sharing an outer container does not make unrelated arguments a valid
    # union match: list[int] cannot explain list[Mapping[Sub, str]].
    if "unrelated" in relations:
        return "unrelated"
    return "ok"


def _mapping_key_breaks(new: str, old: str, ancestry: dict[str, set[str]]) -> bool:
    """True when a mapping key changed inside an otherwise compatible return."""
    return _key_relation(new, old, ancestry) == "break"


def _compare_return_annotations(
    old_api: dict,
    new_api: dict,
    already_reported: set[str] | None = None,
    aexpy_compatible: set[str] | None = None,
) -> tuple[Findings, Findings]:
    """Return ``(breaking, compatible)`` public return-annotation changes.

    AexPy only emits ``ChangeReturnType`` when mypy filled ``returnType`` on
    both sides. Unions that include ``dict[str, Any]`` stay null, so the
    stored ``returnAnnotation`` is compared here. Adding an annotation where
    the baseline had none is left alone. Spellings that normalize to the same
    type are not changes.

    A resolved change AexPy ranked breaking is left to AexPy. A resolved
    change it ranked compatible is left alone too, except for two vetoes:
    a mapping key changed (AexPy 0.4.3 compares that key covariantly, and
    ``result[old_key]`` then fails to type-check), or a ``RawData`` /
    ``List[RawData]`` member was dropped, including inside a generic. The full
    annotation check is not re-run for those ids. That check rejects
    callable-parameter changes AexPy correctly treats as compatible.

    A narrower return is compatible for callers: AexPy 0.4.3 ranks that
    covariance ``Compatible`` in ``ChangeReturnType``. Those are reported as
    compatible and do not fail the check. Narrower means every new union member
    is an old member or a subclass of one, also inside covariant generic
    arguments (``list[Account]`` -> ``list[AccountExtended]``), or the old
    return was a top-level ``Any``/``object``. ``dict`` and ``Mapping`` keys
    are compared exactly (``Mapping[Base, V]`` -> ``Mapping[Sub, V]`` is
    breaking); only their values may narrow. Dropping ``dict[str, Any]``
    (``RawData``) or ``list[dict[str, Any]]`` (``List[RawData]``) stays
    breaking at any nesting level (``Iterator[List[RawData] | ...]``), because
    in this SDK it means ``raw_data=True`` stopped being honored.

    A ``None`` return that gains a value is also compatible. Type checkers
    reject using the result of a ``None`` return, so callers could only
    discard it.
    """
    reported = already_reported or set()
    compatible_resolved = reported & (aexpy_compatible or set())
    ancestry = _class_ancestry(new_api)
    old_functions = _function_index(old_api)
    new_functions = _function_index(new_api)
    breaking: dict[str, list[str]] = {}
    compatible: dict[str, list[str]] = {}

    for api_id in sorted(set(old_functions) & set(new_functions)):
        if not _is_public_callable_id(api_id):
            continue
        # Rank > 0 is already failing. Rank 0 still needs the vetoes below.
        if api_id in reported and api_id not in compatible_resolved:
            continue
        old_entry = old_functions[api_id]
        new_entry = new_functions[api_id]
        if old_entry.get("private") or new_entry.get("private"):
            continue
        old_annotation = old_entry.get("returnAnnotation") or ""
        if not str(old_annotation).strip():
            continue
        new_annotation = new_entry.get("returnAnnotation") or ""
        old_normalized = _normalize_type_annotation(str(old_annotation))
        new_normalized = _normalize_type_annotation(str(new_annotation))
        if api_id in compatible_resolved:
            if old_normalized == new_normalized:
                continue
            short_name = api_id.rsplit(".", 1)[-1]
            if _annotation_drops_raw_data(new_normalized, old_normalized):
                message = (
                    f"{short_name} return type dropped RawData: "
                    f"{old_normalized} -> {new_normalized}"
                )
                breaking.setdefault(message, []).append(api_id)
            elif _mapping_key_breaks(new_normalized, old_normalized, ancestry):
                message = (
                    f"{short_name} return type changed a mapping key: "
                    f"{old_normalized} -> {new_normalized}"
                )
                breaking.setdefault(message, []).append(api_id)
            continue
        if old_normalized == new_normalized:
            continue
        old_members = set(_split_top_level_union(old_normalized))
        new_members = set(_split_top_level_union(new_normalized))
        # Same members in an order the parser could not canonicalize.
        if new_members and new_members == old_members:
            continue
        short_name = api_id.rsplit(".", 1)[-1]
        if old_normalized == "None" and new_members:
            message = (
                f"{short_name} return type gained a value: "
                f"{old_normalized} -> {new_normalized}"
            )
            compatible.setdefault(message, []).append(api_id)
            continue
        # An empty new annotation is not a narrowing: the return became untyped.
        if (
            new_members
            and (
                old_members & _TOP_TYPES
                or _union_narrows(new_normalized, old_normalized, ancestry)
            )
            and not _drops_raw_data(old_members, new_members)
        ):
            message = (
                f"{short_name} return type narrowed: "
                f"{old_normalized} -> {new_normalized}"
            )
            compatible.setdefault(message, []).append(api_id)
            continue
        shown_new = new_normalized or "<unannotated>"
        message = f"{short_name} return type changed: {old_normalized} -> {shown_new}"
        breaking.setdefault(message, []).append(api_id)

    return _sorted_findings(breaking), _sorted_findings(compatible)


def _rank_value(entry: dict) -> int:
    rank = entry.get("rank", 0)
    if isinstance(rank, dict):
        rank = rank.get("rank", 0)
    try:
        return int(rank)
    except (TypeError, ValueError):
        return 0


def _is_caller_compatible(entry: dict) -> bool:
    return entry.get("kind") in CALLER_COMPATIBLE_KINDS and _rank_value(entry) > 0


def _effective_rank(entry: dict) -> int:
    return 0 if _is_caller_compatible(entry) else _rank_value(entry)


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
        rank = _effective_rank(entry)
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
        if _effective_rank(entry) > 0
    ]
    breaking.sort(key=lambda item: (-item["rank"], item["message"]))
    if limit is None:
        return breaking
    return breaking[:limit]


def _caller_compatible_entries(changes_json: Path) -> list[dict]:
    """AexPy breakings reclassified as compatible, for the verbose report."""
    entries = [
        {"rank": _rank_value(entry), "message": _entry_message(entry)}
        for entry in _change_entries(changes_json)
        if _is_caller_compatible(entry)
    ]
    entries.sort(key=lambda item: item["message"])
    return entries


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
            "release using AexPy plus enum, model, and return-annotation checks."
        )
    )
    parser.add_argument(
        "--against",
        metavar="VERSION",
        help="Published version to compare against (default: latest on PyPI)",
    )
    parser.add_argument(
        "--baseline-ref",
        metavar="GITREF",
        help=(
            "Compare against a git ref (e.g. origin/master) instead of a PyPI release. "
            "The ref's wheel is built in a throwaway worktree and cached in the "
            "workdir for reuse across iterations. Mutually exclusive with --against."
        ),
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

    if args.baseline_ref and args.against:
        parser.error("--baseline-ref and --against are mutually exclusive")

    baseline_ref = args.baseline_ref
    if baseline_ref:
        against_label = f"ref {baseline_ref}"
        print(f"Comparing current tree against git {against_label}", flush=True)
    else:
        against = args.against or _latest_pypi_version(PACKAGE_NAME)
        against_label = f"{PACKAGE_NAME}=={against}"
        print(f"Comparing current tree against {against_label}", flush=True)

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

        if not verbose:
            print(
                f"Preparing comparison environment (AexPy {AEXPY_VERSION})...",
                flush=True,
            )
        python = _ensure_venv(venv_dir, verbose=verbose)
        _pip(python, "install", "-U", "pip", f"aexpy=={AEXPY_VERSION}", verbose=verbose)

        if baseline_ref:
            old_wheel = _build_ref_wheel(
                baseline_ref, workdir / "baseline", verbose=verbose
            )
        else:
            if not verbose:
                print(f"Downloading {PACKAGE_NAME}=={against} wheel...", flush=True)
            old_wheel = _download_release_wheel(
                python, against, wheels_dir, verbose=verbose
            )
        if not verbose:
            print("Building current-tree wheel...", flush=True)
        new_wheel = _build_current_wheel(wheels_dir, exclude=old_wheel, verbose=verbose)
        if verbose:
            print(f"Old wheel: {old_wheel.name}", flush=True)
            print(f"New wheel: {new_wheel.name}", flush=True)
            print("\n=== Extracting old API ===", flush=True)
        else:
            print("Extracting baseline API...", flush=True)
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
        else:
            print("Extracting current API...", flush=True)
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
        else:
            print("Diffing APIs...", flush=True)
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

        change_entries = _change_entries(changes)
        return_breaking, return_compatible = _compare_return_annotations(
            json.loads(api_old.read_text()),
            json.loads(api_new.read_text()),
            already_reported=_reported_return_type_ids(change_entries),
            aexpy_compatible=_aexpy_compatible_return_ids(change_entries),
        )
        if verbose:
            print("\n=== Return annotations ===", flush=True)
            if return_breaking:
                _print_findings("Breaking", return_breaking)
            if return_compatible:
                _print_findings("Compatible", return_compatible)
            if not return_breaking and not return_compatible:
                print("No public return annotations changed.", flush=True)
        else:
            _print_findings("Return type breakings", return_breaking)

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
            relaxed = _caller_compatible_entries(changes)
            if relaxed:
                print(
                    f"\nAexPy breakings treated as compatible ({len(relaxed)}):",
                    flush=True,
                )
                for entry in relaxed:
                    print(
                        f"  [aexpy rank={entry['rank']}] {entry['message']}",
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
            f"\nSummary vs {against_label}: "
            f"aexpy_breaking={breaking} aexpy_compatible={compatible} "
            f"aexpy_unknown={unknown} enum_breaking={len(enum_breaking)} "
            f"model_breaking={len(model_breaking)} "
            f"return_breaking={len(return_breaking)} "
            f"return_compatible={len(return_compatible)}",
            flush=True,
        )

        failed = False
        if args.fail_on_breaking and (
            breaking or enum_breaking or model_breaking or return_breaking
        ):
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
