from datetime import datetime
import uuid

from alpaca.trading.models import WatchlistWithoutAsset
from alpaca.trading.requests import CreateWatchlistRequest, UpdateWatchlistRequest


def test_create_watchlist_request_symbols_are_optional():
    request = CreateWatchlistRequest(name="Technology")

    assert request.symbols is None
    assert request.to_request_fields() == {"name": "Technology"}


def test_update_watchlist_request_name_remains_optional():
    request = UpdateWatchlistRequest(symbols=["AAPL"])

    assert request.name is None
    assert request.to_request_fields() == {"symbols": ["AAPL"]}


def test_watchlist_without_asset_response_model():
    watchlist = WatchlistWithoutAsset(
        id="7c3ac77f-894c-4c08-987f-18a2e43e8e2a",
        account_id="0d969814-40d6-4b2b-99ac-2e37427f1ad2",
        name="Technology",
        created_at="2022-05-20T16:17:30.159561Z",
        updated_at="2022-05-20T16:17:30.159561Z",
    )

    assert watchlist.name == "Technology"
    assert isinstance(watchlist.id, uuid.UUID)
    assert isinstance(watchlist.account_id, uuid.UUID)
    assert isinstance(watchlist.created_at, datetime)
    assert isinstance(watchlist.updated_at, datetime)
    assert "assets" not in watchlist.model_dump()
