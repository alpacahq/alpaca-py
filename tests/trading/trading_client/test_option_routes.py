"""
Contains tests for Trading API's option routes.
"""

from alpaca.common.enums import BaseURL
from alpaca.trading.requests import GetOptionContractsRequest
from alpaca.trading.client import TradingClient
from alpaca.trading.models import OptionContract, OptionContractsResponse


def test_get_option_contracts(reqmock, trading_client: TradingClient):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/options/contracts?underlying_symbols=AAPL",
        text="""
        {
            "option_contracts": [
                {
                    "id": "00000000-0000-0000-0000-000000000000",
                    "symbol": "AAPL231103C00170000",
                    "name": "AAPL Nov 03 2023 170 Call",
                    "status": "active",
                    "tradable": true,
                    "expiration_date": "2023-11-03",
                    "root_symbol": "AAPL",
                    "underlying_symbol": "AAPL",
                    "underlying_asset_id": "00000000-0000-0000-0000-000000000000",
                    "type": "call",
                    "style": "american",
                    "strike_price": "170",
                    "size": "100",
                    "open_interest": "0",
                    "open_interest_date": "2023-11-03",
                    "close_price": null,
                    "close_price_date": null
                }
            ],
            "next_page_token": null
        }
        """,
    )

    res = trading_client.get_option_contracts(
        GetOptionContractsRequest(underlying_symbols=["AAPL"])
    )

    assert reqmock.called_once
    assert isinstance(res, OptionContractsResponse)
    assert res.next_page_token is None
    assert isinstance(res.option_contracts, list)
    assert len(res.option_contracts) == 1
    assert isinstance(res.option_contracts[0], OptionContract)


def test_get_option_contracts_with_multiple_symbols(
    reqmock, trading_client: TradingClient
):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/options/contracts?underlying_symbols=AAPL,SPY",
        text="""
        {
            "option_contracts": [
                {
                    "id": "00000000-0000-0000-0000-000000000000",
                    "symbol": "AAPL231103C00170000",
                    "name": "AAPL Nov 03 2023 170 Call",
                    "status": "active",
                    "tradable": true,
                    "expiration_date": "2023-11-03",
                    "root_symbol": "AAPL",
                    "underlying_symbol": "AAPL",
                    "underlying_asset_id": "00000000-0000-0000-0000-000000000000",
                    "type": "call",
                    "style": "american",
                    "strike_price": "170",
                    "size": "100",
                    "open_interest": "0",
                    "open_interest_date": "2023-11-03",
                    "close_price": null,
                    "close_price_date": null
                }
            ],
            "next_page_token": "MA=="
        }
        """,
    )

    res = trading_client.get_option_contracts(
        GetOptionContractsRequest(underlying_symbols=["AAPL", "SPY"])
    )

    assert reqmock.called_once
    assert isinstance(res, OptionContractsResponse)
    assert res.next_page_token == "MA=="
    assert isinstance(res.option_contracts, list)
    assert len(res.option_contracts) == 1
    assert isinstance(res.option_contracts[0], OptionContract)


def test_get_option_contract(reqmock, trading_client: TradingClient):
    symbol = "AAPL231103C00170000"

    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/options/contracts/{symbol}",
        text="""
            {
                "id": "00000000-0000-0000-0000-000000000000",
                "symbol": "AAPL231103C00170000",
                "name": "AAPL Nov 03 2023 170 Call",
                "status": "active",
                "tradable": true,
                "expiration_date": "2023-11-03",
                "root_symbol": "AAPL",
                "underlying_symbol": "AAPL",
                "underlying_asset_id": "00000000-0000-0000-0000-000000000000",
                "type": "call",
                "style": "american",
                "strike_price": "170",
                "size": "100",
                "open_interest": "0",
                "open_interest_date": "2023-11-03",
                "close_price": null,
                "close_price_date": null
            }
        """,
    )

    contract = trading_client.get_option_contract(symbol)

    assert reqmock.called_once
    assert isinstance(contract, OptionContract)
    assert contract.symbol == symbol
