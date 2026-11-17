"""Runs every registered consumer scenario in the mode chosen by --consumer-mode."""

import pytest

import _harness
from scenarios import load_all

SCENARIOS = load_all()


@pytest.mark.parametrize("name", sorted(SCENARIOS))
def test_scenario(name, consumer_settings):
    _harness.check_scenario(SCENARIOS[name], consumer_settings)


def test_recording_allowlist(consumer_settings):
    """Allowlisted scenarios must exist and must not already be recorded.

    A line stays only while its recording cannot be made. Once the file
    exists, delete the line (see recording_allowlist.txt).
    """
    names = _harness.recording_allowlist()
    unknown = sorted(names - set(SCENARIOS))
    recorded = sorted(
        name
        for name in names
        if (consumer_settings.recordings_dir / f"{name}.json").is_file()
    )
    problems = []
    if unknown:
        problems.append("not a scenario: " + ", ".join(unknown))
    if recorded:
        problems.append(
            "already recorded, remove from recording_allowlist.txt: "
            + ", ".join(recorded)
        )
    if problems:
        pytest.fail("; ".join(problems), pytrace=False)


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
