"""Artifact recording helpers for live smoke tests."""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import UUID

from pydantic import BaseModel

_SECRET_KEYS = {
    "apca-api-key-id",
    "apca-api-secret-key",
    "authorization",
    "api_key",
    "secret_key",
    "oauth_token",
    "password",
}

# Header-only: "token" is too broad for response bodies.
_SECRET_HEADER_KEYS = _SECRET_KEYS | {"token"}

_SECRET_PATTERN = re.compile(
    r"(?i)(APCA-API-(?:KEY-ID|SECRET-KEY)|Bearer|Basic)\s+[^\s\"']+"
)


def serialize_response(obj: Any) -> Any:
    """Best-effort JSON-serializable form of an SDK return value."""
    if obj is None:
        return None
    if isinstance(obj, BaseModel):
        return obj.model_dump(mode="json")
    if isinstance(obj, dict):
        return {str(k): serialize_response(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [serialize_response(v) for v in obj]
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if hasattr(obj, "model_dump"):
        try:
            return obj.model_dump(mode="json")
        except TypeError:
            return obj.model_dump()
    if hasattr(obj, "__dict__"):
        return serialize_response(
            {k: v for k, v in vars(obj).items() if not k.startswith("_")}
        )
    return str(obj)


def redact(value: Any, *, secret_keys: Optional[Set[str]] = None) -> Any:
    """Recursively redact secret-looking keys and auth header values."""
    keys = secret_keys if secret_keys is not None else _SECRET_KEYS
    if isinstance(value, dict):
        out: Dict[str, Any] = {}
        for k, v in value.items():
            if str(k).lower() in keys:
                out[str(k)] = "***REDACTED***"
            else:
                out[str(k)] = redact(v, secret_keys=keys)
        return out
    if isinstance(value, list):
        return [redact(v, secret_keys=keys) for v in value]
    if isinstance(value, str):
        return _SECRET_PATTERN.sub(r"\1 ***REDACTED***", value)
    return value


def redact_request(request: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Redact a captured HTTP request; apply header-only secret key names."""
    if request is None:
        return None
    serialized = serialize_response(request)
    if not isinstance(serialized, dict):
        return redact(serialized)
    out = dict(serialized)
    if "headers" in out:
        out["headers"] = redact(out["headers"], secret_keys=_SECRET_HEADER_KEYS)
    if "body" in out:
        out["body"] = redact(out["body"])
    return out


def _decode_request_body(body: Any) -> Any:
    if body is None:
        return None
    if isinstance(body, bytes):
        try:
            text = body.decode("utf-8")
        except UnicodeDecodeError:
            return f"<binary {len(body)} bytes>"
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text
    if isinstance(body, str):
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return body
    return body


def attach_http_capture(session: Any, capture: Dict[str, Any]) -> None:
    """Record the last HTTP request/response seen on a requests Session."""

    def _hook(response: Any, *args: Any, **kwargs: Any) -> Any:
        req = response.request
        capture["request"] = {
            "method": getattr(req, "method", None),
            "url": getattr(req, "url", None),
            "headers": dict(getattr(req, "headers", {}) or {}),
            "body": _decode_request_body(getattr(req, "body", None)),
        }
        capture["status_code"] = response.status_code
        try:
            capture["body"] = response.json()
        except ValueError:
            capture["body"] = response.text
        return response

    session.hooks.setdefault("response", []).append(_hook)


def format_exchange_report(
    *,
    method: str,
    request: Optional[Dict[str, Any]] = None,
    status_code: Optional[int] = None,
    response_body: Any = None,
    error: Optional[str] = None,
    passed: bool = True,
) -> str:
    """Human-readable redacted request/response block for console evidence."""
    lines = [
        "",
        "=" * 72,
        f"LIVE PROBE  method={method}  passed={passed}",
        "-" * 72,
        "REQUEST",
    ]
    if request:
        safe_req = redact_request(request) or {}
        lines.append(f"  {safe_req.get('method')} {safe_req.get('url')}")
        headers = safe_req.get("headers") or {}
        if headers:
            lines.append("  headers:")
            for key, value in headers.items():
                lines.append(f"    {key}: {value}")
        body = safe_req.get("body")
        if body is not None:
            lines.append("  body:")
            body_json = json.dumps(body, indent=2, default=str)
            lines.extend(f"    {line}" for line in body_json.splitlines())
    else:
        lines.append("  <not captured>")

    lines.extend(["-" * 72, "RESPONSE", f"  status_code: {status_code}"])
    if error:
        lines.append(f"  error: {error}")
    safe_body = redact(serialize_response(response_body))
    if safe_body is not None:
        body_json = json.dumps(safe_body, indent=2, default=str)
        lines.append("  body:")
        lines.extend(f"    {line}" for line in body_json.splitlines())
    else:
        lines.append("  body: null")
    lines.extend(["=" * 72, ""])
    return "\n".join(lines)


def write_artifact(
    run_dir: Path,
    *,
    test_id: str,
    method: str,
    passed: bool,
    status_code: Optional[int] = None,
    response_body: Any = None,
    request: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
) -> Path:
    """Write one minimal per-test artifact JSON file."""
    run_dir.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^\w.\-]+", "_", test_id)
    path = run_dir / f"{safe_name}.json"
    payload = {
        "id": test_id,
        "method": method,
        "status_code": status_code,
        "passed": passed,
        "request": redact_request(request),
        "response_body": redact(serialize_response(response_body)),
        "error": error,
    }
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    return path


def write_summary(run_dir: Path, results: List[Dict[str, Any]]) -> Path:
    """Write summary.json for a live run."""
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / "summary.json"
    path.write_text(json.dumps(results, indent=2, default=str) + "\n", encoding="utf-8")
    return path


def update_artifact_outcome(
    path: Path,
    *,
    passed: bool,
    error: Optional[str] = None,
) -> None:
    """Update passed/error on an existing per-test artifact file."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["passed"] = passed
    payload["error"] = error
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")


def reconcile_results_with_test_outcome(
    results: List[Dict[str, Any]],
    *,
    test_failed: bool,
    error: Optional[str],
) -> None:
    """Flip provisional passed=true entries when the pytest case failed.

    ``invoke_and_record`` records success as soon as the SDK call returns
    without raising. Live tests often validate the value afterward; if that
    assert fails, artifacts/summary must not keep ``passed=true``.
    """
    if not test_failed:
        return
    for entry in results:
        if not entry.get("passed"):
            continue
        entry["passed"] = False
        entry["error"] = error
        artifact = entry.get("artifact")
        if artifact:
            update_artifact_outcome(Path(artifact), passed=False, error=error)


def invoke_and_record(
    method: str,
    fn: Callable[..., Any],
    record: Callable[..., Any],
    *args: Any,
    response_transform: Optional[Callable[[Any], Any]] = None,
    **kwargs: Any,
) -> Any:
    """Invoke an SDK method and always record evidence (including failures).

    On a non-raising return, records ``passed=True`` immediately. Callers that
    validate the result afterward (e.g. pytest asserts) must reconcile that
    provisional outcome with the final test result — the ``record_live``
    fixture does this via :func:`reconcile_results_with_test_outcome`.
    """
    try:
        result = fn(*args, **kwargs)
    except Exception as exc:
        record(
            method,
            passed=False,
            error=f"{type(exc).__name__}: {exc}",
        )
        raise
    to_record = response_transform(result) if response_transform else result
    record(method, to_record)
    return result
