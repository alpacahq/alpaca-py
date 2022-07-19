"""
Contains tests for Trading API's asset routes.
"""

from typing import List
from alpaca.common.enums import BaseURL
from alpaca.trading.enums import AssetStatus
from alpaca.trading.requests import GetAssetsRequest
from alpaca.trading.client import TradingClient
from alpaca.trading.models import Asset


def test_get_all_assets(reqmock, trading_client: TradingClient):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER}/v2/assets",
        text="""
        [
            {
              "id": "904837e3-3b76-47ec-b432-046db621571b",
              "class": "us_equity",
              "exchange": "NASDAQ",
              "symbol": "AAPL",
              "name": "Apple Inc. Common Stock",
              "status": "active",
              "tradable": true,
              "marginable": true,
              "shortable": true,
              "easy_to_borrow": true,
              "fractionable": true,
              "last_close_pct_change": "string",
              "last_price": "string"
            }
      ]
      """,
    )

    assets = trading_client.get_all_assets(GetAssetsRequest(status=AssetStatus.ACTIVE))

    assert reqmock.called_once
    assert isinstance(assets, List)
    assert len(assets) == 1
    assert isinstance(assets[0], Asset)


def test_get_asset(reqmock, trading_client: TradingClient):
    symbol = "AAPL"

    reqmock.get(
        f"{BaseURL.TRADING_PAPER}/v2/assets/{symbol}",
        text="""
            {
              "id": "904837e3-3b76-47ec-b432-046db621571b",
              "class": "us_equity",
              "exchange": "NASDAQ",
              "symbol": "AAPL",
              "name": "Apple Inc. Common Stock",
              "status": "active",
              "tradable": true,
              "marginable": true,
              "shortable": true,
              "easy_to_borrow": true,
              "fractionable": true,
              "last_close_pct_change": "string",
              "last_price": "string"
            }
            """,
    )

    asset = trading_client.get_asset(symbol)

    assert reqmock.called_once
    assert isinstance(asset, Asset)
    assert asset.symbol == symbol
