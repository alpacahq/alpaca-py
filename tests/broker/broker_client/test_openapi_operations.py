"""Request and response coverage for the Broker operations added from OpenAPI."""

import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

from alpaca.broker._generated.models import CIPInfo as GeneratedCIPInfo
from alpaca.broker.client import BrokerClient
from alpaca.broker.models import (
    ClockResp,
    CryptoTransfer,
    CryptoWallet,
    DemoFundingTransfer,
    PublicCalendarResp,
    SettlementAccount,
    SettlementTransfer,
    TokenizationMintCallback,
    TransmitterInfo,
    WhitelistedAddress,
)
from alpaca.broker.requests import (
    AcatsContraAccountDetails,
    AcatsInitiateTransferDetails,
    AcatsInitiateTransferRequest,
    BatchCreateFundingWalletRequest,
    CreateAccountAgreementRequest,
    CreateCryptoTransferRequest,
    CreateFundingWalletRecipientBankRequest,
    CreateFundingWalletWithdrawalRequest,
    CreateIFTransferRequest,
    CreateJITSettlementRequest,
    CreateSettlementRequest,
    CreateWhitelistedAddressRequest,
    GetAccountActivitiesByTypeRequest,
    GetAssetEntryRequirementsRequest,
    GetCryptoTransferEstimateRequest,
    GetEodAggregatePositionsRequest,
    GetEodCashInterestReportRequest,
    GetEodPositionsRequest,
    GetEventsRequest,
    GetFpslAccountLoansRequest,
    GetInstantFundingAccountLimitsRequest,
    GetInstantFundingReportsRequest,
    GetInstantFundingSettlementsRequest,
    GetInstantFundingTransfersRequest,
    GetJitLedgerBalancesRequest,
    GetJitReportRequest,
    GetJitSettlementsRequest,
    GetLogoRequest,
    GetOauthClientRequest,
    GetOnfidoSdkTokenRequest,
    GetOptionContractsRequest,
    GetTokenizationRequestByClientRequestIdRequest,
    GetTokenizationRequestByIssuerRequestIdRequest,
    GetUsCorporateBondsRequest,
    GetUsTreasuriesRequest,
    GetV1TradingAccountsAccountIdOrdersEstimationRequest,
    GetV2CalendarRequest,
    GetV2ClockRequest,
    ListAcatsTransfersForAccountRequest,
    ListAcatsTransfersRequest,
    ListCryptoWalletsRequest,
    ListFpslLoansRequest,
    ListFundingDetailsRequest,
    ListIpoOfferingsRequest,
    ListOptionsApprovalsRequest,
    ListTokenizationRequestsRequest,
    OAuthTokenRequest,
    OptionsApprovalRequest,
    PatchV1AccountsAccountIdOnfidoSdkRequest,
    SearchVaspsRequest,
    TokenizationMintRequest,
    TokenizationRedeemRequest,
    TravelRuleInfo,
    UpdateWhitelistedAddressTravelRuleInfoRequest,
)
from alpaca.common.enums import BaseURL
from alpaca.common.exceptions import APIError

_BASE = BaseURL.BROKER_SANDBOX.value
_ACCOUNT = "00000000-0000-4000-8000-000000000000"
_OTHER = "00000000-0000-4000-8000-000000000001"
_TRANSMITTER = TransmitterInfo()


def _wire_body(value):
    if value is None:
        return None
    if hasattr(value, "to_request_fields"):
        return value.to_request_fields()
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json", exclude_none=True, by_alias=True)
    return value


def _wire_query(model):
    if model is None:
        return {}
    rendered = {}
    for key, value in model.to_request_fields().items():
        if isinstance(value, bool):
            rendered[key] = str(value).lower()
        elif isinstance(value, list):
            rendered[key] = ",".join(str(item) for item in value)
        else:
            rendered[key] = value if isinstance(value, str) else str(value)
    return rendered


def _client() -> BrokerClient:
    return BrokerClient("key-id", "secret-key", sandbox=True, raw_data=True)


