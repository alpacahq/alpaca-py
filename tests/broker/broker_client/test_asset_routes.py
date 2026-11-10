from alpaca.broker.client import BrokerClient
from alpaca.broker.models import Asset as BrokerAsset
from alpaca.common.enums import BaseURL
from alpaca.trading.models import Asset

ASSET = """
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
          "margin_requirement_long": "30",
          "margin_requirement_short": "100",
          "attributes": ["has_options"]
        }
"""


def test_get_asset_returns_the_broker_asset_on_request(reqmock, client: BrokerClient):
    reqmock.get(f"{BaseURL.BROKER_SANDBOX.value}/v1/assets/AAPL", text=ASSET)

    assert type(client.get_asset("AAPL")) is Asset
    # The Broker spec documents its own Asset for this route.
    generated = client.get_asset("AAPL", generated=True)
    assert type(generated) is BrokerAsset
    assert generated.margin_requirement_long == "30"


def test_get_all_assets_returns_the_broker_asset_on_request(
    reqmock, client: BrokerClient
):
    reqmock.get(f"{BaseURL.BROKER_SANDBOX.value}/v1/assets", text=f"[{ASSET}]")

    assert [type(a) for a in client.get_all_assets()] == [Asset]
    assert [type(a) for a in client.get_all_assets(generated=True)] == [BrokerAsset]
