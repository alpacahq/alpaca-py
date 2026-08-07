"""Fixtures and gates for opt-in live Alpaca API smoke tests."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import pytest

from alpaca.broker.client import BrokerClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.historical.crypto import CryptoHistoricalDataClient
from alpaca.data.historical.news import NewsClient
from alpaca.trading.client import TradingClient

from tests.live.recording import (
    attach_http_capture,
    format_exchange_report,
    invoke_and_record,
    write_artifact,
    write_summary,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT_DIR = REPO_ROOT / "artifacts" / "live_probe"


def _env_flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _load_dotenv(path: Path) -> None:
    """Load KEY=VALUE pairs from .env without overriding existing env vars."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("live")
    group.addoption(
        "--run-live",
        action="store_true",
        default=False,
        help="Run @pytest.mark.live tests against real Alpaca APIs",
    )
    group.addoption(
        "--allow-mutative",
        action="store_true",
        default=False,
        help="Allow @pytest.mark.live_mutative tests (requires --run-live)",
    )
    group.addoption(
        "--live-out-dir",
        action="store",
        default=None,
        help="Directory for live proof artifacts (default: artifacts/live_probe)",
    )
    group.addoption(
        "--live-quiet",
        action="store_true",
        default=False,
        help="Do not print redacted request/response to the console during live runs",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "live: live API smoke tests (requires --run-live)"
    )
    config.addinivalue_line(
        "markers",
        "live_mutative: mutative live API tests (requires --run-live --allow-mutative)",
    )
    if _run_live_enabled(config):
        _load_dotenv(REPO_ROOT / ".env")


def _run_live_enabled(config: pytest.Config) -> bool:
    return bool(config.getoption("--run-live")) or _env_flag("ALPACA_RUN_LIVE")


def pytest_collection_modifyitems(
    config: pytest.Config, items: List[pytest.Item]
) -> None:
    run_live = _run_live_enabled(config)
    allow_mutative = bool(config.getoption("--allow-mutative"))
    skip_live = pytest.mark.skip(
        reason="live tests require --run-live or ALPACA_RUN_LIVE=1"
    )
    skip_mutative = pytest.mark.skip(
        reason="mutative live tests require --allow-mutative"
    )

    for item in items:
        markers = {m.name for m in item.iter_markers()}
        if "live_mutative" in markers:
            if not run_live:
                item.add_marker(skip_live)
            elif not allow_mutative:
                item.add_marker(skip_mutative)
        elif "live" in markers:
            if not run_live:
                item.add_marker(skip_live)


def pytest_sessionstart(session: pytest.Session) -> None:
    session.config._live_results = []  # type: ignore[attr-defined]
    session.config._live_run_dir = None  # type: ignore[attr-defined]
    if not _run_live_enabled(session.config):
        return
    out = session.config.getoption("--live-out-dir")
    root = Path(out) if out else DEFAULT_OUT_DIR
    run_dir = root / datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    run_dir.mkdir(parents=True, exist_ok=True)
    session.config._live_run_dir = run_dir  # type: ignore[attr-defined]


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    run_dir = getattr(session.config, "_live_run_dir", None)
    results = getattr(session.config, "_live_results", None)
    if run_dir is not None and results is not None:
        write_summary(Path(run_dir), list(results))


def _require_pair(
    key_names: Tuple[str, ...], secret_names: Tuple[str, ...]
) -> Tuple[str, str]:
    key = next((os.environ[n] for n in key_names if os.environ.get(n)), None)
    secret = next((os.environ[n] for n in secret_names if os.environ.get(n)), None)
    if not key or not secret:
        raise pytest.UsageError(
            "Live credentials missing. Set "
            f"{key_names[0]} and {secret_names[0]} "
            "(or load them via a gitignored .env). "
            "See tests/live/README.md."
        )
    return key, secret


@pytest.fixture(scope="session")
def live_run_dir(pytestconfig: pytest.Config) -> Path:
    run_dir = getattr(pytestconfig, "_live_run_dir", None)
    if run_dir is None:
        pytest.skip("live run directory only available with --run-live")
    return Path(run_dir)


@pytest.fixture
def http_capture() -> Dict[str, Any]:
    return {"status_code": None, "body": None, "request": None}


@pytest.fixture(scope="session")
def trading_api_credentials() -> Tuple[str, str]:
    return _require_pair(
        ("APCA_API_KEY_ID", "ALPACA_API_KEY_ID"),
        ("APCA_API_SECRET_KEY", "ALPACA_API_SECRET_KEY"),
    )


@pytest.fixture(scope="session")
def broker_api_credentials() -> Tuple[str, str]:
    return _require_pair(
        ("ALPACA_BROKER_API_KEY", "APCA_BROKER_API_KEY"),
        ("ALPACA_BROKER_API_SECRET", "APCA_BROKER_SECRET_KEY"),
    )


@pytest.fixture(scope="session")
def trading_paper() -> bool:
    # Default paper=True; set ALPACA_TRADING_PAPER=false for live trading API.
    if "ALPACA_TRADING_PAPER" not in os.environ:
        return True
    return _env_flag("ALPACA_TRADING_PAPER")


@pytest.fixture(scope="session")
def broker_sandbox() -> bool:
    if "ALPACA_BROKER_SANDBOX" not in os.environ:
        return True
    return _env_flag("ALPACA_BROKER_SANDBOX")


