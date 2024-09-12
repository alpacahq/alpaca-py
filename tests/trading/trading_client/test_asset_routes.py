"""
Contains tests for Trading API's asset routes.
"""

from typing import List
from alpaca.common.enums import BaseURL
from alpaca.data.enums import Exchange
from alpaca.trading.enums import AssetClass, AssetExchange, AssetStatus
from alpaca.trading.requests import GetAssetsRequest
from alpaca.trading.client import TradingClient
from alpaca.trading.models import Asset


def test_get_all_assets(reqmock, trading_client: TradingClient):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/assets?status=active",
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
              "last_price": "string",
              "attributes": [
                "attribute1",
                "attribute2"
              ]
            }
      ]
      """,
    )

    assets = trading_client.get_all_assets(GetAssetsRequest(status=AssetStatus.ACTIVE))

    assert reqmock.called_once
    assert isinstance(assets, List)
    assert len(assets) == 1
    assert isinstance(assets[0], Asset)
    asset = assets[0]
    assert asset.status == AssetStatus.ACTIVE
    assert asset.attributes == ["attribute1", "attribute2"]


def test_get_all_assets_params(reqmock, trading_client: TradingClient):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/assets?status=active&asset_class=us_equity&exchange=NASDAQ&attributes=attribute1%2Cattribute2",
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
              "last_price": "string",
              "attributes": [
                "attribute1",
                "attribute2"
              ]
            }
      ]
      """,
    )

    assets = trading_client.get_all_assets(
        GetAssetsRequest(
            status=AssetStatus.ACTIVE,
            asset_class=AssetClass.US_EQUITY,
            exchange=AssetExchange.NASDAQ,
            attributes=",".join(["attribute1", "attribute2"]),
        )
    )

    assert reqmock.called_once
    assert isinstance(assets, List)
    assert len(assets) == 1
    assert isinstance(assets[0], Asset)
    asset = assets[0]
    assert asset.status == AssetStatus.ACTIVE
    assert asset.asset_class == AssetClass.US_EQUITY
    assert asset.exchange == AssetExchange.NASDAQ
    assert asset.attributes == ["attribute1", "attribute2"]


def test_get_asset(reqmock, trading_client: TradingClient):
    symbol = "AAPL"

    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/assets/{symbol}",
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
              "last_price": "string",
              "attributes": [
                "attribute1",
                "attribute2"
              ]
            }
            """,
    )

    asset = trading_client.get_asset(symbol)

    assert reqmock.called_once
    assert isinstance(asset, Asset)
    assert asset.symbol == symbol
    assert asset.status == AssetStatus.ACTIVE
    assert asset.attributes == ["attribute1", "attribute2"]