# name, http, path, args, kwargs, kind
# kind is "json", "empty", "sse", "bytes", or "file".
_CASES = [
    (
        "create_agreement",
        "post",
        "/v1/agreements",
        (),
        {
            "request": CreateAccountAgreementRequest(
                account_id="d7e8f9a0-b1c2-3d4e-5f67-890123456789",
                agreement="options_agreement",
                ip_address="10.0.0.50",
                party_id="550e8400-e29b-41d4-a716-446655440000",
                signed_at="2024-08-18T14:05:00Z",
            )
        },
        "json",
    ),
    (
        "get_account_activities_by_type",
        "get",
        "/v1/accounts/activities/FILL",
        ("FILL",),
        {
            "filter": GetAccountActivitiesByTypeRequest(
                account_id=_ACCOUNT,
                direction="desc",
                page_size=100,
            )
        },
        "json",
    ),
    (
        "get_account_activity_event",
        "get",
        f"/v2beta1/accounts/{_ACCOUNT}/events/activities/01ARZ3NDEKTSV4RRFFQ69G5FAV",
        (_ACCOUNT, "01ARZ3NDEKTSV4RRFFQ69G5FAV"),
        {},
        "sse",
    ),
    (
        "get_cip_data_for_account_by_id",
        "get",
        f"/v1/accounts/{_ACCOUNT}/cip",
        (_ACCOUNT,),
        {},
        "json",
    ),
    (
        "upload_cip_data_for_account_by_id",
        "post",
        f"/v1/accounts/{_ACCOUNT}/cip",
        (_ACCOUNT,),
        {"request": GeneratedCIPInfo(provider_name=["alpaca"], account_id=_ACCOUNT)},
        "json",
    ),
    (
        "get_onfido_sdk_token",
        "get",
        f"/v1/accounts/{_ACCOUNT}/onfido/sdk/tokens",
        (_ACCOUNT,),
        {"filter": GetOnfidoSdkTokenRequest(referrer="https://example.com")},
        "json",
    ),
    (
        "update_onfido_sdk_outcome",
        "patch",
        f"/v1/accounts/{_ACCOUNT}/onfido/sdk",
        (_ACCOUNT,),
        {
            "request": PatchV1AccountsAccountIdOnfidoSdkRequest(
                outcome="USER_EXITED",
                reason="User denied consent",
                token="header.payload.signature",
            )
        },
        "json",
    ),
    (
        "get_account_trading_limits",
        "get",
        f"/v1/trading/accounts/{_ACCOUNT}/limits",
        (_ACCOUNT,),
        {},
        "json",
    ),
    (
        "list_ira_excess_contributions",
        "get",
        "/v1/accounts/ira_excess_contributions",
        (),
        {},
        "json",
    ),
    ("get_country_info", "get", "/v1/country-info", (), {}, "json"),
    (
        "list_options_approvals",
        "get",
        "/v1/accounts/options/approvals",
        (),
        {"filter": ListOptionsApprovalsRequest(account_id=_ACCOUNT, page_size=1000)},
        "json",
    ),
    (
        "request_options_approval",
        "post",
        f"/v1/accounts/{_ACCOUNT}/options/approval",
        (_ACCOUNT,),
        {"request": OptionsApprovalRequest(level=3)},
        "json",
    ),
    (
        "download_w8ben_document_for_account_by_id",
        "get",
        f"/v1/accounts/{_ACCOUNT}/documents/w8ben/{_OTHER}/download",
        (_ACCOUNT, _OTHER),
        {},
        "file",
    ),
    (
        "batch_create_funding_wallets",
        "post",
        "/v1beta/accounts/funding_wallet",
        (),
        {"request": BatchCreateFundingWalletRequest(account_ids=[_ACCOUNT])},
        "json",
    ),
    (
        "create_funding_wallet",
        "post",
        f"/v1beta/accounts/{_ACCOUNT}/funding_wallet",
        (_ACCOUNT,),
        {},
        "empty",
    ),
    (
        "create_funding_wallet_recipient_bank",
        "post",
        f"/v1beta/accounts/{_ACCOUNT}/funding_wallet/recipient_bank",
        (_ACCOUNT,),
        {
            "request": CreateFundingWalletRecipientBankRequest(
                account_number="123",
                bank_country="US",
                bank_name="Bank",
                city="New York",
                currency="USD",
                street_address="1 Main",
            )
        },
        "json",
    ),
    (
        "create_funding_wallet_withdrawal",
        "post",
        f"/v1beta/accounts/{_ACCOUNT}/funding_wallet/withdrawal",
        (_ACCOUNT,),
        {
            "request": CreateFundingWalletWithdrawalRequest(
                usd_amount="1.0",
                payment_type="swift_wire",
            )
        },
        "json",
    ),
    (
        "delete_funding_wallet_recipient_bank",
        "delete",
        f"/v1beta/accounts/{_ACCOUNT}/funding_wallet/recipient_bank",
        (_ACCOUNT,),
        {},
        "json",
    ),
    (
        "create_demo_funding_deposit",
        "post",
        "/v1beta/demo/banking/funding",
        (),
        {"request": DemoFundingTransfer(amount="1.0", currency="USD")},
        "json",
    ),
    (
        "get_funding_wallet",
        "get",
        f"/v1beta/accounts/{_ACCOUNT}/funding_wallet",
        (_ACCOUNT,),
        {},
        "json",
    ),
    (
        "get_funding_wallet_recipient_bank",
        "get",
        f"/v1beta/accounts/{_ACCOUNT}/funding_wallet/recipient_bank",
        (_ACCOUNT,),
        {},
        "json",
    ),
    (
        "get_funding_wallet_transfer",
        "get",
        f"/v1beta/accounts/{_ACCOUNT}/funding_wallet/transfers/{_OTHER}",
        (_ACCOUNT, _OTHER),
        {},
        "json",
    ),
    (
        "get_funding_wallet_transfers",
        "get",
        f"/v1beta/accounts/{_ACCOUNT}/funding_wallet/transfers",
        (_ACCOUNT,),
        {},
        "json",
    ),
    (
        "list_funding_details",
        "get",
        f"/v1beta/accounts/{_ACCOUNT}/funding_wallet/funding_details",
        (_ACCOUNT,),
        {
            "filter": ListFundingDetailsRequest(
                payment_type="swift_wire", currency="USD"
            )
        },
        "json",
    ),
    (
        "cancel_instant_funding_transfer",
        "delete",
        f"/v1/instant_funding/{_ACCOUNT}",
        (_ACCOUNT,),
        {},
        "json",
    ),
    (
        "get_instant_funding_account_limits",
        "get",
        "/v1/instant_funding/limits/accounts",
        (),
        {"filter": GetInstantFundingAccountLimitsRequest(account_numbers=["sample"])},
        "json",
    ),
    ("get_instant_funding_limits", "get", "/v1/instant_funding/limits", (), {}, "json"),
    (
        "get_instant_funding_transfers",
        "get",
        "/v1/instant_funding",
        (),
        {"filter": GetInstantFundingTransfersRequest(status="PENDING", limit=1)},
        "json",
    ),
    (
        "get_instant_funding_reports",
        "get",
        "/v1/instant_funding/reports",
        (),
        {
            "filter": GetInstantFundingReportsRequest(
                report_type="summary", system_date="2026-01-01"
            )
        },
        "json",
    ),
    (
        "get_instant_funding_settlements",
        "get",
        "/v1/instant_funding/settlements",
        (),
        {"filter": GetInstantFundingSettlementsRequest(statuses="PENDING")},
        "json",
    ),
    (
        "get_instant_funding_settlement",
        "get",
        f"/v1/instant_funding/settlements/{_ACCOUNT}",
        (_ACCOUNT,),
        {},
        "json",
    ),
    (
        "get_instant_funding_transfer",
        "get",
        f"/v1/instant_funding/{_ACCOUNT}",
        (_ACCOUNT,),
        {},
        "json",
    ),
    (
        "create_instant_funding_transfer",
        "post",
        "/v1/instant_funding",
        (),
        {
            "request": CreateIFTransferRequest(
                account_no="123",
                amount="1.0",
                source_account_no="456",
            )
        },
        "json",
    ),
    (
        "create_instant_funding_settlement",
        "post",
        "/v1/instant_funding/settlements",
        (),
        {
            "request": CreateSettlementRequest(
                transfers=[
                    SettlementTransfer(
                        instant_transfer_id=_ACCOUNT,
                        transmitter_info=_TRANSMITTER,
                    )
                ]
            )
        },
        "json",
    ),
    (
        "get_jit_settlements",
        "get",
        "/v1/jit/settlements",
        (),
        {"filter": GetJitSettlementsRequest(statuses="PENDING")},
        "json",
    ),
    (
        "get_jit_settlement",
        "get",
        f"/v1/jit/settlements/{_ACCOUNT}",
        (_ACCOUNT,),
        {},
        "json",
    ),
    (
        "create_jit_settlement",
        "post",
        "/v1/jit/settlements",
        (),
        {
            "request": CreateJITSettlementRequest(
                accounts=[
                    SettlementAccount(
                        account_number="123",
                        amount="1.0",
                        transmitter_info=_TRANSMITTER,
                    )
                ],
                asset_class="crypto",
                currency="USD",
            )
        },
        "json",
    ),
    (
        "get_jit_ledger_balances",
        "get",
        f"/v1/transfers/jit/{_ACCOUNT}/balances",
        (_ACCOUNT,),
        {
            "filter": GetJitLedgerBalancesRequest(
                start_date="2026-01-01",
                end_date="2026-01-02",
            )
        },
        "json",
    ),
    ("get_jit_ledgers", "get", "/v1/transfers/jit/ledgers", (), {}, "json"),
    ("get_jit_limits", "get", "/v1/transfers/jit/limits", (), {}, "json"),
    (
        "get_jit_report",
        "get",
        "/v1/transfers/jit/reports",
        (),
        {
            "filter": GetJitReportRequest(
                report_type="detail",
                system_date="2026-01-01",
                asset_class="us_equity",
            )
        },
        "json",
    ),
    (
        "create_crypto_transfer_for_account",
        "post",
        f"/v1/accounts/{_ACCOUNT}/wallets/transfers",
        (_ACCOUNT,),
        {
            "request": CreateCryptoTransferRequest(
                address="addr",
                amount="1",
                asset="SOL",
            )
        },
        "json",
    ),
    (
        "create_whitelisted_address",
        "post",
        f"/v1/accounts/{_ACCOUNT}/wallets/whitelists",
        (_ACCOUNT,),
        {"request": CreateWhitelistedAddressRequest(address="addr", asset="SOL")},
        "json",
    ),
    (
        "delete_whitelisted_address",
        "delete",
        f"/v1/accounts/{_ACCOUNT}/wallets/whitelists/{_OTHER}",
        (_ACCOUNT, _OTHER),
        {},
        "json",
    ),
    (
        "get_crypto_transfer",
        "get",
        f"/v1/accounts/{_ACCOUNT}/wallets/transfers/{_OTHER}",
        (_ACCOUNT, _OTHER),
        {},
        "json",
    ),
    (
        "get_crypto_transfer_estimate",
        "get",
        "/v1/wallets/fees/estimate",
        (),
        {"filter": GetCryptoTransferEstimateRequest(asset="SOL", amount="1")},
        "json",
    ),
    (
        "list_crypto_transfers",
        "get",
        f"/v1/accounts/{_ACCOUNT}/wallets/transfers",
        (_ACCOUNT,),
        {},
        "json",
    ),
    (
        "list_crypto_wallets",
        "get",
        f"/v1/accounts/{_ACCOUNT}/wallets",
        (_ACCOUNT,),
        {"filter": ListCryptoWalletsRequest(asset="SOL", chain="SOL")},
        "json",
    ),
    (
        "list_whitelisted_addresses",
        "get",
        f"/v1/accounts/{_ACCOUNT}/wallets/whitelists",
        (_ACCOUNT,),
        {},
        "json",
    ),
    (
        "search_vasps",
        "get",
        "/v1/wallets/travel-rule/vasps",
        (),
        {"filter": SearchVaspsRequest(page=0, includeSubsidiaryVASPs=False)},
        "json",
    ),
    (
        "update_whitelisted_address_travel_rule",
        "patch",
        f"/v1/accounts/{_ACCOUNT}/wallets/whitelists/{_OTHER}/travel-rule-info",
        (_ACCOUNT, _OTHER),
        {
            "request": UpdateWhitelistedAddressTravelRuleInfoRequest(
                travel_rule_info=TravelRuleInfo(beneficiary_given_name="John")
            )
        },
        "json",
    ),
    (
        "estimate_order_for_account",
        "post",
        f"/v1/trading/accounts/{_ACCOUNT}/orders/estimation",
        (_ACCOUNT,),
        {
            "request": GetV1TradingAccountsAccountIdOrdersEstimationRequest(
                symbol="AAPL",
                side="buy",
                type="market",
                time_in_force="day",
                notional="40",
            )
        },
        "json",
    ),
    (
        "do_not_exercise_options_position_for_account",
        "post",
        f"/v1/trading/accounts/{_ACCOUNT}/positions/AAPL250620C00200000/do-not-exercise",
        (_ACCOUNT, "AAPL250620C00200000"),
        {},
        "object",
    ),
    (
        "get_v2_calendar",
        "get",
        "/v2/calendar/NYSE",
        ("NYSE",),
        {
            "filter": GetV2CalendarRequest(
                start="2025-01-01", end="2025-01-02", timezone="UTC"
            )
        },
        "json",
    ),
    (
        "get_v2_clock",
        "get",
        "/v2/clock",
        (),
        {"filter": GetV2ClockRequest(markets="NYSE,LSE", time="2026-01-01T00:00:00Z")},
        "json",
    ),
    (
        "get_asset_entry_requirements",
        "get",
        "/v1/assets/entry-requirements",
        (),
        {"filter": GetAssetEntryRequirementsRequest(symbols="AAPL,SPY")},
        "json",
    ),
    (
        "get_option_contract",
        "get",
        "/v1/options/contracts/AAPL250620C00200000",
        ("AAPL250620C00200000",),
        {},
        "json",
    ),
    (
        "get_option_contracts",
        "get",
        "/v1/options/contracts",
        (),
        {
            "filter": GetOptionContractsRequest(
                underlying_symbols="AAPL",
                show_deliverables=True,
                type="call",
                limit=100,
            )
        },
        "json",
    ),
    (
        "get_logo",
        "get",
        "/v1beta1/logos/AAPL",
        ("AAPL",),
        {"logo_filter": GetLogoRequest(placeholder="true")},
        "bytes",
    ),
    (
        "get_us_corporate_bonds",
        "get",
        "/v1/assets/fixed_income/us_corporates",
        (),
        {
            "filter": GetUsCorporateBondsRequest(
                bond_status="outstanding", tickers="BAC"
            )
        },
        "json",
    ),
    (
        "get_us_treasuries",
        "get",
        "/v1/assets/fixed_income/us_treasuries",
        (),
        {"filter": GetUsTreasuriesRequest(subtype="bond", bond_status="outstanding")},
        "json",
    ),
    (
        "authorize_oauth_token",
        "post",
        "/v1/oauth/authorize",
        (),
        {
            "request": OAuthTokenRequest(
                account_id=_ACCOUNT,
                client_id="client",
                client_secret="secret",
                redirect_uri="http://localhost",
                scope="general",
            )
        },
        "json",
    ),
    (
        "get_oauth_client",
        "get",
        "/v1/oauth/clients/client",
        ("client",),
        {"filter": GetOauthClientRequest(response_type="token", scope="general")},
        "json",
    ),
    (
        "issue_oauth_token",
        "post",
        "/v1/oauth/token",
        (),
        {
            "request": OAuthTokenRequest(
                account_id=_ACCOUNT,
                client_id="client",
                client_secret="secret",
                redirect_uri="http://localhost",
                scope="general",
            )
        },
        "json",
    ),
    (
        "get_acats_transfer",
        "get",
        f"/v1beta1/acats/{_ACCOUNT}/{_OTHER}",
        (_ACCOUNT, _OTHER),
        {},
        "json",
    ),
    (
        "list_acats_assets",
        "get",
        f"/v1beta1/acats/{_ACCOUNT}/{_OTHER}/assets",
        (_ACCOUNT, _OTHER),
        {},
        "json",
    ),
    (
        "list_acats_contra_brokers",
        "get",
        "/v1beta1/acats/contrabrokers",
        (),
        {},
        "json",
    ),
    (
        "list_acats_transfers",
        "get",
        "/v1beta1/acats",
        (),
        {"filter": ListAcatsTransfersRequest(transfer_type="FUL", limit=1)},
        "json",
    ),
    (
        "list_acats_transfers_for_account",
        "get",
        f"/v1beta1/acats/{_ACCOUNT}",
        (_ACCOUNT,),
        {"filter": ListAcatsTransfersForAccountRequest(limit=1, page_token="MA==")},
        "json",
    ),
    (
        "request_acats_transfer",
        "post",
        f"/v1beta1/acats/{_ACCOUNT}",
        (_ACCOUNT,),
        {
            "request": AcatsInitiateTransferRequest(
                contra_account_details=AcatsContraAccountDetails(
                    account_number="A00000123",
                    broker_number="0158",
                    customer_name="Jane Doe",
                    customer_tax_id="123456789",
                ),
                ip_address="203.0.113.42",
                signed_at="2026-04-29T13:00:00Z",
                transfer_details=AcatsInitiateTransferDetails(type="FULL"),
            )
        },
        "json",
    ),
    (
        "get_ipo_offering",
        "get",
        "/v1/ipos/EXMP",
        ("EXMP",),
        {},
        "json",
    ),
    (
        "list_ipo_offerings",
        "get",
        "/v1/ipos",
        (),
        {
            "filter": ListIpoOfferingsRequest(
                availability="available", ticker="EXMP", limit=50
            )
        },
        "json",
    ),
    (
        "get_tokenization_request_by_client_request_id",
        "get",
        f"/v1/accounts/{_ACCOUNT}/tokenization/requests:by_client_request_id",
        (_ACCOUNT,),
        {
            "filter": GetTokenizationRequestByClientRequestIdRequest(
                client_request_id="ap-request-2025-11-04-001"
            )
        },
        "json",
    ),
    (
        "get_tokenization_request_by_id",
        "get",
        f"/v1/accounts/{_ACCOUNT}/tokenization/requests/{_OTHER}",
        (_ACCOUNT, _OTHER),
        {},
        "json",
    ),
    (
        "get_tokenization_request_by_issuer_request_id",
        "get",
        f"/v1/accounts/{_ACCOUNT}/tokenization/requests:by_issuer_request_id",
        (_ACCOUNT,),
        {
            "filter": GetTokenizationRequestByIssuerRequestIdRequest(
                issuer_request_id="ABCDEF123"
            )
        },
        "json",
    ),
    (
        "list_tokenization_requests",
        "get",
        f"/v1/accounts/{_ACCOUNT}/tokenization/requests",
        (_ACCOUNT,),
        {"filter": ListTokenizationRequestsRequest(type="mint", status="pending")},
        "json",
    ),
    (
        "submit_tokenization_mint_callback",
        "post",
        f"/v1/accounts/{_ACCOUNT}/tokenization/callback/mint",
        (_ACCOUNT,),
        {
            "request": TokenizationMintCallback(
                tokenization_request_id=_ACCOUNT,
                tx_hash="hash",
            )
        },
        "json",
    ),
    (
        "create_tokenization_mint",
        "post",
        f"/v1/accounts/{_ACCOUNT}/tokenization/mint",
        (_ACCOUNT,),
        {
            "request": TokenizationMintRequest(
                issuer="xstocks",
                network="solana",
                qty="1",
                underlying_symbol="AAPL",
                wallet_address="wallet",
            )
        },
        "json",
    ),
    (
        "submit_tokenization_redeem_callback",
        "post",
        f"/v1/accounts/{_ACCOUNT}/tokenization/callback/redeem",
        (_ACCOUNT,),
        {
            "request": TokenizationRedeemRequest(
                issuer_request_id="ABCDEF123",
                network="solana",
                qty="1",
                token_symbol="AAPLx",
                tx_hash="hash",
                underlying_symbol="AAPL",
                wallet_address="wallet",
            )
        },
        "json",
    ),
    (
        "get_fpsl_account_loans",
        "get",
        f"/v1/fpsl/analytics/{_ACCOUNT}/loans",
        (_ACCOUNT,),
        {"filter": GetFpslAccountLoansRequest(start="2026-01-01", end="2026-01-02")},
        "json",
    ),
    ("list_apr_tiers", "get", "/v1/cash_interest/apr_tiers", (), {}, "json"),
    (
        "list_fpsl_loans",
        "get",
        "/v1/fpsl/loans",
        (),
        {"filter": ListFpslLoansRequest(account_id=_ACCOUNT, limit=1000)},
        "json",
    ),
    ("list_fpsl_tiers", "get", "/v1/fpsl/tiers", (), {}, "json"),
    (
        "get_eod_cash_interest_report",
        "get",
        "/v1/reporting/eod/cash_interest",
        (),
        {
            "filter": GetEodCashInterestReportRequest(
                account_id=_ACCOUNT,
                date="2026-01-01",
                direction="desc",
            )
        },
        "json",
    ),
    (
        "get_eod_aggregate_positions",
        "get",
        "/v1/reporting/eod/aggregate_positions",
        (),
        {
            "filter": GetEodAggregatePositionsRequest(
                date="2026-01-01", firm_accounts="True"
            )
        },
        "json",
    ),
    (
        "get_eod_positions",
        "get",
        "/v1/reporting/eod/positions",
        (),
        {
            "filter": GetEodPositionsRequest(
                account_id=_ACCOUNT, asof="2026-01-01", limit=1
            )
        },
        "json",
    ),
    (
        "subscribe_to_activity_events",
        "get",
        "/v2beta1/events/activities",
        (),
        {
            "events_filter": GetEventsRequest(
                since="2026-01-01T00:00:00Z", until="2026-01-02T00:00:00Z"
            )
        },
        "sse",
    ),
    (
        "subscribe_to_admin_action_events",
        "get",
        "/v2/events/admin-actions",
        (),
        {"events_filter": GetEventsRequest(since="2026-01-01T00:00:00Z")},
        "sse",
    ),
    (
        "subscribe_to_funding_status_events",
        "get",
        "/v2/events/funding/status",
        (),
        {"events_filter": GetEventsRequest(since="2026-01-01", until="2026-01-02")},
        "sse",
    ),
    (
        "subscribe_to_ipo_events",
        "get",
        "/v2/events/ipos",
        (),
        {"events_filter": GetEventsRequest(since="2026-01-01T00:00:00Z")},
        "sse",
    ),
    (
        "subscribe_to_journal_status_events_v2",
        "get",
        "/v2/events/journals/status",
        (),
        {
            "events_filter": GetEventsRequest(
                id="journal-1", since="2026-01-01T00:00:00Z"
            )
        },
        "sse",
    ),
    (
        "subscribe_to_system_events",
        "get",
        "/v2/events/system",
        (),
        {"events_filter": GetEventsRequest(since="2026-01-01T00:00:00Z")},
        "sse",
    ),
    (
        "subscribe_to_trade_events_v2",
        "get",
        "/v2/events/trades",
        (),
        {"events_filter": GetEventsRequest(since="2026-01-01", until="2026-01-02")},
        "sse",
    ),
]


