"""Unit tests for live-test safety gates (no network)."""

from types import SimpleNamespace

import pytest

from tests.live.conftest import pytest_collection_modifyitems


class _Config:
    def __init__(self, *, run_live: bool, allow_mutative: bool) -> None:
        self._options = {
            "--run-live": run_live,
            "--allow-mutative": allow_mutative,
        }

    def getoption(self, name: str) -> bool:
        return self._options[name]


class _Item:
    def __init__(self, *markers: str) -> None:
        self._markers = [SimpleNamespace(name=name) for name in markers]
        self.added_markers = []

    def iter_markers(self):
        return iter(self._markers)

    def add_marker(self, marker) -> None:
        self.added_markers.append(marker)


@pytest.mark.parametrize(
    "environment_variable",
    ["ALPACA_TRADING_PAPER", "ALPACA_BROKER_SANDBOX"],
)
def test_mutative_live_tests_reject_production_overrides(
    monkeypatch: pytest.MonkeyPatch, environment_variable: str
) -> None:
    monkeypatch.delenv("ALPACA_TRADING_PAPER", raising=False)
    monkeypatch.delenv("ALPACA_BROKER_SANDBOX", raising=False)
    monkeypatch.setenv(environment_variable, "false")

    config = _Config(run_live=True, allow_mutative=True)
    item = _Item("live_mutative")

    with pytest.raises(pytest.UsageError, match=environment_variable):
        pytest_collection_modifyitems(config, [item])


def test_mutative_live_tests_allow_paper_and_sandbox(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ALPACA_TRADING_PAPER", raising=False)
    monkeypatch.delenv("ALPACA_BROKER_SANDBOX", raising=False)

    config = _Config(run_live=True, allow_mutative=True)
    item = _Item("live_mutative")

    pytest_collection_modifyitems(config, [item])

    assert item.added_markers == []


def test_read_only_live_tests_allow_production_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ALPACA_TRADING_PAPER", "false")

    config = _Config(run_live=True, allow_mutative=False)
    item = _Item("live")

    pytest_collection_modifyitems(config, [item])

    assert item.added_markers == []
