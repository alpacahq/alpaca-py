"""Runs every registered consumer scenario in the mode chosen by --consumer-mode."""

import pytest

import _harness
from scenarios import load_all

SCENARIOS = load_all()


@pytest.mark.parametrize("name", sorted(SCENARIOS))
def test_scenario(name, consumer_settings):
    _harness.check_scenario(SCENARIOS[name], consumer_settings)


def test_every_recording_has_a_scenario(consumer_settings):
    # Deleting or renaming a scenario would otherwise drop its check silently,
    # since tests come from the scenarios, not from the recordings.
    orphans = _harness.orphan_recordings(consumer_settings, SCENARIOS)
    if orphans:
        pytest.fail(
            "recordings with no scenario: "
            + ", ".join(orphans)
            + ". Restore the scenario, or delete the recording in a PR with the "
            "sdk-breaking label that explains what users lose.",
            pytrace=False,
        )