@pytest.mark.parametrize(
    ("name", "http", "path", "args", "kwargs", "kind"),
    _CASES,
    ids=[case[0] for case in _CASES],
)
def test_broker_operation_request_and_response(
    reqmock, tmp_path, name, http, path, args, kwargs, kind
):
    client = _client()
    url = _BASE + path
    payload = {"marker": name}
    if kind == "sse":
        reqmock.get(
            url,
            text="data: event-1\n\n",
            headers={"Content-Type": "text/event-stream"},
        )
    elif kind == "bytes":
        reqmock.get(url, content=b"\x89PNG")
    elif kind == "file":
        reqmock.get(url, content=b"%PDF")
        args = (*args, str(tmp_path / "download.bin"))
    else:
        getattr(reqmock, http)(url, json=payload)

    result = getattr(client, name)(*args, **kwargs)
    if kind == "sse":
        assert list(result) == ["event-1"]
    elif kind == "bytes":
        assert result == b"\x89PNG"
    elif kind == "file":
        assert result is None
        assert (tmp_path / "download.bin").read_bytes() == b"%PDF"
    else:
        assert result == payload

    sent = reqmock.request_history[0]
    parsed = urlparse(sent.url)
    assert sent.method == http.upper()
    assert parsed.path == path
    query_model = (
        kwargs.get("filter") or kwargs.get("logo_filter") or kwargs.get("events_filter")
    )
    actual_query = parse_qs(parsed.query)
    expected_query = _wire_query(query_model)
    assert actual_query == {key: [value] for key, value in expected_query.items()}
    if kind == "sse":
        assert sent.headers["Accept"] == "text/event-stream"
    if "request" in kwargs:
        assert sent.json() == _wire_body(kwargs["request"])
    elif kind == "object":
        assert sent.json() == {}
    elif kind == "empty":
        assert sent.body in (None, b"")


