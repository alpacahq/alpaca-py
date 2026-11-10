import json
from urllib.parse import parse_qs, urlparse

from alpaca.common.enums import BaseURL
from alpaca.trading.client import TradingClient
from alpaca.trading.models import ListLocateQuotesResponse, ListLocatesResponse, Locate
from alpaca.trading.requests import (
    CreateLocateRequest,
    GetLocateQuotesRequest,
    GetLocatesRequest,
)

_PAPER = BaseURL.TRADING_PAPER.value
_LOCATE = {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "symbol": "TSLA",
    "requested_qty": 100,
    "all_or_none": False,
    "status": "active",
    "created_at": "2026-01-02T15:04:05Z",
    "limit_price": "0.05",
}


def _request(reqmock):
    sent = reqmock.request_history[0]
    parsed = urlparse(sent.url)
    body = json.loads(sent.body) if sent.body else None
    return sent.method, parsed.path, parse_qs(parsed.query), body


def test_get_locates_sends_v1_filters_and_parses_response(
    reqmock, trading_client: TradingClient
):
    reqmock.get(
        f"{_PAPER}/v1/locates", json={"locates": [_LOCATE], "next_page_token": None}
    )

    page = trading_client.get_locates(
        GetLocatesRequest(
            symbol="TSLA",
            status="active",
            limit=1000,
            start="2026-01-01",
            end="2026-01-01",
            page_token="next",
        )
    )

    method, path, query, body = _request(reqmock)
    assert method == "GET"
    assert path == "/v1/locates"
    assert body is None
    assert query["symbol"] == ["TSLA"]
    assert query["status"] == ["active"]
    assert query["limit"] == ["1000"]
    assert query["start"] == ["2026-01-01"]
    assert query["end"] == ["2026-01-01"]
    assert query["page_token"] == ["next"]
    assert isinstance(page, ListLocatesResponse)
    assert page.locates[0].symbol == "TSLA"


def test_create_and_get_locate(reqmock, trading_client: TradingClient):
    reqmock.post(f"{_PAPER}/v1/locates", json=_LOCATE)
    reqmock.get(f"{_PAPER}/v1/locates/{_LOCATE['id']}", json=_LOCATE)

    created = trading_client.create_locate(
        CreateLocateRequest(
            symbol="TSLA", qty=100, all_or_none=False, limit_price="0.05"
        )
    )
    fetched = trading_client.get_locate(_LOCATE["id"])

    assert isinstance(created, Locate)
    assert isinstance(fetched, Locate)
    create_request = reqmock.request_history[0]
    assert create_request.method == "POST"
    assert urlparse(create_request.url).path == "/v1/locates"
    assert json.loads(create_request.body) == {
        "symbol": "TSLA",
        "qty": 100,
        "all_or_none": False,
        "limit_price": "0.05",
    }
    assert (
        urlparse(reqmock.request_history[1].url).path == f"/v1/locates/{_LOCATE['id']}"
    )


def test_get_locate_quotes(reqmock, trading_client: TradingClient):
    reqmock.get(
        f"{_PAPER}/v1/locates/quotes",
        json={"quotes": [], "errors": []},
    )

    quotes = trading_client.get_locate_quotes(
        GetLocateQuotesRequest(symbols=["TSLA", "AAPL"])
    )

    method, path, query, _body = _request(reqmock)
    assert method == "GET"
    assert path == "/v1/locates/quotes"
    assert query["symbols"] == ["TSLA,AAPL"]
    assert isinstance(quotes, ListLocateQuotesResponse)


def test_get_locates_honors_raw_data_and_url_override(reqmock):
    client = TradingClient(
        "key-id",
        "secret-key",
        raw_data=True,
        url_override="https://override.example",
    )
    reqmock.get(
        "https://override.example/v1/locates",
        json={"locates": [], "next_page_token": None},
    )

    locates = client.get_locates()

    assert locates == {"locates": [], "next_page_token": None}
    assert urlparse(reqmock.request_history[0].url).path == "/v1/locates"
