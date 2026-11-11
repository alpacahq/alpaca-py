"""Record / replay transport and output snapshots for consumer scenarios.

Modes:

* ``record``: runs a scenario against the paper API with the baseline release
  installed, saves every HTTP exchange, then replays it once to store the
  output snapshot.
* ``replay``: serves the saved responses, fails on any difference in the
  requests the SDK sends, and compares the output snapshot.
* ``live``: runs against the paper API and checks only the scenario's own
  assertions, because live data changes.
* ``migrate``: upgrades recordings made with an older recording format,
  offline. With the baseline release installed, it replays the stored
  responses, re-captures the requests the baseline sends, and re-takes the
  snapshot. Only for scenarios unchanged since they were recorded.

HTTP is intercepted at ``requests.adapters.HTTPAdapter.send``. Replay also
blocks real network connections, so if the SDK stops sending HTTP through
``requests`` the run fails loudly instead of reaching a real server. Update
this module, not the scenarios, when that happens.
"""

from __future__ import annotations

import base64
import difflib
import hashlib
import importlib.metadata
import inspect
import json
import platform
import re
import socket
import time
import warnings
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass, field
from datetime import date, datetime
from datetime import time as dt_time
from datetime import timedelta
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Mapping, Optional, Set
from urllib.parse import parse_qsl, urlsplit
from uuid import UUID

import pytest
import requests
from packaging.version import Version
from requests.adapters import HTTPAdapter
from requests.structures import CaseInsensitiveDict

from scenarios import Context, Scenario, new_unique_id

# 2: request and response headers recorded, snapshots keyed by attribute name,
# scenario digest covers referenced helpers, constants and Context members.
FORMAT_VERSION = 2
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent

# Paper-account identifiers replaced in recorded response bodies. Request
# headers (API keys) are never recorded. Replacements keep the value's shape
# (a UUID stays a UUID) so the SDK models still validate on replay.
SCRUBBED_RESPONSE_KEYS = frozenset({"account_number", "account_id"})
# Endpoints whose top-level "id" is the paper account's own id.
SCRUBBED_ID_PATHS = frozenset({"/v2/account"})
SCRUBBED_VALUE = "SCRUBBED"
SCRUBBED_UUID = "00000000-0000-0000-0000-000000000000"

# Request headers: auth values are never stored, only the header name (and the
# Authorization scheme). Transport headers come from the HTTP library or are
# derived from the body, which is compared on its own.
SECRET_REQUEST_HEADERS = frozenset(
    {"apca-api-key-id", "apca-api-secret-key", "authorization"}
)
TRANSPORT_REQUEST_HEADERS = frozenset(
    {"accept-encoding", "connection", "content-length"}
)
# Response headers that vary per request, are sensitive, or describe an
# encoding the stored (decoded) body no longer has.
DROPPED_RESPONSE_HEADERS = frozenset(
    {
        "connection",
        "content-encoding",
        "content-length",
        "date",
        "keep-alive",
        "set-cookie",
        "transfer-encoding",
    }
)
# Version numbers in User-Agent change with every release.
_VERSION = re.compile(r"\d+(?:\.\d+)+[^\s/]*")

# Third-party packages whose versions change snapshot output (for example
# DataFrame dtypes). Stored with each recording and shown on a mismatch.
TRACKED_PACKAGES = ("alpaca-py", "pandas", "pydantic", "requests", "numpy")

MAX_DIFF_LINES = 200

# Set by conftest for --consumer-surface-out: records what replay exercises of
# the public surface (see _exercised.py and check_surface.py).
COLLECTOR: Any = None


@dataclass(frozen=True)
class Settings:
    mode: str
    update_snapshots: bool
    strict: bool
    recordings_dir: Path
    baseline: str
    # Record mode: also overwrite scenarios that already have a recording.
    rerecord: bool = False
    # Replay with --consumer-update-snapshots: only scenarios whose recordings
    # come from the SDK installed here (see _check_sdk). Used by refresh.
    match_sdk: bool = False
    # Left out of repr: pytest prints fixture values when a test fails.
    api_key: Optional[str] = field(default=None, repr=False)
    secret_key: Optional[str] = field(default=None, repr=False)


# --------------------------------------------------------------------------
# Request / response encoding