def test_v1_clock_and_calendar_stay_on_legacy_routes(reqmock, client: BrokerClient):
    reqmock.get(
        f"{_BASE}/v1/clock",
        json={
            "timestamp": "2026-01-01T00:00:00Z",
            "is_open": False,
            "next_open": "2026-01-02T14:30:00Z",
            "next_close": "2026-01-02T21:00:00Z",
        },
    )
    reqmock.get(f"{_BASE}/v2/clock", json={"clocks": []})

    client.get_clock()
    client.get_v2_clock()

    assert urlparse(reqmock.request_history[0].url).path == "/v1/clock"
    assert urlparse(reqmock.request_history[1].url).path == "/v2/clock"


@pytest.mark.parametrize("shape", ["array", "object"])
@pytest.mark.parametrize(
    ("method", "path", "model", "item"),
    [
        (
            "list_crypto_transfers",
            f"/v1/accounts/{_ACCOUNT}/wallets/transfers",
            CryptoTransfer,
            {"id": _OTHER, "asset": "BTC", "amount": "0.1"},
        ),
        (
            "list_crypto_wallets",
            f"/v1/accounts/{_ACCOUNT}/wallets",
            CryptoWallet,
            {"id": _OTHER, "address": "addr", "chain": "SOL"},
        ),
        (
            "list_whitelisted_addresses",
            f"/v1/accounts/{_ACCOUNT}/wallets/whitelists",
            WhitelistedAddress,
            {"id": "wl-1", "address": "addr", "asset": "BTC", "chain": "BTC"},
        ),
    ],
)
def test_crypto_lists_parse_array_or_object(
    reqmock, client: BrokerClient, shape, method, path, model, item
):
    body = [item] if shape == "array" else item
    reqmock.get(f"{_BASE}{path}", json=body)

    result = getattr(client, method)(_ACCOUNT)

    if shape == "array":
        assert isinstance(result, list)
        assert len(result) == 1
        parsed = result[0]
    else:
        parsed = result
    assert isinstance(parsed, model)
    assert str(parsed.id) == item["id"]


