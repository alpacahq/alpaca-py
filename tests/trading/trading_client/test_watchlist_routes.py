import json
from urllib.parse import parse_qs, urlparse

from alpaca.common.enums import BaseURL
from alpaca.trading.client import TradingClient
from alpaca.trading.models import Watchlist
from alpaca.trading.requests import (
    AddAssetToWatchlistRequest,
    UpdateWatchlistRequest,
)

_PAPER = BaseURL.TRADING_PAPER.value
_WATCHLIST = {
    "id": "00000000-0000-4000-8000-000000000002",
    "account_id": "00000000-0000-4000-8000-000000000001",
    "name": "Tech",
    "created_at": "2026-01-02T15:04:05Z",
    "updated_at": "2026-01-02T15:04:05Z",
}


def test_watchlists_by_name(reqmock, trading_client: TradingClient):
    reqmock.get(f"{_PAPER}/v2/watchlists:by_name", json=_WATCHLIST)
    reqmock.post(f"{_PAPER}/v2/watchlists:by_name", json=_WATCHLIST)
    reqmock.put(f"{_PAPER}/v2/watchlists:by_name", json=_WATCHLIST)
    reqmock.delete(f"{_PAPER}/v2/watchlists:by_name", status_code=204, text="")

    fetched = trading_client.get_watchlist_by_name("Tech")
    added = trading_client.add_asset_to_watchlist_by_name(
        "Tech", AddAssetToWatchlistRequest(symbol="AAPL")
    )
    updated = trading_client.update_watchlist_by_name(
        "Tech", UpdateWatchlistRequest(name="Tech", symbols=["AAPL"])
    )
    assert trading_client.delete_watchlist_by_name("Tech") is None

    assert isinstance(fetched, Watchlist)
    assert isinstance(added, Watchlist)
    assert isinstance(updated, Watchlist)
    assert parse_qs(urlparse(reqmock.request_history[0].url).query)["name"] == ["Tech"]
    assert reqmock.request_history[1].method == "POST"
    assert json.loads(reqmock.request_history[1].body) == {"symbol": "AAPL"}
    assert parse_qs(urlparse(reqmock.request_history[1].url).query)["name"] == ["Tech"]
    assert reqmock.request_history[2].method == "PUT"
    assert json.loads(reqmock.request_history[2].body) == {
        "name": "Tech",
        "symbols": ["AAPL"],
    }
    assert reqmock.request_history[3].method == "DELETE"
    assert parse_qs(urlparse(reqmock.request_history[3].url).query)["name"] == ["Tech"]
