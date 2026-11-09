import json
import os
from pathlib import Path

import pytest

# Show values when a scenario's own assert fails: pytest only rewrites asserts
# in test files by default. Must run before the scenarios are imported.
pytest.register_assert_rewrite("scenarios")

import _dotenv  # noqa: E402
import _harness  # noqa: E402

HERE = Path(__file__).resolve().parent


def pytest_addoption(parser):
    group = parser.getgroup("consumer checks")
    group.addoption(
        "--consumer-mode",
        choices=("replay", "record", "live", "migrate"),
        default="replay",
        help="replay (default, offline), record (paper API, baseline release), "
        "live (paper API, current SDK) or migrate (offline, baseline release: "
        "upgrade old-format recordings).",
    )
    group.addoption(
        "--consumer-update-snapshots",
        action="store_true",
        help="Replay mode: overwrite output snapshots with what the current SDK "
        "returns. Requests must still match. Needs the sdk-breaking label.",
    )
    group.addoption(
        "--consumer-rerecord",
        action="store_true",
        help="Record mode: also re-record scenarios that already have a "
        "recording. Without it, only missing recordings are made.",
    )
    group.addoption(
        "--consumer-match-sdk",
        action="store_true",
        help="With --consumer-update-snapshots: only scenarios recorded with the "
        "SDK installed here (BASELINE release, or this checkout for `since` "
        "scenarios). Used by `make consumer-refresh`.",
    )
    group.addoption(
        "--consumer-surface-out",
        metavar="PATH",
        help="Replay mode: write what the scenarios exercised of the public SDK "
        "surface to PATH (JSON). Used by check_surface.py.",
    )
    group.addoption(
        "--consumer-strict",
        action="store_true",
        help="Replay mode: fail, instead of skip, scenarios with no recording.",
    )


@pytest.fixture(scope="session")
def consumer_settings(pytestconfig):
    recordings_dir = os.environ.get("CONSUMER_RECORDINGS_DIR")
    keys = _dotenv.find_keys()
    return _harness.Settings(
        mode=pytestconfig.getoption("--consumer-mode"),
        update_snapshots=pytestconfig.getoption("--consumer-update-snapshots"),
        strict=pytestconfig.getoption("--consumer-strict"),
        recordings_dir=(
            Path(recordings_dir) if recordings_dir else HERE / "recordings"
        ),
        baseline=(HERE / "BASELINE").read_text(encoding="utf-8").strip(),
        rerecord=pytestconfig.getoption("--consumer-rerecord"),
        match_sdk=pytestconfig.getoption("--consumer-match-sdk"),
        api_key=keys.api_key,
        secret_key=keys.secret_key,
    )


_PASSED_SCENARIOS = set()


def pytest_configure(config):
    if config.getoption("--consumer-surface-out"):
        import _exercised
        import _surface

        _harness.COLLECTOR = _exercised.Collector(_surface.collect())


def pytest_runtest_logreport(report):
    if report.when == "call" and report.passed and "test_scenario[" in report.nodeid:
        _PASSED_SCENARIOS.add(report.nodeid)


def pytest_sessionfinish(session, exitstatus):
    out = session.config.getoption("--consumer-surface-out")
    if not out or _harness.COLLECTOR is None:
        return
    from scenarios import SCENARIOS

    config = session.config
    # Complete only if every scenario replayed and passed, without rewriting.
    complete = (
        len(_PASSED_SCENARIOS) == len(SCENARIOS)
        and session.testsfailed == 0
        and config.getoption("--consumer-mode") == "replay"
        and not config.getoption("--consumer-update-snapshots")
    )
    Path(out).write_text(
        json.dumps(
            {
                "complete": complete,
                "scenarios": len(_PASSED_SCENARIOS),
                "exercised": sorted(_harness.COLLECTOR.exercised),
            },
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )


def pytest_report_header(config):
    env = _harness.environment()
    mode = config.getoption("--consumer-mode")
    lines = [
        f"consumer checks: mode={mode}, "
        f"alpaca-py {env['alpaca-py']} from {_harness.sdk_location()}",
    ]
    if mode in ("record", "live"):
        lines.append(f"consumer checks: paper keys {_dotenv.find_keys().source}")
    return lines
