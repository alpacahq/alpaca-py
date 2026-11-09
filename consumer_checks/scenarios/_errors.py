"""Shared by the error scenarios. Part of every using scenario's hash."""

from __future__ import annotations

from typing import Any, Dict

from alpaca.common.exceptions import APIError


def error_details(error: APIError) -> Dict[str, Any]:
    """What a user reads from an APIError, including which reads raise."""
    details: Dict[str, Any] = {"error": error, "text": str(error)}
    for attribute in ("code", "message"):
        try:
            details[attribute] = getattr(error, attribute)
        except Exception as problem:  # the body is not JSON, or lacks the key
            details[f"{attribute}_raises"] = type(problem).__name__
    return details