def test_v2_clock_and_calendar_parse_responses(reqmock, client: BrokerClient):
    reqmock.get(
        f"{_BASE}/v2/clock",
        json={
            "clocks": [
                {
                    "is_market_day": False,
                    "market": {
                        "acronym": "NYSE",
                        "name": "New York Stock Exchange",
                        "timezone": "America/New_York",
                    },
                    "next_market_close": "2026-01-02T21:00:00Z",
                    "next_market_open": "2026-01-02T14:30:00Z",
                    "phase": "closed",
                    "phase_until": "2026-01-02T14:30:00Z",
                    "timestamp": "2026-01-01T00:00:00Z",
                }
            ]
        },
    )
    reqmock.get(
        f"{_BASE}/v2/calendar/NYSE",
        json={
            "market": {
                "acronym": "NYSE",
                "name": "New York Stock Exchange",
                "timezone": "America/New_York",
            },
            "calendar": [
                {
                    "date": "2026-01-02",
                    "core_start": "2026-01-02T14:30:00Z",
                    "core_end": "2026-01-02T21:00:00Z",
                }
            ],
        },
    )

    clock = client.get_v2_clock()
    calendar = client.get_v2_calendar("NYSE")

    assert isinstance(clock, ClockResp)
    assert clock.clocks[0].market.acronym == "NYSE"
    assert isinstance(calendar, PublicCalendarResp)
    assert calendar.calendar[0].var_date.isoformat() == "2026-01-02"
    assert urlparse(reqmock.request_history[1].url).path == "/v2/calendar/NYSE"


