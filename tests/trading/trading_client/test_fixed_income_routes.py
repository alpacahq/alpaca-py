from alpaca.common.enums import BaseURL
from alpaca.trading.client import TradingClient
from alpaca.trading.models import USCorporatesResp, USTreasuriesResp
from alpaca.trading.requests import GetUSCorporatesRequest, GetUSTreasuriesRequest


def test_get_us_treasuries(reqmock, trading_client: TradingClient):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/assets/fixed_income/us_treasuries"
        "?subtype=note&bond_status=outstanding",
        json={"us_treasuries": []},
    )

    response = trading_client.get_us_treasuries(
        GetUSTreasuriesRequest(subtype="note", bond_status="outstanding")
    )

    assert response == USTreasuriesResp(us_treasuries=[])


def test_get_us_corporates(reqmock, trading_client: TradingClient):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/assets/fixed_income/us_corporates"
        "?bond_status=outstanding&tickers=MSFT",
        json={"us_corporates": []},
    )

    response = trading_client.get_us_corporates(
        GetUSCorporatesRequest(bond_status="outstanding", tickers="MSFT")
    )

    assert response == USCorporatesResp(us_corporates=[])
