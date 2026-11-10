import json
from urllib.parse import parse_qs, urlparse

from alpaca.common.enums import BaseURL
from alpaca.trading.client import TradingClient
from alpaca.trading.models import (
    CryptoTransfer,
    CryptoWallet,
    SearchVASPsResponse,
    WalletFeeEstimateResponse,
    WhitelistedAddress,
)
from alpaca.trading.requests import (
    CreateWhitelistedAddressRequest,
    GetCryptoWalletsRequest,
    GetWalletFeeEstimateRequest,
    SearchVASPsRequest,
    TravelRuleInfo,
    UpdateWhitelistedAddressTravelRuleInfoRequest,
)

_PAPER = BaseURL.TRADING_PAPER.value
_TRANSFER = {
    "id": "00000000-0000-4000-8000-000000000010",
    "amount": "1",
    "asset": "USDC",
    "chain": "ETH",
    "created_at": "2026-01-02T15:04:05Z",
    "direction": "OUTGOING",
    "status": "PROCESSING",
}


def test_crypto_wallet_routes(reqmock, trading_client: TradingClient):
    reqmock.get(
        f"{_PAPER}/v2/wallets",
        json={"address": "addr", "chain": "ETH", "created_at": "2026-01-02T15:04:05Z"},
    )
    reqmock.get(
        f"{_PAPER}/v2/wallets/fees/estimate",
        json={"fee": "0.01", "network_fee": "0.02"},
    )
    reqmock.get(f"{_PAPER}/v2/wallets/transfers", json=_TRANSFER)
    reqmock.get(f"{_PAPER}/v2/wallets/transfers/transfer-1", json=_TRANSFER)
    reqmock.get(
        f"{_PAPER}/v2/wallets/travel-rule/vasps",
        json={
            "page": 0,
            "pages": 1,
            "total": 1,
            "vasps": [{"id": "vasp-1", "name": "Example"}],
        },
    )

    wallet = trading_client.list_crypto_funding_wallets(
        GetCryptoWalletsRequest(asset="USDC", chain="ETH", network="ethereum")
    )
    estimate = trading_client.get_wallet_fee_estimate(
        GetWalletFeeEstimateRequest(asset="USDC", amount="10")
    )
    transfers = trading_client.list_crypto_funding_transfers()
    transfer = trading_client.get_crypto_funding_transfer("transfer-1")
    vasps = trading_client.search_vasps(
        SearchVASPsRequest(page=0, per_page=10, includeSubsidiaryVASPs=False)
    )

    assert isinstance(wallet, CryptoWallet)
    assert wallet.chain == "ETH"
    assert isinstance(estimate, WalletFeeEstimateResponse)
    assert estimate.fee == "0.01"
    assert isinstance(transfers, CryptoTransfer)
    assert isinstance(transfer, CryptoTransfer)
    assert isinstance(vasps, SearchVASPsResponse)
    assert vasps.vasps[0].name == "Example"
    wallet_query = parse_qs(urlparse(reqmock.request_history[0].url).query)
    assert wallet_query["chain"] == ["ETH"]
    assert wallet_query["network"] == ["ethereum"]
    estimate_query = parse_qs(urlparse(reqmock.request_history[1].url).query)
    assert estimate_query["asset"] == ["USDC"]
    assert estimate_query["amount"] == ["10"]
    assert urlparse(reqmock.request_history[2].url).path == "/v2/wallets/transfers"
    assert (
        urlparse(reqmock.request_history[3].url).path
        == "/v2/wallets/transfers/transfer-1"
    )
    vasp_query = parse_qs(urlparse(reqmock.request_history[4].url).query)
    assert vasp_query["includeSubsidiaryVASPs"] == ["false"]
    assert vasp_query["page"] == ["0"]


def test_list_endpoints_accept_the_array_payloads_described_by_the_spec(
    reqmock, trading_client: TradingClient
):
    wallet = {
        "address": "addr",
        "chain": "ETH",
        "created_at": "2026-01-02T15:04:05Z",
    }
    address = {
        "id": "sample-id",
        "address": "addr",
        "asset": "USDT",
        "chain": "ETH",
        "created_at": "2026-01-02T15:04:05Z",
        "status": "PENDING",
    }
    reqmock.get(f"{_PAPER}/v2/wallets", json=[wallet])
    reqmock.get(f"{_PAPER}/v2/wallets/transfers", json=[_TRANSFER])
    reqmock.get(f"{_PAPER}/v2/wallets/whitelists", json=[address])

    wallets = trading_client.list_crypto_funding_wallets()
    transfers = trading_client.list_crypto_funding_transfers()
    addresses = trading_client.list_whitelisted_addresses()

    assert isinstance(wallets, list)
    assert isinstance(wallets[0], CryptoWallet)
    assert wallets[0].chain == "ETH"
    assert isinstance(transfers, list)
    assert isinstance(transfers[0], CryptoTransfer)
    assert isinstance(addresses, list)
    assert isinstance(addresses[0], WhitelistedAddress)
    assert reqmock.request_history[0].qs == {}


def test_whitelisted_address_routes(reqmock, trading_client: TradingClient):
    address = {
        "id": "sample-id",
        "address": "addr",
        "asset": "USDT",
        "chain": "ETH",
        "created_at": "2026-01-02T15:04:05Z",
        "status": "PENDING",
    }
    reqmock.get(f"{_PAPER}/v2/wallets/whitelists", json=address)
    reqmock.post(f"{_PAPER}/v2/wallets/whitelists", json=address)
    reqmock.delete(
        f"{_PAPER}/v2/wallets/whitelists/sample-id", status_code=200, text=""
    )
    reqmock.patch(
        f"{_PAPER}/v2/wallets/whitelists/00000000-0000-4000-8000-000000000000/travel-rule-info",
        status_code=200,
        text="",
    )

    listed = trading_client.list_whitelisted_addresses()
    created = trading_client.create_whitelisted_address(
        CreateWhitelistedAddressRequest(
            address="addr",
            asset="USDT",
            chain="ETH",
            travel_rule_info=TravelRuleInfo(
                beneficiary_entity_name="Alpaca Crypto LLC"
            ),
        )
    )
    assert trading_client.delete_whitelisted_address("sample-id") is None
    assert (
        trading_client.update_whitelisted_address_travel_rule_info(
            "00000000-0000-4000-8000-000000000000",
            UpdateWhitelistedAddressTravelRuleInfoRequest(
                travel_rule_info=TravelRuleInfo(beneficiary_is_self_hosted=True)
            ),
        )
        is None
    )

    assert isinstance(listed, WhitelistedAddress)
    assert isinstance(created, WhitelistedAddress)
    assert reqmock.request_history[1].method == "POST"
    assert json.loads(reqmock.request_history[1].body)["chain"] == "ETH"
    assert reqmock.request_history[2].method == "DELETE"
    assert urlparse(reqmock.request_history[2].url).path == (
        "/v2/wallets/whitelists/sample-id"
    )
    assert reqmock.request_history[3].method == "PATCH"
    assert json.loads(reqmock.request_history[3].body) == {
        "travel_rule_info": {"beneficiary_is_self_hosted": True}
    }