def test_sse_refuses_redirects_and_closes_the_response(reqmock):
    reqmock.get(
        f"{_BASE}/v2/events/trades",
        status_code=302,
        headers={"Location": "https://files.example/stream"},
    )
    client = _client()

    with pytest.raises(APIError):
        list(client.subscribe_to_trade_events_v2())

    assert len(reqmock.request_history) == 1
    assert reqmock.request_history[0].headers["Accept"] == "text/event-stream"


def test_sse_http_error_raises_api_error(reqmock):
    reqmock.get(f"{_BASE}/v2/events/system", status_code=400, text="bad request")
    client = _client()

    with pytest.raises(APIError):
        list(client.subscribe_to_system_events())

    assert len(reqmock.request_history) == 1


def test_download_strips_authorization_when_the_host_changes(reqmock, tmp_path):
    target = "https://files.example/w8ben.pdf"
    reqmock.get(
        f"{_BASE}/v1/accounts/{_ACCOUNT}/documents/w8ben/{_OTHER}/download",
        status_code=302,
        headers={"Location": target},
    )
    reqmock.get(target, content=b"%PDF-cross")
    client = _client()
    destination = tmp_path / "w8ben.pdf"

    client.download_w8ben_document_for_account_by_id(_ACCOUNT, _OTHER, str(destination))

    assert destination.read_bytes() == b"%PDF-cross"
    assert "Authorization" in reqmock.request_history[0].headers
    assert "Authorization" not in reqmock.request_history[1].headers


