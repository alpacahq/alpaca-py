"""Offline checks for how record and live treat recording_allowlist.txt."""

from pathlib import Path
from types import SimpleNamespace

import pytest

import _harness
from alpaca.common.exceptions import APIError
from scenarios import Scenario

LISTED = "broker_example.listed"
RECORDED = "broker_example.recorded"


def _api_error(status: int) -> APIError:
    http_error = SimpleNamespace(response=SimpleNamespace(status_code=status))
    return APIError('{"message":"unauthorized."}', http_error)


def _scenario(name: str, error: Exception) -> Scenario:
    def fn(ctx):
        raise error

    return Scenario(name=name, fn=fn, covers=(), credentials="broker")


def _settings(tmp_path: Path, mode: str, keys: bool) -> _harness.Settings:
    return _harness.Settings(
        mode=mode,
        update_snapshots=False,
        strict=True,
        recordings_dir=tmp_path,
        baseline="0.0.0",
        broker_api_key="key" if keys else None,
        broker_secret_key="secret" if keys else None,
    )


@pytest.fixture(autouse=True)
def keys_rejected(monkeypatch):
    """What the get_clock probe reports. Tests flip it; nothing calls the API."""
    probe = SimpleNamespace(rejected=True, calls=0)

    def fake(settings, scenario):
        probe.calls += 1
        return probe.rejected

    monkeypatch.setattr(_harness, "recording_allowlist", lambda: {LISTED})
    monkeypatch.setattr(_harness, "_check_sdk", lambda settings, scenario: None)
    monkeypatch.setattr(_harness, "_keys_rejected", fake)
    return probe


@pytest.mark.parametrize("mode", ["live", "record"])
def test_listed_scenario_skips_without_keys(tmp_path, mode):
    scenario = _scenario(LISTED, AssertionError("must not run"))
    with pytest.raises(pytest.skip.Exception, match="are not set"):
        _harness.check_scenario(scenario, _settings(tmp_path, mode, keys=False))


@pytest.mark.parametrize("mode", ["live", "record"])
@pytest.mark.parametrize("status", [401, 403])
def test_listed_scenario_skips_when_keys_are_rejected(tmp_path, mode, status):
    scenario = _scenario(LISTED, _api_error(status))
    with pytest.raises(pytest.skip.Exception, match=f"rejected \\({status}\\)"):
        _harness.check_scenario(scenario, _settings(tmp_path, mode, keys=True))
    assert not (tmp_path / f"{LISTED}.json").exists()


@pytest.mark.parametrize("mode", ["live", "record"])
def test_listed_scenario_fails_on_401_when_the_keys_work(tmp_path, mode, keys_rejected):
    # The broker API answers 401 for an unknown account as well.
    keys_rejected.rejected = False
    error = _api_error(401)
    scenario = _scenario(LISTED, error)
    with pytest.raises(APIError) as raised:
        _harness.check_scenario(scenario, _settings(tmp_path, mode, keys=True))
    assert raised.value is error
    assert keys_rejected.calls == 1


@pytest.mark.parametrize("mode", ["live", "record"])
def test_listed_scenario_still_fails_on_other_errors(tmp_path, mode):
    error = _api_error(422)
    scenario = _scenario(LISTED, error)
    with pytest.raises(APIError) as raised:
        _harness.check_scenario(scenario, _settings(tmp_path, mode, keys=True))
    assert raised.value is error


@pytest.mark.parametrize("mode", ["live", "record"])
def test_recorded_scenario_still_fails_on_rejected_keys(tmp_path, mode):
    error = _api_error(401)
    scenario = _scenario(RECORDED, error)
    with pytest.raises(APIError) as raised:
        _harness.check_scenario(scenario, _settings(tmp_path, mode, keys=True))
    assert raised.value is error


def test_recorded_scenario_still_fails_without_keys(tmp_path):
    scenario = _scenario(RECORDED, AssertionError("must not run"))
    with pytest.raises(pytest.fail.Exception, match="CONSUMER_BROKER_API_KEY"):
        _harness.check_scenario(scenario, _settings(tmp_path, "live", keys=False))