@pytest.fixture
def trading_client_live(
    trading_api_credentials: Tuple[str, str],
    trading_paper: bool,
    http_capture: Dict[str, Any],
) -> TradingClient:
    key, secret = trading_api_credentials
    client = TradingClient(api_key=key, secret_key=secret, paper=trading_paper)
    attach_http_capture(client._session, http_capture)
    return client


@pytest.fixture
def stock_client_live(
    trading_api_credentials: Tuple[str, str],
    http_capture: Dict[str, Any],
) -> StockHistoricalDataClient:
    key, secret = trading_api_credentials
    client = StockHistoricalDataClient(api_key=key, secret_key=secret)
    attach_http_capture(client._session, http_capture)
    return client


@pytest.fixture
def crypto_client_live(
    trading_api_credentials: Tuple[str, str],
    http_capture: Dict[str, Any],
) -> CryptoHistoricalDataClient:
    key, secret = trading_api_credentials
    client = CryptoHistoricalDataClient(api_key=key, secret_key=secret)
    attach_http_capture(client._session, http_capture)
    return client


@pytest.fixture
def news_client_live(
    trading_api_credentials: Tuple[str, str],
    http_capture: Dict[str, Any],
) -> NewsClient:
    key, secret = trading_api_credentials
    client = NewsClient(api_key=key, secret_key=secret)
    attach_http_capture(client._session, http_capture)
    return client


@pytest.fixture
def broker_client_live(
    broker_api_credentials: Tuple[str, str],
    broker_sandbox: bool,
    http_capture: Dict[str, Any],
) -> BrokerClient:
    key, secret = broker_api_credentials
    client = BrokerClient(api_key=key, secret_key=secret, sandbox=broker_sandbox)
    attach_http_capture(client._session, http_capture)
    return client


@pytest.fixture
def record_live(
    request: pytest.FixtureRequest,
    live_run_dir: Path,
    http_capture: Dict[str, Any],
    pytestconfig: pytest.Config,
    capsys: pytest.CaptureFixture[str],
):
    """Record a proof artifact and print redacted request/response to the console."""

    def _record(
        method: str,
        response: Any = None,
        *,
        passed: bool = True,
        error: Optional[str] = None,
        status_code: Optional[int] = None,
        response_body: Any = None,
        request_data: Optional[Dict[str, Any]] = None,
    ) -> Path:
        # Prefer explicit response/response_body so tests can truncate large payloads.
        if response_body is not None:
            body = response_body
        elif response is not None:
            body = response
        else:
            body = http_capture.get("body")
        code = (
            status_code if status_code is not None else http_capture.get("status_code")
        )
        captured_request = (
            request_data
            if request_data is not None
            else http_capture.get("request")
        )
        path = write_artifact(
            live_run_dir,
            test_id=request.node.nodeid,
            method=method,
            passed=passed,
            status_code=code,
            response_body=body,
            request=captured_request,
            error=error,
        )
        if not pytestconfig.getoption("--live-quiet"):
            report = format_exchange_report(
                method=method,
                request=captured_request,
                status_code=code,
                response_body=body,
                error=error,
                passed=passed,
            )
            # Bypass pytest output capture so evidence shows without needing -s.
            with capsys.disabled():
                print(report, flush=True)
        results: List[Dict[str, Any]] = pytestconfig._live_results  # type: ignore[attr-defined]
        results.append(
            {
                "id": request.node.nodeid,
                "method": method,
                "passed": passed,
                "error": error,
                "artifact": str(path),
            }
        )
        return path

    return _record


@pytest.fixture
def live_call(record_live):
    """Invoke an SDK method and always record evidence (including failures)."""

    def _call(
        method: str,
        fn: Callable[..., Any],
        *args: Any,
        response_transform: Optional[Callable[[Any], Any]] = None,
        **kwargs: Any,
    ) -> Any:
        return invoke_and_record(
            method,
            fn,
            record_live,
            *args,
            response_transform=response_transform,
            **kwargs,
        )

    return _call


@pytest.fixture
def live_stream_call(record_live):
    """Run a short stream probe and always record WS request/response evidence."""

    from tests.live.streaming import StreamProbeResult, probe_stream

    def _call(
        method: str,
        stream: Any,
        *,
        subscribe: Callable[[Any, Callable], None],
        connect_path: str,
        timeout: Optional[float] = None,
        min_messages: int = 1,
        require_message: bool = True,
    ) -> StreamProbeResult:
        try:
            result = probe_stream(
                stream,
                subscribe=subscribe,
                connect_path=connect_path,
                timeout=timeout,
                min_messages=min_messages,
                require_message=require_message,
            )
        except Exception as exc:
            record_live(
                method,
                passed=False,
                error=f"{type(exc).__name__}: {exc}",
                status_code=None,
            )
            raise

        passed = result.error is None and result.connected
        if require_message:
            passed = passed and len(result.messages) >= min_messages

        record_live(
            method,
            passed=passed,
            error=result.error,
            status_code=None,
            request_data=result.as_request(),
            response_body=result.as_response_body(),
        )
        if not passed:
            raise AssertionError(result.error or "stream probe failed")
        return result

    return _call
