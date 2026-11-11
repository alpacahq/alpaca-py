"""Consumer scenarios: SDK code written the way users write it.

Rules (see ``consumer_checks/README.md``):

* Import only from public ``alpaca`` modules, never from ``tests/`` or private
  (``_``-prefixed) modules.
* Use only API that exists in the release named in ``consumer_checks/BASELINE``,
  unless the scenario sets ``since`` (see ``Scenario``).
* Keep requests deterministic: fixed dates, explicit ``start``/``end``, and
  ``ctx.unique_id()`` for anything random. Replay compares every request.
* Assert the behavior a user relies on (``isinstance``, field values, raised
  exceptions) and return the outputs worth snapshotting.
"""

from __future__ import annotations

import importlib
import pkgutil
import uuid
from dataclasses import dataclass
from functools import cached_property
from typing import Any, Callable, Dict, Mapping, Optional, Sequence, Tuple

from alpaca.data.historical import (
    CryptoHistoricalDataClient,
    NewsClient,
    OptionHistoricalDataClient,
    ScreenerClient,
    StockHistoricalDataClient,
)
from alpaca.data.historical.corporate_actions import CorporateActionsClient
from alpaca.trading.client import TradingClient

ScenarioFn = Callable[["Context"], Mapping[str, Any]]


@dataclass(frozen=True)
class Scenario:
    """One registered scenario.

    Attributes:
        name: ``<module>.<function>``, also the recording file name.
        fn: The scenario function.
        covers: ``Client.method`` names the scenario exercises, used by
            ``check_coverage.py``.
        since: The first release with the API this scenario uses, when that is
            newer than BASELINE (for example ``"0.46.0"`` for API added on
            master). Until BASELINE reaches it, the scenario is recorded with
            this checkout's SDK, so new API is protected from the PR that adds
            it. Once BASELINE reaches it, it is re-recorded with the release.
        stub_responses: Fixed responses served in order instead of calling the
            API, in every mode. For behavior the API cannot be made to show on
            demand (429, 5xx, non-JSON errors). Each is ``{"status": int}``
            plus ``"json": ...`` or ``"text": ...``.
    """

    name: str
    fn: ScenarioFn
    covers: Tuple[str, ...]
    since: Optional[str] = None
    stub_responses: Tuple[Mapping[str, Any], ...] = ()


SCENARIOS: Dict[str, Scenario] = {}


def scenario(
    *,
    covers: Sequence[str],
    since: Optional[str] = None,
    stub_responses: Sequence[Mapping[str, Any]] = (),
) -> Callable[[ScenarioFn], ScenarioFn]:
    """Register a scenario function and the client methods it exercises."""

    def register(fn: ScenarioFn) -> ScenarioFn:
        name = f"{fn.__module__.rsplit('.', 1)[-1]}.{fn.__name__}"
        if name in SCENARIOS:
            raise ValueError(f"duplicate consumer scenario {name!r}")
        SCENARIOS[name] = Scenario(
            name=name,
            fn=fn,
            covers=tuple(covers),
            since=since,
            stub_responses=tuple(stub_responses),
        )
        return fn

    return register


class Context:
    """What a scenario gets: SDK clients plus mode-aware helpers.

    The harness builds one per run. In replay mode the clients get fake keys and
    every HTTP call is served from the recording.
    """

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        *,
        sleep: Callable[[float], None],
        unique_id: Callable[[str], str],
    ) -> None:
        self._api_key = api_key
        self._secret_key = secret_key
        self._sleep = sleep
        self._unique_id = unique_id

    @cached_property
    def trading(self) -> TradingClient:
        return TradingClient(self._api_key, self._secret_key, paper=True)

    @cached_property
    def stock_data(self) -> StockHistoricalDataClient:
        return StockHistoricalDataClient(self._api_key, self._secret_key)

    @cached_property
    def crypto_data(self) -> CryptoHistoricalDataClient:
        return CryptoHistoricalDataClient(self._api_key, self._secret_key)

    @cached_property
    def option_data(self) -> OptionHistoricalDataClient:
        return OptionHistoricalDataClient(self._api_key, self._secret_key)

    @cached_property
    def news(self) -> NewsClient:
        return NewsClient(self._api_key, self._secret_key)

    @cached_property
    def screener(self) -> ScreenerClient:
        return ScreenerClient(self._api_key, self._secret_key)

    @cached_property
    def corporate_actions(self) -> CorporateActionsClient:
        return CorporateActionsClient(self._api_key, self._secret_key)

    # raw_data=True: methods return the API's JSON (dicts and lists) instead of
    # models. Users who opt in index those directly.
    @cached_property
    def raw_trading(self) -> TradingClient:
        return TradingClient(self._api_key, self._secret_key, paper=True, raw_data=True)

    @cached_property
    def raw_stock_data(self) -> StockHistoricalDataClient:
        return StockHistoricalDataClient(self._api_key, self._secret_key, raw_data=True)

    @cached_property
    def raw_crypto_data(self) -> CryptoHistoricalDataClient:
        return CryptoHistoricalDataClient(
            self._api_key, self._secret_key, raw_data=True
        )

    @cached_property
    def raw_option_data(self) -> OptionHistoricalDataClient:
        return OptionHistoricalDataClient(
            self._api_key, self._secret_key, raw_data=True
        )

    @cached_property
    def raw_news(self) -> NewsClient:
        return NewsClient(self._api_key, self._secret_key, raw_data=True)

    @cached_property
    def raw_screener(self) -> ScreenerClient:
        return ScreenerClient(self._api_key, self._secret_key, raw_data=True)

    @cached_property
    def raw_corporate_actions(self) -> CorporateActionsClient:
        return CorporateActionsClient(self._api_key, self._secret_key, raw_data=True)

    @cached_property
    def trading_with_invalid_keys(self) -> TradingClient:
        """A client whose keys the API rejects, in every mode."""
        return TradingClient("INVALID-KEY-ID", "invalid-secret-key", paper=True)

    def sleep(self, seconds: float) -> None:
        """Wait between polls. A no-op in replay mode."""
        self._sleep(seconds)

    def unique_id(self, label: str) -> str:
        """A fresh id when recording or live, the recorded one in replay mode."""
        return self._unique_id(label)


def new_unique_id() -> str:
    return uuid.uuid4().hex


def load_all() -> Dict[str, Scenario]:
    """Import every scenario module in this package and return the registry."""
    for module in pkgutil.iter_modules(__path__):
        if not module.name.startswith("_"):
            importlib.import_module(f"{__name__}.{module.name}")
    return SCENARIOS
