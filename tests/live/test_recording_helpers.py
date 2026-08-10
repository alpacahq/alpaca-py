"""Unit tests for live recording helpers (no network)."""

from pathlib import Path

from pydantic import BaseModel

from tests.live.recording import (
    format_exchange_report,
    reconcile_results_with_test_outcome,
    redact,
    redact_request,
    serialize_response,
    update_artifact_outcome,
    write_artifact,
)


class _Sample(BaseModel):
    name: str
    value: int


def test_serialize_response_pydantic():
    assert serialize_response(_Sample(name="a", value=1)) == {
        "name": "a",
        "value": 1,
    }


def test_redact_secret_keys_and_headers():
    payload = {
        "APCA-API-KEY-ID": "key",
        "nested": {"authorization": "Bearer abc.def"},
        "message": "Authorization Bearer abc.def ok",
    }
    redacted = redact(payload)
    assert redacted["APCA-API-KEY-ID"] == "***REDACTED***"
    assert redacted["nested"]["authorization"] == "***REDACTED***"
    assert "***REDACTED***" in redacted["message"]


def test_redact_does_not_scrub_body_token_field():
    assert redact({"token": "keep-me"}) == {"token": "keep-me"}


def test_redact_request_scrubs_header_token():
    redacted = redact_request(
        {
            "method": "GET",
            "url": "https://example",
            "headers": {"Token": "secret", "X-Other": "ok"},
            "body": {"token": "keep-me"},
        }
    )
    assert redacted["headers"]["Token"] == "***REDACTED***"
    assert redacted["headers"]["X-Other"] == "ok"
    assert redacted["body"]["token"] == "keep-me"


def test_write_artifact(tmp_path: Path):
    path = write_artifact(
        tmp_path,
        test_id="tests/live/test_x.py::test_get_account",
        method="get_account",
        passed=True,
        status_code=200,
        response_body={"id": "abc"},
        request={"method": "GET", "url": "https://example/v2/account", "headers": {}},
        error=None,
    )
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert '"method": "get_account"' in text
    assert '"passed": true' in text
    assert '"request"' in text


def test_format_exchange_report_includes_request_and_response():
    report = format_exchange_report(
        method="get_account",
        request={
            "method": "GET",
            "url": "https://paper-api.alpaca.markets/v2/account",
            "headers": {"APCA-API-KEY-ID": "secret-key"},
            "body": None,
        },
        status_code=200,
        response_body={"equity": "1000"},
        passed=True,
    )
    assert "LIVE PROBE  method=get_account" in report
    assert "GET https://paper-api.alpaca.markets/v2/account" in report
    assert "***REDACTED***" in report
    assert '"equity": "1000"' in report
    assert "status_code: 200" in report


def test_reconcile_flips_provisional_pass_when_test_fails(tmp_path: Path):
    path = write_artifact(
        tmp_path,
        test_id="tests/live/test_x.py::test_get_account",
        method="get_account",
        passed=True,
        status_code=200,
        response_body={"id": "abc"},
        error=None,
    )
    results = [
        {
            "id": "tests/live/test_x.py::test_get_account",
            "method": "get_account",
            "passed": True,
            "error": None,
            "artifact": str(path),
        },
        {
            "id": "tests/live/test_x.py::test_get_account",
            "method": "get_account",
            "passed": False,
            "error": "RuntimeError: boom",
            "artifact": None,
        },
    ]

    reconcile_results_with_test_outcome(
        results,
        test_failed=True,
        error="AssertionError: account is None",
    )

    assert results[0]["passed"] is False
    assert results[0]["error"] == "AssertionError: account is None"
    assert results[1]["passed"] is False
    assert results[1]["error"] == "RuntimeError: boom"
    updated = path.read_text(encoding="utf-8")
    assert '"passed": false' in updated
    assert "AssertionError: account is None" in updated


def test_reconcile_noop_when_test_passes(tmp_path: Path):
    path = write_artifact(
        tmp_path,
        test_id="tests/live/test_x.py::test_get_account",
        method="get_account",
        passed=True,
        status_code=200,
        response_body={"id": "abc"},
        error=None,
    )
    results = [
        {
            "id": "tests/live/test_x.py::test_get_account",
            "method": "get_account",
            "passed": True,
            "error": None,
            "artifact": str(path),
        }
    ]

    reconcile_results_with_test_outcome(results, test_failed=False, error=None)

    assert results[0]["passed"] is True
    assert '"passed": true' in path.read_text(encoding="utf-8")


def test_update_artifact_outcome(tmp_path: Path):
    path = write_artifact(
        tmp_path,
        test_id="tests/live/test_x.py::test_get_account",
        method="get_account",
        passed=True,
        status_code=200,
        response_body={"id": "abc"},
        error=None,
    )
    update_artifact_outcome(path, passed=False, error="AssertionError: bad")
    text = path.read_text(encoding="utf-8")
    assert '"passed": false' in text
    assert "AssertionError: bad" in text
