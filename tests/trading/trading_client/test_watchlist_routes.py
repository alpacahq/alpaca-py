"""
Contains tests for Trading API watchlist routes.
"""

from typing import List

from alpaca.common.enums import BaseURL
from alpaca.trading.client import TradingClient
from alpaca.trading.models import WatchlistWithoutAsset


def test_get_watchlists_returns_summaries_without_assets(
    reqmock, trading_client: TradingClient
):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/watchlists",
        json=[
            {
                "id": "7c3ac77f-894c-4c08-987f-18a2e43e8e2a",
                "account_id": "0d969814-40d6-4b2b-99ac-2e37427f1ad2",
                "created_at": "2022-05-20T16:17:30.159561Z",
                "updated_at": "2022-05-20T16:17:30.159561Z",
                "name": "Technology",
            }
        ],
    )

    watchlists = trading_client.get_watchlists()

    assert reqmock.called_once
    assert isinstance(watchlists, List)
    assert len(watchlists) == 1
    assert type(watchlists[0]) is WatchlistWithoutAsset
    assert "assets" not in watchlists[0].model_dump()