def _decode_body(raw: Any) -> Optional[Dict[str, Any]]:
    if raw is None or raw == b"" or raw == "":
        return None
    data = raw.encode("utf-8") if isinstance(raw, str) else bytes(raw)
    try:
        return {"json": json.loads(data)}
    except ValueError:
        pass
    try:
        return {"text": data.decode("utf-8")}
    except UnicodeDecodeError:
        return {"base64": base64.b64encode(data).decode("ascii")}


def _encode_body(body: Optional[Dict[str, Any]]) -> bytes:
    if body is None:
        return b""
    if "json" in body:
        return json.dumps(body["json"]).encode("utf-8")
    if "text" in body:
        return body["text"].encode("utf-8")
    return base64.b64decode(body["base64"])


def _request_headers(headers: Any) -> Dict[str, str]:
    normalized: Dict[str, str] = {}
    for name, value in headers.items():
        key = name.lower()
        if key in TRANSPORT_REQUEST_HEADERS:
            continue
        if key in SECRET_REQUEST_HEADERS:
            scheme = (
                value.split(" ", 1)[0] + " "
                if key == "authorization" and " " in value
                else ""
            )
            normalized[key] = f"{scheme}<redacted>"
        elif key == "user-agent":
            normalized[key] = _VERSION.sub("<version>", value)
        else:
            normalized[key] = value
    return dict(sorted(normalized.items()))


def normalize_request(request: requests.PreparedRequest) -> Dict[str, Any]:
    """The parts of a request that replay compares.

    Header names are compared, and so are their values except for auth
    headers (redacted) and the version numbers in User-Agent.
    """
    parts = urlsplit(request.url or "")
    # Sort by key only: a stable sort keeps the order of repeated keys.
    query = sorted(parse_qsl(parts.query, keep_blank_values=True), key=lambda kv: kv[0])
    return {
        "method": (request.method or "").upper(),
        "url": f"{parts.scheme}://{parts.netloc}{parts.path}",
        "query": [list(pair) for pair in query],
        "headers": _request_headers(request.headers),
        "body": _decode_body(request.body),
    }


