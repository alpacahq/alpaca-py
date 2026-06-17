"""
Tests for the Trading API's locates routes:
  GET /v1/locates
  POST /v1/locates
  GET /v1/locates/quotes
"""

from datetime import date

from alpaca.common.enums import BaseURL
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import LocateErrorCode, LocateQuoteErrorCode, LocateStatus
from alpaca.trading.models import (
    ErrorResponse,
    Locate,
    LocateError,
    LocateQuote,
    LocateQuoteError,
    LocateQuotesResponse,
    LocatesResponse,
    ListLocateQuotesResponse,
    ListLocatesResponse,
)
from alpaca.trading.requests import (
    CreateLocateRequest,
    GetLocateQuotesRequest,
    GetLocatesRequest,
)

_LOCATE_JSON = """{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "symbol": "TSLA",
    "requested_qty": 100,
    "all_or_none": false,
    "status": "active",
    "created_at": "2026-01-02T15:04:05Z",
    "expires_at": "2026-01-03T01:00:00Z",
    "limit_price": "0.05",
    "located_price": "0.05",
    "located_qty": 100,
    "total_fee": "5.00"
}"""


def test_get_locates_no_filter(reqmock, trading_client: TradingClient):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v1/locates",
        text=f'{{"locates": [{_LOCATE_JSON}], "next_page_token": null}}',
    )

    result = trading_client.get_locates()

    assert reqmock.called_once
    assert isinstance(result, LocatesResponse)
    assert result.next_page_token is None
    assert len(result.locates) == 1
    assert isinstance(result.locates[0], Locate)
    assert result.locates[0].symbol == "TSLA"
    assert result.locates[0].status == LocateStatus.ACTIVE


def test_get_locates_with_filter(reqmock, trading_client: TradingClient):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v1/locates"
        f"?page_token=next&limit=100&status=active&symbol=TSLA&start=2026-01-02&end=2026-01-03",
        text=f'{{"locates": [{_LOCATE_JSON}], "next_page_token": "next-2"}}',
    )

    result = trading_client.get_locates(
        GetLocatesRequest(
            page_token="next",
            limit=100,
            status=LocateStatus.ACTIVE,
            symbol="TSLA",
            start=date(2026, 1, 2),
            end=date(2026, 1, 3),
        )
    )

    assert reqmock.called_once
    assert isinstance(result, LocatesResponse)
    assert result.next_page_token == "next-2"


def test_create_locate(reqmock, trading_client: TradingClient):
    reqmock.post(
        f"{BaseURL.TRADING_PAPER.value}/v1/locates",
        additional_matcher=lambda request: request.json()
        == {
            "symbol": "TSLA",
            "qty": 100,
            "all_or_none": True,
            "limit_price": "0.05",
        },
        text=_LOCATE_JSON,
    )

    result = trading_client.create_locate(
        CreateLocateRequest(
            symbol="TSLA",
            qty=100,
            all_or_none=True,
            limit_price="0.05",
        )
    )

    assert reqmock.called_once
    assert isinstance(result, Locate)
    assert str(result.id) == "550e8400-e29b-41d4-a716-446655440000"
    assert result.located_price == "0.05"


def test_get_locate_quotes(reqmock, trading_client: TradingClient):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v1/locates/quotes?symbols=TSLA%2CMETA",
        text="""{
            "quotes": [
                {
                    "symbol": "TSLA",
                    "available_qty": 1000,
                    "price": "0.0123",
                    "quoted_at": "2026-01-02T15:04:05Z"
                }
            ],
            "errors": [
                {
                    "symbol": "META",
                    "code": "symbol_not_found",
                    "message": "symbol not found"
                }
            ]
        }""",
    )

    result = trading_client.get_locate_quotes(
        GetLocateQuotesRequest(symbols=["TSLA", "META"])
    )

    assert reqmock.called_once
    assert isinstance(result, LocateQuotesResponse)
    assert len(result.quotes) == 1
    assert isinstance(result.quotes[0], LocateQuote)
    assert result.quotes[0].symbol == "TSLA"
    assert result.quotes[0].available_qty == 1000
    assert result.errors[0].code == LocateQuoteErrorCode.SYMBOL_NOT_FOUND


def test_locate_error_models():
    locate_error = LocateError(
        code="invalid_symbols",
        message="symbols must contain at most 100 unique symbols",
    )
    quote_error = LocateQuoteError(
        symbol="META",
        code="threshold_security",
        message="security is on the threshold list and cannot be located",
    )
    generic_error = ErrorResponse(message="Unauthorized")

    assert locate_error.code == LocateErrorCode.INVALID_SYMBOLS
    assert quote_error.code == LocateQuoteErrorCode.THRESHOLD_SECURITY
    assert generic_error.message == "Unauthorized"


def test_locate_response_aliases_match_spec_names():
    assert LocatesResponse is ListLocatesResponse
    assert LocateQuotesResponse is ListLocateQuotesResponse


def test_get_locates_raw(reqmock, trading_client_raw: TradingClient):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v1/locates",
        text=f'{{"locates": [{_LOCATE_JSON}], "next_page_token": null}}',
    )

    result = trading_client_raw.get_locates()

    assert isinstance(result, dict)
    assert "locates" in result


def test_get_locate_quotes_raw(reqmock, trading_client_raw: TradingClient):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v1/locates/quotes?symbols=TSLA",
        text='{"quotes": [{"symbol": "TSLA", "available_qty": 1000, "quoted_at": "2026-01-02T15:04:05Z"}]}',
    )

    result = trading_client_raw.get_locate_quotes(
        GetLocateQuotesRequest(symbols="TSLA")
    )

    assert isinstance(result, dict)
    assert "quotes" in result