def test_download_keeps_authorization_on_the_same_host(reqmock, tmp_path):
    target = f"{_BASE}/v1/files/w8ben.pdf"
    reqmock.get(
        f"{_BASE}/v1beta1/logos/AAPL",
        status_code=302,
        headers={"Location": target},
    )
    reqmock.get(target, content=b"\x89PNG-same")
    client = _client()

    payload = client.get_logo("AAPL")

    assert payload == b"\x89PNG-same"
    assert reqmock.request_history[0].headers["Authorization"] == (
        reqmock.request_history[1].headers["Authorization"]
    )


def test_download_does_not_retry_a_terminal_http_error(reqmock, tmp_path):
    reqmock.get(
        f"{_BASE}/v1/accounts/{_ACCOUNT}/documents/w8ben/{_OTHER}/download",
        status_code=404,
        text="missing",
    )
    client = _client()

    with pytest.raises(APIError):
        client.download_w8ben_document_for_account_by_id(
            _ACCOUNT, _OTHER, str(tmp_path / "missing.pdf")
        )

    assert len(reqmock.request_history) == 1
    assert not (tmp_path / "missing.pdf").exists()


@pytest.mark.parametrize(
    "target_host", ["broker-api.sandbox.alpaca.markets", "files.example"]
)
def test_download_refuses_https_downgrades(reqmock, target_host):
    target = f"http://{target_host}/logo.png"
    reqmock.get(
        f"{_BASE}/v1beta1/logos/AAPL",
        status_code=302,
        headers={"Location": target},
    )
    reqmock.get(target, content=b"image")

    with pytest.raises(APIError, match="HTTPS download redirect to HTTP refused"):
        _client().get_logo("AAPL")

    assert len(reqmock.request_history) == 1


