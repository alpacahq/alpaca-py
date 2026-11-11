"""
Contains tests for Trading API's option routes.
"""

import json
import warnings
from uuid import UUID

import pytest
from pydantic import ValidationError

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


def test_get_option_contract_cash_deliverable_omits_asset_id(
    reqmock, trading_client: TradingClient
):
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
                        "type": "cash",
                        "symbol": "USD",
                        "amount": "2500",
                        "allocation_percentage": "100",
                        "settlement_type": "T+1",
                        "settlement_method": "CAFX",
                        "delayed_settlement": false
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
    assert contract.deliverables is not None
    assert len(contract.deliverables) == 1
    deliverable = contract.deliverables[0]
    assert isinstance(deliverable, OptionDeliverable)
    assert deliverable.type == OptionDeliverableType.CASH
    assert deliverable.symbol == "USD"
    assert deliverable.amount == "2500"
    assert deliverable.allocation_percentage == "100"
    assert deliverable.settlement_type == OptionDeliverableSettlementType.T_PLUS_1
    assert deliverable.settlement_method == OptionDeliverableSettlementMethod.CAFX
    assert deliverable.delayed_settlement is False
    assert deliverable.asset_id is None


def test_get_option_contract_delayed_settlement_null_amount(
    reqmock, trading_client: TradingClient
):
    symbol = "AAPL231103C00170000"
    asset_id = UUID("b0b6dd9d-8b9b-48a9-ba46-b9d54906e415")

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
                        "amount": null,
                        "allocation_percentage": "40",
                        "settlement_type": "T+2",
                        "settlement_method": "BTOB",
                        "delayed_settlement": true,
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
    assert contract.deliverables is not None
    assert len(contract.deliverables) == 1
    deliverable = contract.deliverables[0]
    assert isinstance(deliverable, OptionDeliverable)
    assert deliverable.type == OptionDeliverableType.EQUITY
    assert deliverable.symbol == "AAPL"
    assert deliverable.amount is None
    assert deliverable.allocation_percentage == "40"
    assert deliverable.settlement_type == OptionDeliverableSettlementType.T_PLUS_2
    assert deliverable.settlement_method == OptionDeliverableSettlementMethod.BTOB
    assert deliverable.delayed_settlement is True
    assert deliverable.asset_id == asset_id


def test_get_option_contracts_strike_price_types(
    reqmock, trading_client: TradingClient
):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/options/contracts",
        text="""
        {
            "option_contracts": [],
            "next_page_token": null
        }
        """,
    )

    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        req_float = GetOptionContractsRequest(
            underlying_symbols=["AAPL"],
            strike_price_gte=150.5,
            strike_price_lte=200.0,
        )
        req_int = GetOptionContractsRequest(
            underlying_symbols=["AAPL"],
            strike_price_gte=150,
            strike_price_lte=200,
        )

    assert req_float.strike_price_gte == 150.5
    assert req_float.strike_price_lte == 200.0
    res = trading_client.get_option_contracts(req_float)
    assert isinstance(res, OptionContractsResponse)
    assert reqmock.request_history[0].qs["strike_price_gte"] == ["150.5"]
    assert reqmock.request_history[0].qs["strike_price_lte"] == ["200.0"]

    assert req_int.strike_price_gte == 150.0
    assert req_int.strike_price_lte == 200.0
    trading_client.get_option_contracts(req_int)
    assert reqmock.request_history[1].qs["strike_price_gte"] == ["150.0"]
    assert reqmock.request_history[1].qs["strike_price_lte"] == ["200.0"]

    with pytest.warns(DeprecationWarning, match="strike_price_gte"):
        with pytest.raises(ValidationError):
            GetOptionContractsRequest(strike_price_gte="abc")


def test_get_option_contracts_accepts_string_strike_prices(
    reqmock, trading_client: TradingClient
):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/options/contracts",
        text="""
        {
            "option_contracts": [],
            "next_page_token": null
        }
        """,
    )

    with pytest.warns(DeprecationWarning, match="Pass a float instead") as caught:
        request = GetOptionContractsRequest(
            underlying_symbols=["AAPL"],
            strike_price_gte="150.5",
            strike_price_lte="200",
        )

    assert [str(warning.message) for warning in caught] == [
        "Passing strike_price_gte as str is deprecated since 0.50.0 and will be removed in a future version. Pass a float instead.",
        "Passing strike_price_lte as str is deprecated since 0.50.0 and will be removed in a future version. Pass a float instead.",
    ]
    assert all(warning.filename == __file__ for warning in caught)
    assert request.strike_price_gte == 150.5
    assert request.strike_price_lte == 200.0

    trading_client.get_option_contracts(request)
    assert reqmock.request_history[0].qs["strike_price_gte"] == ["150.5"]
    assert reqmock.request_history[0].qs["strike_price_lte"] == ["200.0"]


def _construct(**fields):
    return GetOptionContractsRequest(**fields)


def _model_validate(**fields):
    return GetOptionContractsRequest.model_validate(fields)


def _model_validate_json(**fields):
    return GetOptionContractsRequest.model_validate_json(json.dumps(fields))


def _assign(**fields):
    request = GetOptionContractsRequest()
    for name, value in fields.items():
        setattr(request, name, value)
    return request


class _SubclassedRequest(GetOptionContractsRequest):
    def __init__(self, **data):
        super().__init__(**data)


@pytest.mark.parametrize(
    "build",
    [_construct, _model_validate, _model_validate_json, _assign, _SubclassedRequest],
    ids=[
        "construct",
        "model_validate",
        "model_validate_json",
        "assignment",
        "subclass",
    ],
)
def test_strike_price_deprecation_warning_points_at_the_caller(build):
    with pytest.warns(DeprecationWarning, match="strike_price_gte") as caught:
        request = build(strike_price_gte="150.5")

    assert request.strike_price_gte == 150.5
    assert [warning.filename for warning in caught] == [__file__]


def test_get_option_contracts_blank_strike_prices_are_unset(
    reqmock, trading_client: TradingClient
):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/options/contracts",
        text="""
        {
            "option_contracts": [],
            "next_page_token": null
        }
        """,
    )

    with pytest.warns(
        DeprecationWarning, match="Pass None to leave it unset"
    ) as caught:
        request = GetOptionContractsRequest(
            underlying_symbols=["AAPL"],
            strike_price_gte="",
            strike_price_lte=" \t",
        )

    assert len(caught) == 2
    assert all(warning.filename == __file__ for warning in caught)
    assert request.strike_price_gte is None
    assert request.strike_price_lte is None

    trading_client.get_option_contracts(request)
    query = reqmock.request_history[0].qs
    assert "strike_price_gte" not in query
    assert "strike_price_lte" not in query
