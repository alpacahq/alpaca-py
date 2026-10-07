"""
Contains tests for Trading API's option routes.
"""

from alpaca.common.enums import BaseURL
from alpaca.trading.requests import GetOptionContractsRequest
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import (
    OptionDeliverableSettlementMethod,
    OptionDeliverableSettlementType,
    OptionDeliverableType,
)
from alpaca.trading.models import (
    OptionContract,
    OptionContractsResponse,
    OptionDeliverable,
)


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
    assert res.option_contracts[0].ppind is None
    assert res.option_contracts[0].deliverables is None


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


def test_get_option_contracts_with_deliverables_and_ppind(
    reqmock, trading_client: TradingClient
):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/options/contracts",
        text="""
        {
            "option_contracts": [
                {
                    "id": "00000000-0000-0000-0000-000000000000",
                    "symbol": "AAPL231103C00170000",
                    "name": "AAPL Nov 03 2023 170 Call",
                    "status": "active",
                    "tradable": true,
                    "ppind": true,
                    "expiration_date": "2023-11-03",
                    "root_symbol": "AAPL",
                    "underlying_symbol": "AAPL",
                    "underlying_asset_id": "00000000-0000-0000-0000-000000000000",
                    "type": "call",
                    "style": "american",
                    "strike_price": "170",
                    "multiplier": "100",
                    "size": "100",
                    "deliverables": [
                        {
                            "type": "equity",
                            "symbol": "AAPL",
                            "amount": "100",
                            "allocation_percentage": "100",
                            "settlement_type": "T+1",
                            "settlement_method": "CCC",
                            "delayed_settlement": false,
                            "asset_id": "b0b6dd9d-8b9b-48a9-ba46-b9d54906e415"
                        }
                    ],
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
        GetOptionContractsRequest(
            underlying_symbols=["AAPL"],
            show_deliverables=True,
            ppind=True,
        )
    )

    assert reqmock.called_once
    assert reqmock.request_history[0].qs["underlying_symbols"] == ["aapl"]
    assert reqmock.request_history[0].qs["show_deliverables"] == ["true"]
    assert reqmock.request_history[0].qs["ppind"] == ["true"]
    assert isinstance(res, OptionContractsResponse)
    contract = res.option_contracts[0]
    assert contract.ppind is True
    assert contract.deliverables is not None
    assert isinstance(contract.deliverables[0], OptionDeliverable)


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
                "ppind": true,
                "expiration_date": "2023-11-03",
                "root_symbol": "AAPL",
                "underlying_symbol": "AAPL",
                "underlying_asset_id": "00000000-0000-0000-0000-000000000000",
                "type": "call",
                "style": "american",
                "strike_price": "170",
                "multiplier": "100",
                "size": "100",
                "deliverables": [
                    {
                        "type": "equity",
                        "symbol": "AAPL",
                        "amount": "100",
                        "allocation_percentage": "100",
                        "settlement_type": "T+1",
                        "settlement_method": "CCC",
                        "delayed_settlement": false,
                        "asset_id": "b0b6dd9d-8b9b-48a9-ba46-b9d54906e415"
                    }
                ],
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
    assert contract.ppind is True
    assert contract.multiplier == "100"
    assert contract.deliverables is not None
    deliverable = contract.deliverables[0]
    assert isinstance(deliverable, OptionDeliverable)
    assert deliverable.type == OptionDeliverableType.EQUITY
    assert deliverable.symbol == "AAPL"
    assert deliverable.amount == "100"
    assert deliverable.settlement_type == OptionDeliverableSettlementType.T_PLUS_1
    assert deliverable.settlement_method == OptionDeliverableSettlementMethod.CCC
    assert deliverable.delayed_settlement is False
