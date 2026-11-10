import json
from urllib.parse import parse_qs, urlparse

from alpaca.common.enums import BaseURL
from alpaca.trading.client import TradingClient
from alpaca.trading.models import TokenizationMintResponse, TokenizationRequest
from alpaca.trading.requests import (
    GetTokenizationRequestsRequest,
    TokenizationMintRequest,
)

_PAPER = BaseURL.TRADING_PAPER.value
_TOKENIZATION = {
    "tokenization_request_id": "5b1d6a3e-7f0a-4d2c-b8e1-9e6f1c0d2c4a",
    "created_at": "2026-01-02T15:04:05Z",
    "type": "mint",
    "status": "pending",
    "underlying_symbol": "AAPL",
    "token_symbol": "AAPLx",
    "qty": "10",
    "issuer": "xstocks",
    "network": "solana",
    "wallet_address": "wallet",
}


def test_tokenization_routes(reqmock, trading_client: TradingClient):
    request_id = "00000000-0000-4000-8000-000000000000"
    reqmock.post(f"{_PAPER}/v2/tokenization/mint", json=_TOKENIZATION)
    reqmock.get(f"{_PAPER}/v2/tokenization/requests", json=[_TOKENIZATION])
    reqmock.get(f"{_PAPER}/v2/tokenization/requests/{request_id}", json=_TOKENIZATION)
    reqmock.get(
        f"{_PAPER}/v2/tokenization/requests:by_client_request_id",
        json=_TOKENIZATION,
    )

    minted = trading_client.tokenization_mint(
        TokenizationMintRequest(
            issuer="xstocks",
            network="solana",
            qty="10",
            underlying_symbol="AAPL",
            wallet_address="wallet",
        )
    )
    listed = trading_client.get_tokenization_requests(
        GetTokenizationRequestsRequest(
            type="mint", status="pending", issuer="xstocks", network="solana"
        )
    )
    fetched = trading_client.get_tokenization_request(request_id)
    by_client = trading_client.get_tokenization_request_by_client_request_id(
        "ap-request-2025-11-04-001"
    )

    assert isinstance(minted, TokenizationMintResponse)
    assert isinstance(listed[0], TokenizationRequest)
    assert isinstance(fetched, TokenizationRequest)
    assert isinstance(by_client, TokenizationRequest)
    assert reqmock.request_history[0].method == "POST"
    assert urlparse(reqmock.request_history[0].url).path == "/v2/tokenization/mint"
    assert json.loads(reqmock.request_history[0].body)["underlying_symbol"] == "AAPL"
    listed_query = parse_qs(urlparse(reqmock.request_history[1].url).query)
    assert listed_query["type"] == ["mint"]
    assert listed_query["network"] == ["solana"]
    assert urlparse(reqmock.request_history[2].url).path == (
        f"/v2/tokenization/requests/{request_id}"
    )
    by_client_query = parse_qs(urlparse(reqmock.request_history[3].url).query)
    assert by_client_query["client_request_id"] == ["ap-request-2025-11-04-001"]
