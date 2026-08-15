"""Unit tests for live_call failure recording (no network)."""

import pytest

from tests.live.recording import invoke_and_record


def test_invoke_and_record_records_failures():
    recorded = []

    def fake_record(method, response=None, *, passed=True, error=None, **_kwargs):
        recorded.append(
            {"method": method, "passed": passed, "error": error, "response": response}
        )

    def boom():
        raise RuntimeError("upstream failed")

    with pytest.raises(RuntimeError, match="upstream failed"):
        invoke_and_record("get_account", boom, fake_record)

    assert len(recorded) == 1
    assert recorded[0]["method"] == "get_account"
    assert recorded[0]["passed"] is False
    assert "RuntimeError: upstream failed" in recorded[0]["error"]


def test_invoke_and_record_records_success_with_transform():
    recorded = []

    def fake_record(method, response=None, *, passed=True, error=None, **_kwargs):
        recorded.append(
            {"method": method, "passed": passed, "error": error, "response": response}
        )

    result = invoke_and_record(
        "get_calendar",
        lambda: [1, 2, 3, 4],
        fake_record,
        response_transform=lambda items: items[:2],
    )

    assert result == [1, 2, 3, 4]
    # Provisional: call did not raise; pytest record_live reconciles if asserts fail.
    assert recorded[0]["passed"] is True
    assert recorded[0]["response"] == [1, 2]