def _scrubbed(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    try:
        UUID(value)
    except ValueError:
        return SCRUBBED_VALUE
    return SCRUBBED_UUID


def _scrub(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _scrubbed(item) if key in SCRUBBED_RESPONSE_KEYS else _scrub(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_scrub(item) for item in value]
    return value


def encode_response(response: requests.Response) -> Dict[str, Any]:
    body = _decode_body(response.content)
    if body is not None and "json" in body:
        data = _scrub(body["json"])
        path = urlsplit(response.url or "").path
        if path in SCRUBBED_ID_PATHS and isinstance(data, dict) and "id" in data:
            data["id"] = _scrubbed(data["id"])
        body = {"json": data}
    return {
        "status": response.status_code,
        "reason": response.reason,
        "headers": {
            name: value
            for name, value in response.headers.items()
            if name.lower() not in DROPPED_RESPONSE_HEADERS
        },
        "body": body,
    }


def build_response(
    recorded: Dict[str, Any], request: requests.PreparedRequest
) -> requests.Response:
    response = requests.Response()
    response.status_code = recorded["status"]
    response.reason = recorded.get("reason") or ""
    headers = dict(recorded.get("headers") or {})
    if not headers and recorded.get("content_type"):  # format 1 recordings
        headers["Content-Type"] = recorded["content_type"]
    response.headers = CaseInsensitiveDict(headers)
    response._content = _encode_body(recorded.get("body"))
    response._content_consumed = True
    response.encoding = "utf-8"
    response.url = request.url or ""
    response.request = request
    return response


# --------------------------------------------------------------------------
# Transport patches


class ReplayMismatch(AssertionError):
    """The SDK sent a request the recording does not have."""


class NetworkBlocked(RuntimeError):
    """Replay mode tried to open a real network connection."""


def _pretty(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, default=str)


def _same(left: Any, right: Any) -> bool:
    """Equality that keeps JSON types apart.

    Plain ``==`` treats ``1 == 1.0 == True`` and ``nan != nan``. Comparing the
    canonical JSON text catches an ``int`` turning into a ``float`` and treats
    two NaNs as equal.
    """
    return json.dumps(left, sort_keys=True, default=str) == json.dumps(
        right, sort_keys=True, default=str
    )


def _added_fields(
    expected: Any, actual: Any, path: str = "result"
) -> Optional[List[str]]:
    """Model fields present now but not in the snapshot, if that is the only change.

    Returns ``None`` when ``actual`` is not ``expected`` plus extra Pydantic
    model fields. A new field does not break callers; a removed, renamed or
    retyped one does, and so does any change outside model fields.
    """
    if _same(expected, actual):
        return []
    if isinstance(expected, dict) and isinstance(actual, dict):
        if (
            "fields" in expected
            and "fields" in actual
            and expected.get("__type__") == actual.get("__type__")
            and set(expected) == set(actual)
        ):
            old, new = expected["fields"], actual["fields"]
            if not set(old) <= set(new):
                return None
            added = [f"{path}.{name}" for name in sorted(set(new) - set(old))]
            for name in old:
                nested = _added_fields(old[name], new[name], f"{path}.{name}")
                if nested is None:
                    return None
                added.extend(nested)
            for key in set(expected) - {"fields"}:
                if not _same(expected[key], actual[key]):
                    return None
            return added
        if "__type__" in expected or "__type__" in actual:
            if set(expected) != set(actual):
                return None
            added = []
        else:
            # A plain dict (raw JSON, or a dict keyed by symbol): a new key does
            # not break code that reads the existing ones.
            if not set(expected) <= set(actual):
                return None
            added = [f"{path}.{key}" for key in sorted(set(actual) - set(expected))]
        for key in expected:
            nested = _added_fields(expected[key], actual[key], f"{path}.{key}")
            if nested is None:
                return None
            added.extend(nested)
        return added
    if isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            return None
        added = []
        for index, (old_item, new_item) in enumerate(zip(expected, actual)):
            nested = _added_fields(old_item, new_item, f"{path}[{index}]")
            if nested is None:
                return None
            added.extend(nested)
        return added
    return None


def _diff(expected: Any, actual: Any, expected_label: str, actual_label: str) -> str:
    lines = list(
        difflib.unified_diff(
            _pretty(expected).splitlines(),
            _pretty(actual).splitlines(),
            fromfile=expected_label,
            tofile=actual_label,
            lineterm="",
        )
    )
    if len(lines) > MAX_DIFF_LINES:
        hidden = len(lines) - MAX_DIFF_LINES
        lines = lines[:MAX_DIFF_LINES] + [f"... {hidden} more diff lines"]
    return "\n".join(lines)


@contextmanager
def _patched_send(handler) -> Iterator[None]:
    original = HTTPAdapter.send

    def send(adapter, request, **kwargs):
        return handler(original, adapter, request, **kwargs)

    HTTPAdapter.send = send  # type: ignore[method-assign]
    try:
        yield
    finally:
        HTTPAdapter.send = original  # type: ignore[method-assign]


@contextmanager
def _network_blocked() -> Iterator[None]:
    original = socket.socket.connect

    def connect(sock, address):
        host = address[0] if isinstance(address, tuple) else address
        if sock.family == getattr(socket, "AF_UNIX", None) or host in (
            "127.0.0.1",
            "::1",
            "localhost",
        ):
            return original(sock, address)
        raise NetworkBlocked(
            f"replay mode blocks real network access (tried {address!r}). If the "
            "SDK no longer sends HTTP through `requests`, update "
            "consumer_checks/_harness.py so replay can intercept it."
        )

    socket.socket.connect = connect  # type: ignore[method-assign]
    try:
        yield
    finally:
        socket.socket.connect = original  # type: ignore[method-assign]


class Recorder:
    def __init__(self) -> None:
        self.interactions: List[Dict[str, Any]] = []

    @contextmanager
    def active(self) -> Iterator[None]:
        def handle(original, adapter, request, **kwargs):
            response = original(adapter, request, **kwargs)
            self.interactions.append(
                {
                    "request": normalize_request(request),
                    "response": encode_response(response),
                }
            )
            return response

        with _patched_send(handle):
            yield


def _stub_response(spec: Mapping[str, Any]) -> Dict[str, Any]:
    if "json" in spec:
        body, content_type = {"json": spec["json"]}, "application/json"
    else:
        body, content_type = {"text": spec.get("text", "")}, "text/html"
    return {
        "status": spec["status"],
        "reason": spec.get("reason", ""),
        "headers": {"Content-Type": content_type},
        "body": body,
    }


@contextmanager
def _stubbed(responses: Any) -> Iterator[None]:
    """Serve fixed responses in order instead of calling the API."""
    remaining = list(responses)

    def handle(original, adapter, request, **kwargs):
        if not remaining:
            raise AssertionError(
                f"the SDK sent more requests than the {len(responses)} stubbed "
                "responses"
            )
        return build_response(_stub_response(remaining.pop(0)), request)

    with _network_blocked(), _no_sleep(), _patched_send(handle):
        yield
    # Only reached when the scenario succeeded, so this never hides its error.
    if remaining:
        raise AssertionError(
            f"{len(remaining)} of {len(responses)} stubbed responses were never "
            "requested: the stub no longer matches what the SDK sends (for "
            "example how often it retries)"
        )


@contextmanager
def _no_sleep() -> Iterator[None]:
    # The SDK sleeps between retries (429/504). Replay serves the same
    # responses instantly, so those waits are pure delay.
    original = time.sleep
    time.sleep = lambda seconds: None  # type: ignore[assignment]
    try:
        yield
    finally:
        time.sleep = original  # type: ignore[assignment]


def _without_headers(request: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in request.items() if key != "headers"}


class Replayer:
    def __init__(
        self, interactions: List[Dict[str, Any]], *, compare_headers: bool = True
    ) -> None:
        self.interactions = interactions
        self.compare_headers = compare_headers
        self.cursor = 0
        # What the SDK sent, as normalized now. Migration stores these.
        self.sent: List[Dict[str, Any]] = []
        # Kept even if the SDK or the scenario swallows the exception.
        self.errors: List[AssertionError] = []

    @contextmanager
    def active(self) -> Iterator[None]:
        def handle(original, adapter, request, **kwargs):
            actual = normalize_request(request)
            number = self.cursor + 1
            if self.cursor >= len(self.interactions):
                error = ReplayMismatch(
                    f"the SDK sent request #{number}, but the recording has only "
                    f"{len(self.interactions)}:\n{_pretty(actual)}"
                )
                self.errors.append(error)
                raise error
            recorded = self.interactions[self.cursor]
            expected = recorded["request"]
            compared = actual
            if not self.compare_headers:
                expected, compared = _without_headers(expected), _without_headers(
                    actual
                )
            if not _same(compared, expected):
                error = ReplayMismatch(
                    f"request #{number} differs from the recording:\n"
                    + _diff(expected, compared, "recorded", "sent now")
                )
                self.errors.append(error)
                raise error
            self.cursor += 1
            self.sent.append(actual)
            return build_response(recorded["response"], request)

        with _network_blocked(), _no_sleep(), _patched_send(handle):
            yield

    def check_complete(self) -> None:
        if self.errors:
            raise self.errors[0]
        if self.cursor != len(self.interactions):
            missing = self.interactions[self.cursor]["request"]
            raise ReplayMismatch(
                f"the SDK sent {self.cursor} of {len(self.interactions)} recorded "
                f"requests. First one not sent:\n{_pretty(missing)}"
            )


# --------------------------------------------------------------------------
# Output snapshots


def _type_name(value: Any) -> str:
    # Class name only: moving a class to another module is not a user-visible
    # change, while renaming it is.
    return type(value).__name__


def _key(key: Any) -> str:
    if isinstance(key, str) and not isinstance(key, Enum):
        return key
    snap = snapshot(key)
    return json.dumps(snap, sort_keys=True) if not isinstance(snap, str) else snap


def _snapshot_frame(frame: Any) -> Dict[str, Any]:
    index = frame.index
    return {
        "__type__": _type_name(frame),
        "shape": list(frame.shape),
        "columns": [str(column) for column in frame.columns],
        "dtypes": {str(column): str(dtype) for column, dtype in frame.dtypes.items()},
        "index": {
            "names": [str(name) for name in index.names],
            "dtypes": [
                str(index.get_level_values(level).dtype)
                for level in range(index.nlevels)
            ],
        },
        "head": [
            [str(label), [str(item) for item in row]]
            for label, row in zip(
                frame.head(3).index, frame.head(3).itertuples(index=False)
            )
        ],
    }


def snapshot(value: Any) -> Any:
    """A JSON-friendly picture of an SDK output that keeps its types.

    JSON already tells ``None``, ``bool``, ``int``, ``float`` and ``str`` apart.
    Everything else becomes ``{"__type__": ..., ...}`` so that, for example, a
    ``str`` turning into an enum or a ``float`` turning into a ``str`` shows up.
    """
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, Enum):
        return {"__type__": _type_name(value), "name": value.name, "value": value.value}
    if type(value) in (int, float, str):
        return value
    if isinstance(value, datetime):
        return {"__type__": "datetime", "value": value.isoformat()}
    if isinstance(value, (date, dt_time)):
        return {"__type__": _type_name(value), "value": value.isoformat()}
    if isinstance(value, timedelta):
        return {"__type__": "timedelta", "value": value.total_seconds()}
    if isinstance(value, (UUID, Decimal)):
        return {"__type__": _type_name(value), "value": str(value)}
    if isinstance(value, BaseException):
        snap: Dict[str, Any] = {"__type__": _type_name(value)}
        for attribute in ("status_code", "code"):
            try:
                snap[attribute] = snapshot(getattr(value, attribute))
            except Exception:  # properties that parse the error body may fail
                pass
        return snap
    fields = getattr(type(value), "model_fields", None)
    if isinstance(fields, dict):  # Pydantic model
        # Keyed by attribute name, whatever provides it: a declared field, a
        # computed field or an extra field. Users write `obj.name` either way,
        # so a value moving between them is not a change.
        names = [*fields, *(getattr(type(value), "model_computed_fields", None) or {})]
        with warnings.catch_warnings():
            # Reading every field touches deprecated ones too. They stay in the
            # snapshot so their removal is flagged, but the warning is noise here.
            warnings.simplefilter("ignore", DeprecationWarning)
            values = {name: getattr(value, name) for name in names}
        for name, item in (getattr(value, "model_extra", None) or {}).items():
            values.setdefault(name, item)
        return {
            "__type__": _type_name(value),
            "fields": {name: snapshot(item) for name, item in values.items()},
        }
    if type(value).__module__.startswith("pandas") and hasattr(value, "dtypes"):
        if hasattr(value, "columns"):
            return _snapshot_frame(value)
    if isinstance(value, dict):
        items = {_key(key): snapshot(item) for key, item in value.items()}
        if type(value) is dict:
            return items
        return {"__type__": _type_name(value), "items": items}
    if isinstance(value, (list, tuple)):
        items_list = [snapshot(item) for item in value]
        if type(value) is list:
            return items_list
        return {"__type__": _type_name(value), "items": items_list}
    if isinstance(value, (int, float, str)):  # subclasses, e.g. numpy scalars
        return {"__type__": _type_name(value), "value": str(value)}
    return {"__type__": _type_name(value), "repr": repr(value)}


# --------------------------------------------------------------------------
# Recordings


def recording_path(settings: Settings, scenario: Scenario) -> Path:
    return settings.recordings_dir / f"{scenario.name}.json"


def load_recording(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_recording(path: Path, recording: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(recording, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


_CONSTANT_TYPES = (
    bool,
    int,
    float,
    str,
    bytes,
    date,
    datetime,
    dt_time,
    timedelta,
    Decimal,
    UUID,
    Enum,
)


def _is_constant(value: Any) -> bool:
    if value is None or isinstance(value, _CONSTANT_TYPES):
        return True
    if isinstance(value, (tuple, list, frozenset, set)):
        return all(_is_constant(item) for item in value)
    if isinstance(value, dict):
        return all(_is_constant(k) and _is_constant(v) for k, v in value.items())
    return False


def _constant_repr(value: Any) -> str:
    if isinstance(value, (set, frozenset)):
        return f"{type(value).__name__}({sorted(map(repr, value))})"
    if isinstance(value, dict):
        items = sorted((repr(k), _constant_repr(v)) for k, v in value.items())
        return "{" + ", ".join(f"{k}: {v}" for k, v in items) + "}"
    return repr(value)


def _code_names(code: Any) -> Set[str]:
    names = set(code.co_names)
    for const in code.co_consts:
        if inspect.iscode(const):  # lambdas, generator expressions, nested functions
            names |= _code_names(const)
    return names


def _is_scenario_code(value: Any) -> bool:
    module = getattr(value, "__module__", "") or ""
    return module == "scenarios" or module.startswith("scenarios.")


def source_digest(scenario: Scenario) -> str:
    """Hash of everything the scenario's behavior depends on in this package.

    Starting from the scenario function, it follows every global name the code
    uses: functions and classes from ``scenarios`` (helpers, shared modules) are
    hashed by source and followed in turn, module constants by value, and
    ``ctx.<name>`` members of ``Context`` by source. Code the scenario never
    references does not affect its digest. SDK names are not followed: changes
    there are what replay is for.
    """
    parts: List[str] = []
    seen: Set[int] = set()

    def visit(obj: Any) -> None:
        if id(obj) in seen:
            return
        seen.add(id(obj))
        parts.append(inspect.getsource(obj))
        if not inspect.isfunction(obj):
            return
        scope = obj.__globals__
        for name in sorted(_code_names(obj.__code__)):
            if name in scope:
                value = scope[name]
                if (inspect.isfunction(value) or inspect.isclass(value)) and (
                    _is_scenario_code(value)
                ):
                    visit(value)
                elif _is_constant(value):
                    parts.append(f"{name} = {_constant_repr(value)}")
            if not name.startswith("__"):
                member = inspect.getattr_static(Context, name, None)
                function = (
                    getattr(member, "func", None)
                    or getattr(member, "fget", None)
                    or member
                )
                if inspect.isfunction(function) and _is_scenario_code(function):
                    visit(function)

    visit(scenario.fn)
    if scenario.stub_responses:
        parts.append(json.dumps(list(scenario.stub_responses), sort_keys=True))
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def _legacy_source_digest(scenario: Scenario) -> str:
    """The format 1 digest: the scenario plus the ``_`` helpers in its module.

    Only used to confirm a format 1 recording still matches its scenario before
    migrating it.
    """
    module = inspect.getmodule(scenario.fn)
    helpers = sorted(
        (name, member)
        for name, member in vars(module).items()
        if name.startswith("_")
        and inspect.isfunction(member)
        and member.__module__ == scenario.fn.__module__
    )
    source = inspect.getsource(scenario.fn) + "".join(
        inspect.getsource(member) for _, member in helpers
    )
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


# How each recording format hashed its scenario. Migration checks a recording
# against the hash of its own format, so it can upgrade from any of them.
# Add an entry here when source_digest changes.
_DIGEST_BY_FORMAT: Dict[int, Callable[[Scenario], str]] = {
    1: _legacy_source_digest,
    2: source_digest,
}


def environment() -> Dict[str, Optional[str]]:
    info: Dict[str, Optional[str]] = {"python": platform.python_version()}
    for package in TRACKED_PACKAGES:
        try:
            info[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            info[package] = None
    return info


def orphan_recordings(settings: Settings, scenario_names: Any) -> List[str]:
    """Recordings whose scenario no longer exists (deleted or renamed)."""
    recorded = {path.stem for path in settings.recordings_dir.glob("*.json")}
    return sorted(recorded - set(scenario_names))


def sdk_location() -> Path:
    import alpaca

    return Path(alpaca.__file__).resolve().parent


# --------------------------------------------------------------------------
# Running scenarios


def _require_keys(settings: Settings) -> None:
    if not (settings.api_key and settings.secret_key):
        pytest.fail(
            f"{settings.mode} mode needs CONSUMER_TRADING_API_KEY_ID and "
            "CONSUMER_TRADING_API_SECRET_KEY, in the environment or the repo's "
            ".env, for a paper account used only by these checks (see "
            ".env.example)",
            pytrace=False,
        )


def unreleased(settings: Settings, scenario: Scenario) -> bool:
    """The scenario uses API newer than the BASELINE release."""
    return scenario.since is not None and Version(scenario.since) > Version(
        settings.baseline
    )


def _installed_sdk(settings: Settings) -> str:
    if sdk_location() == REPO_ROOT / "alpaca":
        return "checkout"
    if importlib.metadata.version("alpaca-py") == settings.baseline:
        return "baseline"
    return "other"


def _check_sdk(settings: Settings, scenario: Scenario) -> None:
    """Record, migrate and refresh use the SDK the recording comes from.

    That is the BASELINE release, or this checkout for scenarios whose ``since``
    is newer than BASELINE. The make targets run one pass with each; a pass
    skips the scenarios that belong to the other.
    """
    wanted = "checkout" if unreleased(settings, scenario) else "baseline"
    installed = _installed_sdk(settings)
    if installed == wanted:
        return
    label = (
        "this checkout's SDK"
        if wanted == "checkout"
        else (f"alpaca-py {settings.baseline}")
    )
    if installed != "other":
        pytest.skip(f"{scenario.name} is recorded with {label}: the other pass does it")
    pytest.fail(
        f"{settings.mode} needs {label} for {scenario.name}, but found alpaca-py "
        f"{importlib.metadata.version('alpaca-py')} at {sdk_location()}. Use the "
        "make target (`make consumer-record`, `consumer-migrate` or "
        "`consumer-refresh`).",
        pytrace=False,
    )


def _run(scenario: Scenario, ctx: Context) -> Dict[str, Any]:
    result = scenario.fn(ctx)
    if not isinstance(result, dict):
        raise TypeError(f"{scenario.name} must return a dict of named outputs")
    return result


def _replay(
    settings: Settings,
    scenario: Scenario,
    path: Path,
    recording: Dict[str, Any],
    *,
    update: bool,
    migrate: bool = False,
) -> None:
    variables: Dict[str, str] = recording.get("vars", {})
    recorded_format = recording.get("format", 1)

    def unique_id(label: str) -> str:
        if label not in variables:
            pytest.fail(
                f"{scenario.name} asks for unique_id({label!r}), which the "
                "recording does not have. Re-record the scenario.",
                pytrace=False,
            )
        return variables[label]

    digest = source_digest(scenario)
    if migrate:
        recorded_digest = _DIGEST_BY_FORMAT.get(recorded_format)
        if recorded_digest is None:
            pytest.fail(
                f"{scenario.name}: no migration from recording format "
                f"{recorded_format}. Re-record it with `make consumer-record`.",
                pytrace=False,
            )
        if recording.get("scenario_sha256") != recorded_digest(scenario):
            pytest.fail(
                f"{scenario.name} changed since it was recorded, so its recording "
                "cannot be migrated. Re-record it with `make consumer-record`.",
                pytrace=False,
            )
    elif recorded_format != FORMAT_VERSION:
        pytest.fail(
            f"{scenario.name}: recording format {recorded_format} is older than "
            f"{FORMAT_VERSION}. Upgrade it offline with `make consumer-migrate`, "
            "or re-record it.",
            pytrace=False,
        )
    elif not update and recording.get("scenario_sha256") != digest:
        pytest.fail(
            f"{scenario.name} changed since it was recorded. Scenario code is "
            "frozen: re-record it, or refresh its snapshot with "
            "--consumer-update-snapshots (both need the sdk-breaking label).",
            pytrace=False,
        )

    replayer = Replayer(recording["interactions"], compare_headers=not migrate)
    ctx = Context(
        "replay-key-id",
        "replay-secret-key",
        sleep=lambda seconds: None,
        unique_id=unique_id,
    )
    collecting = COLLECTOR.active() if COLLECTOR is not None else nullcontext()
    with replayer.active(), collecting:
        try:
            result = _run(scenario, ctx)
        except Exception:
            # The SDK may wrap the mismatch, or the scenario may catch it.
            if replayer.errors:
                pytest.fail(f"{scenario.name}: {replayer.errors[0]}", pytrace=False)
            raise
    try:
        replayer.check_complete()
    except ReplayMismatch as error:
        pytest.fail(f"{scenario.name}: {error}", pytrace=False)

    actual = snapshot(result)
    if migrate:
        # Old recordings lack request headers: store what the baseline sends.
        # Response headers cannot be recovered; only Content-Type was kept.
        for interaction, sent in zip(recording["interactions"], replayer.sent):
            interaction["request"] = sent
        recording["format"] = FORMAT_VERSION
        recording["migrated_from_format"] = recorded_format
    if update or migrate:
        recording["result"] = actual
        recording["scenario_sha256"] = digest
        recording["result_from"] = environment()
        write_recording(path, recording)
        return

    if recording.get("recorded_against") == "checkout" and not unreleased(
        settings, scenario
    ):
        warnings.warn(
            f"{scenario.name} was recorded with an unreleased SDK, and BASELINE "
            f"{settings.baseline} now has its API. Re-record it with the release: "
            f'make consumer-record ARGS="--consumer-rerecord -k {scenario.name}"',
            stacklevel=1,
        )

    expected = recording.get("result")
    added = _added_fields(expected, actual)
    if added:
        # Additive, so not a break. Refresh the snapshot (labeled PR, or at the
        # next baseline bump) to start protecting the new fields.
        shown = sorted({re.sub(r"\[\d+\]", "[]", path) for path in added})
        warnings.warn(
            f"{scenario.name}: new fields or keys not in the snapshot yet: "
            + ", ".join(shown[:10])
            + (f" and {len(shown) - 10} more" if len(shown) > 10 else ""),
            stacklevel=1,
        )
    if added is None:
        recorded_env = (
            recording.get("result_from") or recording.get("recorded_with") or {}
        )
        here = environment()
        # The SDK version always differs from the baseline; other packages
        # (pandas, numpy, pydantic) change snapshots by themselves.
        drift = [
            f"{package} {here.get(package)} here, {recorded_env.get(package)} "
            "when the snapshot was taken"
            for package in TRACKED_PACKAGES
            if package != "alpaca-py" and recorded_env.get(package) != here.get(package)
        ]
        cause = ""
        if drift:
            cause = (
                "Your environment differs from the recording's: "
                + "; ".join(drift)
                + ". Run `poetry install` so it matches poetry.lock and try again: "
                "the difference may come from that, not from the SDK.\n\n"
            )
        pytest.fail(
            f"{scenario.name}: SDK output differs from the recording.\n"
            + cause
            + _diff(expected, actual, "recorded", "now"),
            pytrace=False,
        )


@contextmanager
def _transport(scenario: Scenario) -> Iterator[None]:
    """Stubbed scenarios never reach the API; the rest call it for real."""
    if scenario.stub_responses:
        with _stubbed(scenario.stub_responses):
            yield
    else:
        yield


def _keys(settings: Settings, scenario: Scenario) -> tuple:
    if scenario.stub_responses:
        return "stub-key-id", "stub-secret-key"
    _require_keys(settings)
    return settings.api_key or "", settings.secret_key or ""


def _record(settings: Settings, scenario: Scenario, path: Path) -> None:
    api_key, secret_key = _keys(settings, scenario)

    variables: Dict[str, str] = {}

    def unique_id(label: str) -> str:
        return variables.setdefault(label, new_unique_id())

    recorder = Recorder()
    ctx = Context(api_key, secret_key, sleep=time.sleep, unique_id=unique_id)
    with _transport(scenario), recorder.active():
        _run(scenario, ctx)

    recording: Dict[str, Any] = {
        "format": FORMAT_VERSION,
        "scenario": scenario.name,
        "recorded_with": environment(),
        "recorded_against": (
            "checkout" if unreleased(settings, scenario) else "baseline"
        ),
        "vars": variables,
        "interactions": recorder.interactions,
    }
    # Take the snapshot by replaying the scrubbed recording, so the stored
    # output is exactly what later replays reproduce.
    _replay(settings, scenario, path, recording, update=True)


def _live(settings: Settings, scenario: Scenario) -> None:
    api_key, secret_key = _keys(settings, scenario)
    ctx = Context(
        api_key, secret_key, sleep=time.sleep, unique_id=lambda label: new_unique_id()
    )
    with _transport(scenario):
        snapshot(_run(scenario, ctx))


def check_scenario(scenario: Scenario, settings: Settings) -> None:
    path = recording_path(settings, scenario)
    if settings.mode == "record":
        _check_sdk(settings, scenario)
        if path.exists() and not settings.rerecord:
            # Re-recording changes the file (new ids, times, account values),
            # which the freeze rule treats like any other recording change.
            pytest.skip(
                f"{scenario.name} is already recorded. Pass --consumer-rerecord to "
                "record it again (that changes its recording: sdk-breaking label)."
            )
        _record(settings, scenario, path)
        return
    if settings.mode == "live":
        _live(settings, scenario)
        return

    recording = load_recording(path)
    if settings.mode == "migrate":
        if recording is None:
            pytest.skip(f"no recording for {scenario.name}")
        if recording.get("format", 1) == FORMAT_VERSION:
            pytest.skip(f"{scenario.name} is already in format {FORMAT_VERSION}")
        _check_sdk(settings, scenario)
        _replay(settings, scenario, path, recording, update=True, migrate=True)
        return
    if recording is None:
        message = (
            f"no recording for {scenario.name} at {path}. Record it with "
            "`make consumer-record`."
        )
        if settings.strict:
            pytest.fail(message, pytrace=False)
        pytest.skip(message)
    if settings.match_sdk:
        _check_sdk(settings, scenario)
    _replay(settings, scenario, path, recording, update=settings.update_snapshots)
