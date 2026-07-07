"""
Tests for the Trading API's wallet routes:
  GET /v2/wallets/fees/estimate
"""

from alpaca.common.enums import BaseURL
from alpaca.trading.client import TradingClient
from alpaca.trading.models import WalletFeeEstimate
from alpaca.trading.requests import GetWalletFeeEstimateRequest


def test_get_wallet_fee_estimate_no_params(reqmock, trading_client: TradingClient):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/wallets/fees/estimate",
        text='{"fee": "0.0021", "network_fee": "0.0019"}',
    )

    result = trading_client.get_wallet_fee_estimate()

    assert reqmock.called_once
    assert isinstance(result, WalletFeeEstimate)
    assert result.fee == "0.0021"
    assert result.network_fee == "0.0019"


def test_get_wallet_fee_estimate_fee_fields_are_optional(
    reqmock, trading_client: TradingClient
):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/wallets/fees/estimate",
        text='{"network_fee": "0.0019"}',
    )

    result = trading_client.get_wallet_fee_estimate()

    assert reqmock.called_once
    assert isinstance(result, WalletFeeEstimate)
    assert result.fee is None
    assert result.network_fee == "0.0019"


def test_get_wallet_fee_estimate_with_params(reqmock, trading_client: TradingClient):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/wallets/fees/estimate"
        f"?asset=USDC&from_address=0xABC&to_address=0xDEF&amount=100",
        text='{"fee": "0.0035"}',
    )

    result = trading_client.get_wallet_fee_estimate(
        GetWalletFeeEstimateRequest(
            asset="USDC",
            from_address="0xABC",
            to_address="0xDEF",
            amount="100",
        )
    )

    assert reqmock.called_once
    assert isinstance(result, WalletFeeEstimate)
    assert result.fee == "0.0035"


def test_get_wallet_fee_estimate_partial_params(reqmock, trading_client: TradingClient):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/wallets/fees/estimate?asset=ETH",
        text='{"fee": "0.0018"}',
    )

    result = trading_client.get_wallet_fee_estimate(
        GetWalletFeeEstimateRequest(asset="ETH")
    )

    assert reqmock.called_once
    assert isinstance(result, WalletFeeEstimate)
    assert result.fee == "0.0018"


def test_get_wallet_fee_estimate_raw(reqmock, trading_client_raw: TradingClient):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/wallets/fees/estimate",
        text='{"fee": "0.0021"}',
    )

    result = trading_client_raw.get_wallet_fee_estimate()

    assert isinstance(result, dict)
    assert result["fee"] == "0.0021"
