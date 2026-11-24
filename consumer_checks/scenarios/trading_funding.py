"""Crypto funding, tokenization and do-not-exercise, added in 0.50.0.

The paper account used by these checks cannot mint tokens, whitelist a
withdrawal address, or submit a do-not-exercise instruction on demand. Fixed
responses exercise the success paths. These scenarios stay stubbed in every
mode, including live mode, and are recorded with this checkout's SDK until
BASELINE reaches 0.50.0.

New SDK imports stay inside the scenarios so BASELINE can collect this module.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict
from uuid import UUID

from . import Context, scenario

SINCE = "0.50.0"
EMPTY = {"status": 200, "text": ""}
CREATED_AT = "2026-01-02T15:04:05Z"
WALLET_ADDRESS = "5dXY1aH2tQpV3wXmJg6Z7c8B4nKvF9bA1pQrSt2uVwYxXz"
CONTRACT_ID = UUID("00000000-0000-4000-8000-000000000000")
TOKENIZATION_ID = "5b1d6a3e-7f0a-4d2c-b8e1-9e6f1c0d2c4a"
TRANSFER_ID = "00000000-0000-4000-8000-000000000010"
ADDRESS_ID = "00000000-0000-4000-8000-000000000020"
CLIENT_REQUEST_ID = "ap-request-2025-11-04-001"
VASP_DID = "did:ethr:0xf1c002f9e7ca88018d6dcf1e86403fb2f5f055f4"
TRAVEL_RULE = {
    "beneficiary_country_of_residence": "US",
    "beneficiary_entity_name": "Alpaca Crypto LLC",
    "beneficiary_family_name": "Doe",
    "beneficiary_geographic_address_building_number": "1",
    "beneficiary_geographic_address_country": "US",
    "beneficiary_geographic_address_post_code": "10001",
    "beneficiary_geographic_address_street_name": "Main Street",
    "beneficiary_geographic_address_town_name": "New York",
    "beneficiary_given_name": "John",
    "beneficiary_is_self_hosted": True,
    "beneficiary_manual_entry": {
        "vasp_name": "Alpaca",
        "vasp_website": "https://alpaca.markets",
    },
    "beneficiary_vasp_id": VASP_DID,
}
TOKENIZATION = {
    "tokenization_request_id": TOKENIZATION_ID,
    "created_at": CREATED_AT,
    "updated_at": "2026-01-02T16:04:05Z",
    "type": "mint",
    "status": "pending",
    "transfer_status": "pending",
    "underlying_symbol": "AAPL",
    "token_symbol": "AAPLx",
    "qty": "10",
    "fees": "0.01",
    "issuer": "xstocks",
    "issuer_request_id": "issuer-req-1",
    "network": "solana",
    "wallet_address": WALLET_ADDRESS,
    "tx_hash": "5KJw8f1d2c4a9e6f1c0d2c4a7f0a4d2cb8e19e6f1c0d2c4a",
    "client_request_id": CLIENT_REQUEST_ID,
    "client_account_id": "06b9d76e-1733-460c-844e-48d1ae0f10c3",
    "client_external_account_id": "AP-EXT-001",
}
WALLET = {
    "address": "0x1111111111111111111111111111111111111111",
    "chain": "ETH",
    "created_at": CREATED_AT,
}
TRANSFER = {
    "id": TRANSFER_ID,
    "amount": "1",
    "asset": "USDC",
    "chain": "ETH",
    "created_at": CREATED_AT,
    "direction": "OUTGOING",
    "fees": "0.01",
    "from_address": "0x2222222222222222222222222222222222222222",
    "network_fee": "0.02",
    "status": "PROCESSING",
    "to_address": WALLET_ADDRESS,
    "tx_hash": "0xabc",
    "usd_value": "1.00",
}
FEE = {"fee": "0.0505", "network_fee": "0.0825"}
VASP = {
    "id": "vasp-1",
    "name": "Example Exchange",
    "address": "1 Main Street",
    "city": "New York",
    "country": "US",
    "did": VASP_DID,
    "emailDomain": "example.com",
    "postalCode": "10001",
    "state": "NY",
    "website": "https://example.com",
}
ADDRESS = {
    "id": ADDRESS_ID,
    "address": WALLET_ADDRESS,
    "asset": "USDT",
    "chain": "ETH",
    "created_at": CREATED_AT,
    "status": "PENDING",
    "travel_rule_info": TRAVEL_RULE,
}


def _travel_rule():
    from alpaca.trading.requests import TravelRuleInfo, TravelRuleManualEntry

    return TravelRuleInfo(
        beneficiary_country_of_residence="US",
        beneficiary_entity_name="Alpaca Crypto LLC",
        beneficiary_family_name="Doe",
        beneficiary_geographic_address_building_number="1",
        beneficiary_geographic_address_country="US",
        beneficiary_geographic_address_post_code="10001",
        beneficiary_geographic_address_street_name="Main Street",
        beneficiary_geographic_address_town_name="New York",
        beneficiary_given_name="John",
        beneficiary_is_self_hosted=True,
        beneficiary_manual_entry=TravelRuleManualEntry(
            vasp_name="Alpaca",
            vasp_website="https://alpaca.markets",
        ),
        beneficiary_vasp_id=VASP_DID,
    )


@scenario(
    covers=["TradingClient.do_not_exercise_option"],
    since=SINCE,
    stub_responses=[EMPTY],
)
def do_not_exercise_held_contract(ctx: Context) -> Dict[str, Any]:
    # Returns None. A real instruction needs a held contract, so the response is stubbed.
    ctx.trading.do_not_exercise_option(CONTRACT_ID)
    return {}


@scenario(
    covers=[
        "TradingClient.tokenization_mint",
        "TradingClient.get_tokenization_requests",
        "TradingClient.get_tokenization_request",
        "TradingClient.get_tokenization_request_by_client_request_id",
    ],
    since=SINCE,
    stub_responses=[
        {"status": 200, "json": body}
        for body in (
            TOKENIZATION,
            [TOKENIZATION],
            TOKENIZATION,
            TOKENIZATION,
        )
    ],
)
def tokenization_mint_and_lookup(ctx: Context) -> Dict[str, Any]:
    from alpaca.trading.enums import (
        TokenizationIssuer,
        TokenizationNetwork,
        TokenizationRequestStatus,
        TokenizationRequestType,
        TokenizationTransferStatus,
    )
    from alpaca.trading.models import TokenizationMintResponse, TokenizationRequest
    from alpaca.trading.requests import (
        GetTokenizationRequestsRequest,
        TokenizationMintRequest,
    )

    minted = ctx.trading.tokenization_mint(
        TokenizationMintRequest(
            issuer=TokenizationIssuer.XSTOCKS,
            network=TokenizationNetwork.SOLANA,
            qty="10",
            underlying_symbol="AAPL",
            wallet_address=WALLET_ADDRESS,
        )
    )
    listed = ctx.trading.get_tokenization_requests(
        GetTokenizationRequestsRequest(
            type=TokenizationRequestType.MINT,
            status=TokenizationRequestStatus.PENDING,
            underlying_symbol="AAPL",
            issuer=TokenizationIssuer.XSTOCKS,
            network=TokenizationNetwork.SOLANA,
            after=datetime(2026, 1, 1, tzinfo=timezone.utc),
            before=datetime(2026, 2, 1, tzinfo=timezone.utc),
        )
    )
    fetched = ctx.trading.get_tokenization_request(TOKENIZATION_ID)
    by_client = ctx.trading.get_tokenization_request_by_client_request_id(
        CLIENT_REQUEST_ID
    )

    assert isinstance(minted, TokenizationMintResponse)
    assert minted.tokenization_request_id == TOKENIZATION_ID
    assert minted.qty == "10"
    assert isinstance(listed, list) and len(listed) == 1
    request = listed[0]
    assert isinstance(request, TokenizationRequest)
    assert request.status == TokenizationRequestStatus.PENDING
    assert request.type == TokenizationRequestType.MINT
    assert request.transfer_status == TokenizationTransferStatus.PENDING
    assert request.client_request_id == CLIENT_REQUEST_ID
    assert isinstance(fetched, TokenizationRequest)
    assert isinstance(by_client, TokenizationRequest)
    assert by_client.client_request_id == CLIENT_REQUEST_ID
    return {
        "minted": minted,
        "listed": listed,
        "fetched": fetched,
        "by_client": by_client,
    }


@scenario(
    covers=[
        "TradingClient.list_crypto_funding_wallets",
        "TradingClient.get_wallet_fee_estimate",
        "TradingClient.list_crypto_funding_transfers",
        "TradingClient.get_crypto_funding_transfer",
    ],
    since=SINCE,
    stub_responses=[
        {"status": 200, "json": WALLET},
        {"status": 200, "json": [WALLET]},
        {"status": 200, "json": FEE},
        {"status": 200, "json": [TRANSFER]},
        {"status": 200, "json": TRANSFER},
    ],
)
def crypto_funding_wallets_transfers_and_fees(ctx: Context) -> Dict[str, Any]:
    from alpaca.trading.enums import (
        CryptoChain,
        CryptoTransferStatus,
        TransferDirection,
        V2WalletsNetworkParameter,
    )
    from alpaca.trading.models import (
        CryptoTransfer,
        CryptoWallet,
        WalletFeeEstimateResponse,
    )
    from alpaca.trading.requests import (
        GetCryptoWalletsRequest,
        GetWalletFeeEstimateRequest,
    )

    wallet = ctx.trading.list_crypto_funding_wallets(
        GetCryptoWalletsRequest(
            asset="USDC",
            chain=CryptoChain.ETH,
            network=V2WalletsNetworkParameter.ETHEREUM,
        )
    )
    wallets = ctx.trading.list_crypto_funding_wallets()
    estimate = ctx.trading.get_wallet_fee_estimate(
        GetWalletFeeEstimateRequest(
            asset="USDC",
            from_address="0x2222222222222222222222222222222222222222",
            to_address=WALLET_ADDRESS,
            amount="10",
        )
    )
    transfers = ctx.trading.list_crypto_funding_transfers()
    transfer = ctx.trading.get_crypto_funding_transfer(TRANSFER_ID)

    assert isinstance(wallet, CryptoWallet)
    assert wallet.address is not None
    assert wallet.chain == "ETH" and wallet.address.startswith("0x")
    assert isinstance(wallets, list) and isinstance(wallets[0], CryptoWallet)
    assert isinstance(estimate, WalletFeeEstimateResponse)
    assert estimate.fee == "0.0505" and estimate.network_fee == "0.0825"
    assert isinstance(transfers, list) and isinstance(transfers[0], CryptoTransfer)
    assert transfers[0].direction == TransferDirection.OUTGOING
    assert transfers[0].status == CryptoTransferStatus.PROCESSING
    assert isinstance(transfer, CryptoTransfer)
    assert str(transfer.id) == TRANSFER_ID
    return {
        "wallet": wallet,
        "wallets": wallets,
        "estimate": estimate,
        "transfers": transfers,
        "transfer": transfer,
    }


@scenario(
    covers=["TradingClient.search_vasps"],
    since=SINCE,
    stub_responses=[
        {"status": 200, "json": {"page": 0, "pages": 1, "total": 1, "vasps": [VASP]}}
    ],
)
def search_travel_rule_vasps(ctx: Context) -> Dict[str, Any]:
    from alpaca.trading.models import SearchVASPsResponse
    from alpaca.trading.requests import SearchVASPsRequest

    found = ctx.trading.search_vasps(
        SearchVASPsRequest(
            q="example",
            emailDomain="example.com",
            chainalysisName="Example Exchange",
            fields="id,name",
            page=0,
            per_page=10,
            order="name",
            includeSubsidiaryVASPs=False,
        )
    )

    assert isinstance(found, SearchVASPsResponse)
    assert found.page == 0 and found.pages == 1 and found.total == 1
    assert found.vasps[0].name == "Example Exchange"
    assert found.vasps[0].email_domain == "example.com"
    return {"vasps": found}


@scenario(
    covers=[
        "TradingClient.list_whitelisted_addresses",
        "TradingClient.create_whitelisted_address",
        "TradingClient.delete_whitelisted_address",
        "TradingClient.update_whitelisted_address_travel_rule_info",
    ],
    since=SINCE,
    stub_responses=[
        {"status": 200, "json": [ADDRESS]},
        {"status": 200, "json": ADDRESS},
        EMPTY,
        EMPTY,
    ],
)
def whitelisted_address_lifecycle(ctx: Context) -> Dict[str, Any]:
    from alpaca.trading.enums import CryptoChain, WhitelistedAddressStatus
    from alpaca.trading.models import WhitelistedAddress
    from alpaca.trading.requests import (
        CreateWhitelistedAddressRequest,
        UpdateWhitelistedAddressTravelRuleInfoRequest,
    )

    travel_rule = _travel_rule()
    listed = ctx.trading.list_whitelisted_addresses()
    created = ctx.trading.create_whitelisted_address(
        CreateWhitelistedAddressRequest(
            address=WALLET_ADDRESS,
            asset="USDT",
            chain=CryptoChain.ETH,
            travel_rule_info=travel_rule,
        )
    )
    ctx.trading.delete_whitelisted_address(ADDRESS_ID)
    ctx.trading.update_whitelisted_address_travel_rule_info(
        ADDRESS_ID,
        UpdateWhitelistedAddressTravelRuleInfoRequest(travel_rule_info=travel_rule),
    )

    assert isinstance(listed, list) and isinstance(listed[0], WhitelistedAddress)
    assert listed[0].status == WhitelistedAddressStatus.PENDING
    assert listed[0].travel_rule_info is not None
    assert listed[0].travel_rule_info.beneficiary_entity_name == "Alpaca Crypto LLC"
    assert isinstance(created, WhitelistedAddress)
    assert created.id == ADDRESS_ID
    return {"listed": listed, "created": created}
