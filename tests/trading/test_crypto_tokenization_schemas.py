from datetime import datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from alpaca.trading.enums import (
    CreateCryptoTransferRequestChain,
    CryptoTransferStatus,
    TokenizationIssuer,
    TokenizationNetwork,
    TokenizationRequestStatus,
    TokenizationRequestType,
    TransferDirection,
    WhitelistedAddressStatus,
)
from alpaca.trading.models import (
    CryptoTransfer,
    CryptoWallet,
    TokenizationMintResponse,
    TokenizationRequest,
    WalletFeeEstimate,
    WhitelistedAddress,
)
from alpaca.trading.requests import (
    CreateCryptoTransferRequest,
    GetWalletFeeEstimateRequest,
    TokenizationMintRequest,
)


def test_crypto_transfer_enums_match_api_values():
    assert [member.value for member in CreateCryptoTransferRequestChain] == [
        "SOL",
        "ETH",
        "BTC",
        "XRP",
        "ARB",
    ]
    assert [member.value for member in TransferDirection] == [
        "INCOMING",
        "OUTGOING",
    ]
    assert [member.value for member in CryptoTransferStatus] == [
        "PROCESSING",
        "FAILED",
        "COMPLETE",
    ]
    assert [member.value for member in WhitelistedAddressStatus] == [
        "APPROVED",
        "PENDING",
    ]


def test_tokenization_enums_match_api_values():
    assert [member.value for member in TokenizationIssuer] == ["xstocks", "st0x"]
    assert [member.value for member in TokenizationNetwork] == [
        "solana",
        "arbitrum",
        "ethereum",
        "binance",
        "base",
        "ton",
        "tron",
        "mantle",
    ]
    assert [member.value for member in TokenizationRequestType] == [
        "mint",
        "redeem",
    ]
    assert [member.value for member in TokenizationRequestStatus] == [
        "pending",
        "rejected",
        "completed",
    ]


def test_create_crypto_transfer_request_validates_chain_and_serializes_fields():
    request = CreateCryptoTransferRequest(
        amount="1.25",
        address="wallet-address",
        asset="ETH",
        chain="ETH",
    )

    assert request.chain == CreateCryptoTransferRequestChain.ETH
    assert request.to_request_fields() == {
        "amount": "1.25",
        "address": "wallet-address",
        "asset": "ETH",
        "chain": "ETH",
    }

    with pytest.raises(ValidationError):
        CreateCryptoTransferRequest(
            amount="1.25",
            address="wallet-address",
            asset="ETH",
            chain="DOGE",
        )


def test_crypto_transfer_models_parse_api_payloads():
    transfer = CryptoTransfer(
        id="4bb62d0f-9ce7-4f51-8e1f-b9b285a1f047",
        tx_hash="0xabc",
        direction="OUTGOING",
        status="COMPLETE",
        amount="1.25",
        asset="ETH",
        created_at="2026-07-14T08:30:00Z",
    )
    wallet = CryptoWallet(chain="ETH", address="0x123")
    whitelisted = WhitelistedAddress(
        id="address-id",
        chain="ETH",
        asset="ETH",
        address="0x123",
        status="PENDING",
    )
    fee = WalletFeeEstimate(fee="0.10", network_fee="0.08")

    assert transfer.id == UUID("4bb62d0f-9ce7-4f51-8e1f-b9b285a1f047")
    assert transfer.direction == TransferDirection.OUTGOING
    assert transfer.status == CryptoTransferStatus.COMPLETE
    assert transfer.created_at == datetime.fromisoformat("2026-07-14T08:30:00+00:00")
    assert wallet.created_at is None
    assert whitelisted.status == WhitelistedAddressStatus.PENDING
    assert fee.model_dump() == {"fee": "0.10", "network_fee": "0.08"}


def test_wallet_fee_estimate_request_omits_unset_fields():
    request = GetWalletFeeEstimateRequest(asset="USDC", amount="100")

    assert request.to_request_fields() == {"asset": "USDC", "amount": "100"}


def test_tokenization_request_and_response_parse_api_payloads():
    mint_request = TokenizationMintRequest(
        underlying_symbol="AAPL",
        qty="2.5",
        issuer="xstocks",
        network="solana",
        wallet_address="wallet-address",
    )
    response = TokenizationMintResponse(
        tokenization_request_id="request-id",
        status="pending",
        underlying_symbol="AAPL",
        token_symbol="AAPLX",
        qty="2.5",
        created_at="2026-07-14T08:30:00Z",
        issuer="xstocks",
        network="solana",
    )
    record = TokenizationRequest(
        tokenization_request_id="request-id",
        created_at="2026-07-14T08:30:00Z",
        type="mint",
        status="completed",
        underlying_symbol="AAPL",
        token_symbol="AAPLX",
        qty="2.5",
        issuer="xstocks",
        network="solana",
        wallet_address="wallet-address",
        tx_hash="0xabc",
    )

    assert mint_request.issuer == TokenizationIssuer.XSTOCKS
    assert mint_request.network == TokenizationNetwork.SOLANA
    assert response.status == TokenizationRequestStatus.PENDING
    assert record.type == TokenizationRequestType.MINT
    assert record.status == TokenizationRequestStatus.COMPLETED
    assert record.issuer_request_id is None
    assert record.tx_hash == "0xabc"
