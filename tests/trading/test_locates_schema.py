from datetime import date, datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from alpaca.trading.enums import (
    LocateErrorCode,
    LocateQuoteErrorCode,
    LocateStatus,
)
from alpaca.trading.models import (
    ErrorResponse,
    ListLocateQuotesResponse,
    ListLocatesResponse,
    Locate,
    LocateError,
    LocateQuote,
    LocateQuoteError,
    LocateQuotesResponse,
    LocatesResponse,
)
from alpaca.trading.requests import (
    CreateLocateRequest,
    GetLocateQuotesRequest,
    GetLocatesRequest,
)


def test_locate_enums_match_api_values() -> None:
    assert [status.value for status in LocateStatus] == [
        "active",
        "expired",
        "rejected",
    ]
    assert [code.value for code in LocateErrorCode] == [
        "invalid_input",
        "invalid_request_body",
        "invalid_limit_price",
        "invalid_symbols",
        "symbol_not_found",
        "security_not_found",
        "insufficient_buying_power",
        "easy_to_borrow",
        "threshold_security",
    ]
    assert [code.value for code in LocateQuoteErrorCode] == [
        "symbol_not_found",
        "easy_to_borrow",
        "threshold_security",
        "corporate_action",
    ]


def test_locate_models_parse_api_payloads() -> None:
    now = datetime.now(timezone.utc)
    locate = Locate(
        id=uuid4(),
        symbol="AAPL",
        requested_qty=100,
        all_or_none=True,
        status="active",
        created_at=now,
        located_qty=100,
    )
    quote = LocateQuote(symbol="AAPL", available_qty=250, quoted_at=now, price="0.01")
    quote_error = LocateQuoteError(
        symbol="UNKNOWN",
        code="symbol_not_found",
        message="symbol not found",
    )

    assert locate.status is LocateStatus.ACTIVE
    assert ListLocatesResponse(locates=[locate], next_page_token=None).locates == [
        locate
    ]
    assert ListLocateQuotesResponse(quotes=[quote], errors=[quote_error]).errors == [
        quote_error
    ]


def test_locate_error_models_parse_error_codes() -> None:
    assert ErrorResponse().message is None
    assert (
        LocateError(message="bad request", code="invalid_input").code
        is LocateErrorCode.INVALID_INPUT
    )


def test_locate_response_aliases_are_backwards_compatible() -> None:
    assert LocatesResponse is ListLocatesResponse
    assert LocateQuotesResponse is ListLocateQuotesResponse


def test_list_locates_response_requires_nullable_page_token() -> None:
    with pytest.raises(ValidationError):
        ListLocatesResponse(locates=[])

    assert ListLocatesResponse(locates=[], next_page_token=None).next_page_token is None


def test_locate_requests_serialize_api_fields() -> None:
    assert GetLocatesRequest(
        page_token="next",
        limit=25,
        status=LocateStatus.ACTIVE,
        symbol="AAPL",
        start=date(2026, 1, 1),
        end=date(2026, 1, 31),
    ).to_request_fields() == {
        "page_token": "next",
        "limit": 25,
        "status": "active",
        "symbol": "AAPL",
        "start": "2026-01-01",
        "end": "2026-01-31",
    }
    assert CreateLocateRequest(
        symbol="AAPL", qty=100, all_or_none=None
    ).to_request_fields() == {"symbol": "AAPL", "qty": 100}
    assert GetLocateQuotesRequest(symbols=["AAPL", "MSFT"]).to_request_fields() == {
        "symbols": ["AAPL", "MSFT"]
    }