@pytest.mark.parametrize("port, authenticated", [(443, True), (8443, False)])
def test_download_compares_effective_ports(reqmock, port, authenticated):
    target = f"https://{urlparse(_BASE).hostname}:{port}/logo.png"
    reqmock.get(
        f"{_BASE}/v1beta1/logos/AAPL",
        status_code=302,
        headers={"Location": target},
    )
    reqmock.get(target, content=b"image")

    assert _client().get_logo("AAPL") == b"image"
    assert ("Authorization" in reqmock.request_history[1].headers) is authenticated


def test_download_does_not_restore_credentials_after_cross_origin_redirect(reqmock):
    external = "https://files.example/logo.png"
    final = f"{_BASE}/logo.png"
    reqmock.get(
        f"{_BASE}/v1beta1/logos/AAPL",
        status_code=302,
        headers={"Location": external},
    )
    reqmock.get(external, status_code=302, headers={"Location": final})
    reqmock.get(final, content=b"image")

    assert _client().get_logo("AAPL") == b"image"
    assert "Authorization" in reqmock.request_history[0].headers
    assert all(
        "Authorization" not in request.headers
        for request in reqmock.request_history[1:]
    )


@pytest.mark.parametrize("raw_data", [False, True])
@pytest.mark.parametrize(
    "name",
    [
        "get_tokenization_request_by_client_request_id",
        "get_tokenization_request_by_id",
        "get_tokenization_request_by_issuer_request_id",
        "list_tokenization_requests",
        "submit_tokenization_mint_callback",
        "create_tokenization_mint",
    ],
)
def test_tokenization_responses_follow_oas(reqmock, name, raw_data):
    spec = json.loads(
        (
            Path(__file__).resolve().parents[3] / "tools/openapi/specs/broker-api.json"
        ).read_text()
    )
    example = spec["paths"][
        "/v1/accounts/{account_id}/tokenization/requests/{tokenization_request_id}"
    ]["get"]["responses"]["200"]["content"]["application/json"]["example"]
    schema_name = (
        "TokenizationMintResponse"
        if name == "create_tokenization_mint"
        else "TokenizationRequest"
    )
    schema = spec["components"]["schemas"][schema_name]
    # Exercise an OAS-valid response with only required fields; no UUID `id` exists.
    payload = {field: example[field] for field in schema["required"]}
    assert "id" not in schema["properties"]
    if name == "list_tokenization_requests":
        payload = [payload]
    _, http, path, args, kwargs, _ = next(case for case in _CASES if case[0] == name)
    getattr(reqmock, http)(f"{_BASE}{path}", json=payload)
    client = BrokerClient("key-id", "secret-key", sandbox=True, raw_data=raw_data)

    result = getattr(client, name)(*args, **kwargs)

    if raw_data:
        assert result == payload
    else:
        parsed = result[0] if isinstance(result, list) else result
        assert parsed.tokenization_request_id == example["tokenization_request_id"]
        assert parsed.qty == example["qty"]
        assert parsed.created_at.isoformat() == "2025-11-04T18:38:01.942282+00:00"
        assert "id" not in type(parsed).model_fields


def test_cip_methods_issue_http_requests(reqmock):
    reqmock.get(
        f"{_BASE}/v1/accounts/{_ACCOUNT}/cip", json={"provider_name": ["alpaca"]}
    )
    reqmock.post(f"{_BASE}/v1/accounts/{_ACCOUNT}/cip", json={})
    client = _client()

    loaded = client.get_cip_data_for_account_by_id(_ACCOUNT)
    client.upload_cip_data_for_account_by_id(
        _ACCOUNT, GeneratedCIPInfo(provider_name=["alpaca"])
    )

    assert loaded == {"provider_name": ["alpaca"]}
    assert [request.method for request in reqmock.request_history] == ["GET", "POST"]
