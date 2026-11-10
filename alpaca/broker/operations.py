"""Public Broker methods for the official operations that BrokerClient did not expose.

Streaming and file downloads bypass ``RESTClient._request`` so they can keep the
socket open. Redirects are refused for event streams. File downloads follow a
redirect only after dropping ``Authorization`` when the origin changes.
HTTPS-to-HTTP redirects are refused.
"""

import time

import sseclient
from typing import Dict, Iterator, List, Optional, Union
from urllib.parse import urljoin, urlparse
from uuid import UUID

from pydantic import TypeAdapter
from requests import HTTPError

from alpaca.broker._generated.models import CIPInfo as GeneratedCIPInfo
from alpaca.broker.models import (
    AcatsAsset,
    AcatsInitiateTransferResponse,
    AcatsListContraBrokersResponse,
    AcatsListTransfersResponse,
    AcatsTransfer,
    AccountLimit,
    AccountTradingLimit,
    Activity,
    AggregatePositionResponse,
    AssetEntryRequirements,
    AuthorizeOAuthTokenResponse,
    BatchCreateFundingWalletResponse,
    ClockResp,
    CorrespondentLimit,
    CountryInfo,
    CryptoTransfer,
    CryptoWallet,
    DailyTradingLimit,
    DemoFundingTransfer,
    EoDCashInterestReportResponse,
    FPSLAnalyticsLoansResponse,
    FPSLTier,
    FundingWallet,
    FundingWalletRecipientBank,
    FundingWalletTransfer,
    GetCryptoTransferEstimate200Response,
    GetOptionsContracts200Response,
    GetV1AccountsAccountIdOnfidoSdkTokens200Response,
    GetV1ReportingEodPositions200Response,
    GetV1TransfersJitLedgerIdBalances200Response,
    InstantFunding,
    IPOOfferingListResponse,
    IPOOfferingResponse,
    IssueOAuthTokenResponse,
    JITLedgerAccount,
    JITReportDownloadURL,
    ListAPRTiersResponse,
    ListFPSLLoansResponse,
    ListFundingDetails,
    ListTransfersResponse,
    OathClientResponse,
    OptionContract,
    OptionsApprovalResponse,
    OptionsApprovalsList,
    Order,
    OvercontributedIRAAccount,
    PublicCalendarResp,
    ReportsResponse,
    SearchVASPsResponse,
    SettlementResponse,
    SettlementsResponse,
    SignedAgreement,
    TokenizationMintCallback,
    TokenizationMintResponse,
    TokenizationRedeemResponse,
    UsCorporatesResp,
    UsTreasuriesResp,
    WhitelistedAddress,
)
from alpaca.broker.requests import (
    AcatsInitiateTransferRequest,
    BatchCreateFundingWalletRequest,
    CreateAccountAgreementRequest,
    CreateCryptoTransferRequest,
    CreateFundingWalletRecipientBankRequest,
    CreateFundingWalletWithdrawalRequest,
    CreateIFTransferRequest,
    CreateJITSettlementRequest,
    CreatePartyAgreementRequest,
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
    TokenizationRequest,
    UpdateWhitelistedAddressTravelRuleInfoRequest,
)
from alpaca.common import RawData
from alpaca.common.exceptions import APIError


def _resource_id(value: Union[UUID, str]) -> str:
    """Render a path id without requiring it to be a UUID."""
    return str(value)


def _object_or_list(model: type) -> object:
    """Accept one object or an array of that object.

    Some Broker responses describe an array while the schema ``$ref`` is a
    single object. A JSON array becomes a list; a JSON object stays one model.
    """
    return Union[List[model], model]


class BrokerOperations:
    """Broker routes generated from the official OpenAPI document."""

    def _parse(self, annotation: object, response: RawData) -> Union[object, RawData]:
        if self._use_raw_data:
            return response
        if response is None:
            return None
        return TypeAdapter(annotation).validate_python(response)

    def _query(self, request: Optional[object]) -> dict:
        """Render query fields, including booleans and comma-separated lists."""
        if request is None:
            return {}
        rendered = {}
        for key, value in request.to_request_fields().items():
            if isinstance(value, bool):
                rendered[key] = str(value).lower()
            elif isinstance(value, list):
                rendered[key] = ",".join(str(item) for item in value)
            else:
                rendered[key] = value
        return rendered

    def _payload(self, data: Optional[object]) -> Optional[object]:
        if data is None:
            return None
        if hasattr(data, "to_request_fields"):
            return data.to_request_fields()
        if hasattr(data, "model_dump"):
            return data.model_dump(mode="json", exclude_none=True, by_alias=True)
        return data

    def _sse_headers(self) -> dict:
        headers = self._get_default_headers()
        headers["Connection"] = "keep-alive"
        headers["Cache-Control"] = "no-cache"
        headers["Accept"] = "text/event-stream"
        return headers

    def _iter_server_events(
        self,
        path: str,
        events_filter: Optional[GetEventsRequest] = None,
        api_version: Optional[str] = None,
    ) -> Iterator[str]:
        """Yield SSE payloads from ``path``.

        Redirects are refused. Auth headers stay on the configured host, and the
        response is closed when the caller finishes or closes the iterator.
        """
        version = api_version or self._api_version
        url = self._base_url + "/" + version + path
        response = self._session.get(
            url=url,
            params=self._query(events_filter),
            stream=True,
            headers=self._sse_headers(),
            allow_redirects=False,
        )
        try:
            if response.is_redirect:
                detail = response.text or "SSE redirect refused"
                raise APIError(detail)
            try:
                response.raise_for_status()
            except HTTPError as http_error:
                raise APIError(response.text, http_error)
            client = sseclient.SSEClient(response)
            for event in client.events():
                yield event.data
        finally:
            response.close()

    def _read_download(self, url: str, params: Optional[dict] = None) -> bytes:
        """GET a file, refusing HTTPS downgrades and stripping auth across origins."""
        last_error: Optional[HTTPError] = None
        for attempt in range(self._retry + 1):
            headers = self._get_default_headers()
            response = self._session.get(
                url=url,
                params=params,
                headers=headers,
                allow_redirects=False,
                stream=True,
            )
            try:
                hops = 0
                while response.is_redirect:
                    if hops >= 5:
                        raise APIError("too many redirects")
                    location = response.headers.get("Location")
                    if not location:
                        break
                    target = urljoin(response.url, location)
                    source_url = urlparse(response.url)
                    target_url = urlparse(target)
                    if source_url.scheme == "https" and target_url.scheme == "http":
                        raise APIError("HTTPS download redirect to HTTP refused")
                    source_origin = (
                        source_url.scheme,
                        source_url.hostname,
                        source_url.port
                        or (443 if source_url.scheme == "https" else 80),
                    )
                    target_origin = (
                        target_url.scheme,
                        target_url.hostname,
                        target_url.port
                        or (443 if target_url.scheme == "https" else 80),
                    )
                    if target_origin != source_origin:
                        headers.pop("Authorization", None)
                    response.close()
                    response = self._session.get(
                        url=target,
                        headers=headers,
                        allow_redirects=False,
                        stream=True,
                    )
                    hops += 1
                try:
                    response.raise_for_status()
                except HTTPError as http_error:
                    if (
                        response.status_code in self._retry_codes
                        and attempt < self._retry
                    ):
                        last_error = http_error
                        time.sleep(self._retry_wait)
                        continue
                    raise APIError(response.text, http_error) from http_error
                return b"".join(
                    chunk for chunk in response.iter_content(chunk_size=None) if chunk
                )
            finally:
                response.close()
        raise APIError("download failed", last_error)

    def _download_to_file(
        self, url: str, file_path: str, params: Optional[dict] = None
    ) -> None:
        payload = self._read_download(url, params)
        with open(file_path, "wb") as handle:
            handle.write(payload)

    def create_agreement(
        self, request: Union[CreateAccountAgreementRequest, CreatePartyAgreementRequest]
    ) -> Union[SignedAgreement, RawData]:
        """Create a Signed Agreement."""
        response = self.post("/agreements", self._payload(request))
        return self._parse(SignedAgreement, response)

    def get_account_activities_by_type(
        self,
        activity_type: Union[UUID, str],
        filter: Optional[GetAccountActivitiesByTypeRequest] = None,
    ) -> Union[List[Activity], RawData]:
        """Retrieve Account Activities of Specific Type."""
        response = self.get(
            f"/accounts/activities/{_resource_id(activity_type)}", self._query(filter)
        )
        return self._parse(List[Activity], response)

    def get_account_activity_event(
        self, account_id: Union[UUID, str], event_id: Union[UUID, str]
    ) -> Iterator[str]:
        """Get a single activity (V2) event by event_id ULID.

        Returns:
            Iterator[str]: Event payloads as they arrive.
        """
        return self._iter_server_events(
            f"/accounts/{_resource_id(account_id)}/events/activities/{_resource_id(event_id)}",
            api_version="v2beta1",
        )

    def get_cip_data_for_account_by_id(
        self, account_id: Union[UUID, str]
    ) -> Union[GeneratedCIPInfo, RawData]:
        """Retrieve CIP information."""
        response = self.get(f"/accounts/{_resource_id(account_id)}/cip")
        return self._parse(GeneratedCIPInfo, response)

    def upload_cip_data_for_account_by_id(
        self, account_id: Union[UUID, str], request: GeneratedCIPInfo
    ) -> Union[RawData, None]:
        """Upload CIP information."""
        response = self.post(
            f"/accounts/{_resource_id(account_id)}/cip", self._payload(request)
        )
        return response

    def get_onfido_sdk_token(
        self,
        account_id: Union[UUID, str],
        filter: Optional[GetOnfidoSdkTokenRequest] = None,
    ) -> Union[GetV1AccountsAccountIdOnfidoSdkTokens200Response, RawData]:
        """Retrieve an Onfido SDK Token."""
        response = self.get(
            f"/accounts/{_resource_id(account_id)}/onfido/sdk/tokens",
            self._query(filter),
        )
        return self._parse(GetV1AccountsAccountIdOnfidoSdkTokens200Response, response)

    def update_onfido_sdk_outcome(
        self,
        account_id: Union[UUID, str],
        request: PatchV1AccountsAccountIdOnfidoSdkRequest,
    ) -> Union[RawData, None]:
        """Update the Onfido SDK Outcome."""
        response = self.patch(
            f"/accounts/{_resource_id(account_id)}/onfido/sdk", self._payload(request)
        )
        return response

    def get_account_trading_limits(
        self, account_id: Union[UUID, str]
    ) -> Union[AccountTradingLimit, RawData]:
        """Retrieve real-time Trading Limits for an Account."""
        response = self.get(f"/trading/accounts/{_resource_id(account_id)}/limits")
        return self._parse(AccountTradingLimit, response)

    def list_ira_excess_contributions(
        self,
    ) -> Union[List[OvercontributedIRAAccount], RawData]:
        """Retrieve Excess Contributions."""
        response = self.get("/accounts/ira_excess_contributions")
        return self._parse(List[OvercontributedIRAAccount], response)

    def get_country_info(self) -> Union[Dict[str, CountryInfo], RawData]:
        """Retrieve countries information."""
        response = self.get("/country-info")
        return self._parse(Dict[str, CountryInfo], response)

    def list_options_approvals(
        self, filter: Optional[ListOptionsApprovalsRequest] = None
    ) -> Union[OptionsApprovalsList, RawData]:
        """Retrieve options level approval requests (BETA)."""
        response = self.get("/accounts/options/approvals", self._query(filter))
        return self._parse(OptionsApprovalsList, response)

    def request_options_approval(
        self, account_id: Union[UUID, str], request: OptionsApprovalRequest
    ) -> Union[OptionsApprovalResponse, RawData]:
        """Request options trading for an account (BETA)."""
        response = self.post(
            f"/accounts/{_resource_id(account_id)}/options/approval",
            self._payload(request),
        )
        return self._parse(OptionsApprovalResponse, response)

    def download_w8ben_document_for_account_by_id(
        self,
        account_id: Union[UUID, str],
        document_id: Union[UUID, str],
        file_path: str,
    ) -> None:
        """Download the W8BEN document for the primary owner of an account.

        The document endpoint answers with a redirect to the PDF. The
        download follows that redirect and writes the body to ``file_path``.
        """
        url = (
            self._base_url
            + "/"
            + "v1"
            + f"/accounts/{_resource_id(account_id)}/documents/w8ben/{_resource_id(document_id)}/download"
        )
        self._download_to_file(url, file_path)

    def batch_create_funding_wallets(
        self, request: BatchCreateFundingWalletRequest
    ) -> Union[BatchCreateFundingWalletResponse, RawData]:
        """Batch create funding wallets."""
        response = self.post(
            "/accounts/funding_wallet", self._payload(request), api_version="v1beta"
        )
        return self._parse(BatchCreateFundingWalletResponse, response)

    def create_funding_wallet(
        self, account_id: Union[UUID, str]
    ) -> Union[FundingWallet, RawData]:
        """Creates a funding wallet."""
        response = self.post(
            f"/accounts/{_resource_id(account_id)}/funding_wallet",
            None,
            api_version="v1beta",
        )
        return self._parse(FundingWallet, response)

    def create_funding_wallet_recipient_bank(
        self,
        account_id: Union[UUID, str],
        request: CreateFundingWalletRecipientBankRequest,
    ) -> Union[FundingWalletRecipientBank, RawData]:
        """Create a recipient bank."""
        response = self.post(
            f"/accounts/{_resource_id(account_id)}/funding_wallet/recipient_bank",
            self._payload(request),
            api_version="v1beta",
        )
        return self._parse(FundingWalletRecipientBank, response)

    def create_funding_wallet_withdrawal(
        self,
        account_id: Union[UUID, str],
        request: CreateFundingWalletWithdrawalRequest,
    ) -> Union[FundingWalletTransfer, RawData]:
        """Create a withdrawal."""
        response = self.post(
            f"/accounts/{_resource_id(account_id)}/funding_wallet/withdrawal",
            self._payload(request),
            api_version="v1beta",
        )
        return self._parse(FundingWalletTransfer, response)

    def delete_funding_wallet_recipient_bank(
        self, account_id: Union[UUID, str]
    ) -> Union[RawData, None]:
        """Delete a recipient bank."""
        response = self.delete(
            f"/accounts/{_resource_id(account_id)}/funding_wallet/recipient_bank",
            api_version="v1beta",
        )
        return response

    def create_demo_funding_deposit(
        self, request: DemoFundingTransfer
    ) -> Union[DemoFundingTransfer, RawData]:
        """Create sandbox deposit transfer."""
        response = self.post(
            "/demo/banking/funding", self._payload(request), api_version="v1beta"
        )
        return self._parse(DemoFundingTransfer, response)

    def get_funding_wallet(
        self, account_id: Union[UUID, str]
    ) -> Union[FundingWallet, RawData]:
        """Retrieve funding wallet."""
        response = self.get(
            f"/accounts/{_resource_id(account_id)}/funding_wallet", api_version="v1beta"
        )
        return self._parse(FundingWallet, response)

    def get_funding_wallet_recipient_bank(
        self, account_id: Union[UUID, str]
    ) -> Union[RawData, None]:
        """Retrieve recipient bank."""
        response = self.get(
            f"/accounts/{_resource_id(account_id)}/funding_wallet/recipient_bank",
            api_version="v1beta",
        )
        return response

    def get_funding_wallet_transfer(
        self, account_id: Union[UUID, str], transfer_id: Union[UUID, str]
    ) -> Union[FundingWalletTransfer, RawData]:
        """Retrieve funding wallet transfer by ID."""
        response = self.get(
            f"/accounts/{_resource_id(account_id)}/funding_wallet/transfers/{_resource_id(transfer_id)}",
            api_version="v1beta",
        )
        return self._parse(FundingWalletTransfer, response)

    def get_funding_wallet_transfers(
        self, account_id: Union[UUID, str]
    ) -> Union[ListTransfersResponse, RawData]:
        """Retrieve funding wallet transfers."""
        response = self.get(
            f"/accounts/{_resource_id(account_id)}/funding_wallet/transfers",
            api_version="v1beta",
        )
        return self._parse(ListTransfersResponse, response)

    def list_funding_details(
        self,
        account_id: Union[UUID, str],
        filter: Optional[ListFundingDetailsRequest] = None,
    ) -> Union[List[ListFundingDetails], RawData]:
        """Retrieve funding details."""
        response = self.get(
            f"/accounts/{_resource_id(account_id)}/funding_wallet/funding_details",
            self._query(filter),
            api_version="v1beta",
        )
        return self._parse(List[ListFundingDetails], response)

    def cancel_instant_funding_transfer(
        self, instant_funding_id: Union[UUID, str]
    ) -> Union[RawData, None]:
        """Cancel an instant funding request."""
        response = self.delete(f"/instant_funding/{_resource_id(instant_funding_id)}")
        return response

    def get_instant_funding_account_limits(
        self, filter: Optional[GetInstantFundingAccountLimitsRequest] = None
    ) -> Union[List[AccountLimit], RawData]:
        """Get instant funding account limits."""
        response = self.get("/instant_funding/limits/accounts", self._query(filter))
        return self._parse(List[AccountLimit], response)

    def get_instant_funding_limits(self) -> Union[CorrespondentLimit, RawData]:
        """Get instant funding limits."""
        response = self.get("/instant_funding/limits")
        return self._parse(CorrespondentLimit, response)

    def get_instant_funding_transfers(
        self, filter: Optional[GetInstantFundingTransfersRequest] = None
    ) -> Union[List[InstantFunding], RawData]:
        """Get Instant Funding List."""
        response = self.get("/instant_funding", self._query(filter))
        return self._parse(List[InstantFunding], response)

    def get_instant_funding_reports(
        self, filter: Optional[GetInstantFundingReportsRequest] = None
    ) -> Union[List[ReportsResponse], RawData]:
        """Get instant funding report."""
        response = self.get("/instant_funding/reports", self._query(filter))
        return self._parse(List[ReportsResponse], response)

    def get_instant_funding_settlements(
        self, filter: Optional[GetInstantFundingSettlementsRequest] = None
    ) -> Union[SettlementsResponse, RawData]:
        """List settlements."""
        response = self.get("/instant_funding/settlements", self._query(filter))
        return self._parse(SettlementsResponse, response)

    def get_instant_funding_settlement(
        self, settlement_id: Union[UUID, str]
    ) -> Union[SettlementResponse, RawData]:
        """Get a single settlement."""
        response = self.get(
            f"/instant_funding/settlements/{_resource_id(settlement_id)}"
        )
        return self._parse(SettlementResponse, response)

    def get_instant_funding_transfer(
        self, instant_funding_id: Union[UUID, str]
    ) -> Union[InstantFunding, RawData]:
        """Get an instant funding request."""
        response = self.get(f"/instant_funding/{_resource_id(instant_funding_id)}")
        return self._parse(InstantFunding, response)

    def create_instant_funding_transfer(
        self, request: CreateIFTransferRequest
    ) -> Union[InstantFunding, RawData]:
        """Create an instant funding request."""
        response = self.post("/instant_funding", self._payload(request))
        return self._parse(InstantFunding, response)

    def create_instant_funding_settlement(
        self, request: CreateSettlementRequest
    ) -> Union[SettlementResponse, RawData]:
        """Create a new settlement."""
        response = self.post("/instant_funding/settlements", self._payload(request))
        return self._parse(SettlementResponse, response)

    def get_jit_settlements(
        self, filter: Optional[GetJitSettlementsRequest] = None
    ) -> Union[SettlementsResponse, RawData]:
        """List all JIT Settlements."""
        response = self.get("/jit/settlements", self._query(filter))
        return self._parse(SettlementsResponse, response)

    def get_jit_settlement(
        self, settlement_id: Union[UUID, str]
    ) -> Union[SettlementResponse, RawData]:
        """Get a single JIT settlement."""
        response = self.get(f"/jit/settlements/{_resource_id(settlement_id)}")
        return self._parse(SettlementResponse, response)

    def create_jit_settlement(
        self, request: CreateJITSettlementRequest
    ) -> Union[SettlementResponse, RawData]:
        """Create a new JIT settlement."""
        response = self.post("/jit/settlements", self._payload(request))
        return self._parse(SettlementResponse, response)

    def get_jit_ledger_balances(
        self,
        ledger_id: Union[UUID, str],
        filter: Optional[GetJitLedgerBalancesRequest] = None,
    ) -> Union[GetV1TransfersJitLedgerIdBalances200Response, RawData]:
        """Retrieve JIT Ledger Balances."""
        response = self.get(
            f"/transfers/jit/{_resource_id(ledger_id)}/balances", self._query(filter)
        )
        return self._parse(GetV1TransfersJitLedgerIdBalances200Response, response)

    def get_jit_ledgers(self) -> Union[List[JITLedgerAccount], RawData]:
        """Retrieve JIT Ledgers."""
        response = self.get("/transfers/jit/ledgers")
        return self._parse(List[JITLedgerAccount], response)

    def get_jit_limits(self) -> Union[DailyTradingLimit, RawData]:
        """Retrieve Daily Trading Limits."""
        response = self.get("/transfers/jit/limits")
        return self._parse(DailyTradingLimit, response)

    def get_jit_report(
        self, filter: Optional[GetJitReportRequest] = None
    ) -> Union[JITReportDownloadURL, RawData]:
        """Retrieve JIT Reports."""
        response = self.get("/transfers/jit/reports", self._query(filter))
        return self._parse(JITReportDownloadURL, response)

    def create_crypto_transfer_for_account(
        self, account_id: Union[UUID, str], request: CreateCryptoTransferRequest
    ) -> Union[CryptoTransfer, RawData]:
        """Request a New Withdrawal."""
        response = self.post(
            f"/accounts/{_resource_id(account_id)}/wallets/transfers",
            self._payload(request),
        )
        return self._parse(CryptoTransfer, response)

    def create_whitelisted_address(
        self, account_id: Union[UUID, str], request: CreateWhitelistedAddressRequest
    ) -> Union[WhitelistedAddress, RawData]:
        """Request a new whitelisted address."""
        response = self.post(
            f"/accounts/{_resource_id(account_id)}/wallets/whitelists",
            self._payload(request),
        )
        return self._parse(WhitelistedAddress, response)

    def delete_whitelisted_address(
        self, account_id: Union[UUID, str], whitelisted_address_id: Union[UUID, str]
    ) -> Union[RawData, None]:
        """Delete a whitelisted address."""
        response = self.delete(
            f"/accounts/{_resource_id(account_id)}/wallets/whitelists/{_resource_id(whitelisted_address_id)}"
        )
        return response

    def get_crypto_transfer(
        self, account_id: Union[UUID, str], transfer_id: Union[UUID, str]
    ) -> Union[CryptoTransfer, RawData]:
        """Retrieve a Crypto Funding Transfer."""
        response = self.get(
            f"/accounts/{_resource_id(account_id)}/wallets/transfers/{_resource_id(transfer_id)}"
        )
        return self._parse(CryptoTransfer, response)

    def get_crypto_transfer_estimate(
        self, filter: Optional[GetCryptoTransferEstimateRequest] = None
    ) -> Union[GetCryptoTransferEstimate200Response, RawData]:
        """Returns the estimated gas fee for a proposed transaction."""
        response = self.get("/wallets/fees/estimate", self._query(filter))
        return self._parse(GetCryptoTransferEstimate200Response, response)

    def list_crypto_transfers(
        self, account_id: Union[UUID, str]
    ) -> Union[List[CryptoTransfer], CryptoTransfer, RawData]:
        """Retrieve crypto funding transfers.

        The documented payload is an array. A single object is also accepted
        because the schema ``$ref`` is ``CryptoTransfer``.
        """
        response = self.get(f"/accounts/{_resource_id(account_id)}/wallets/transfers")
        return self._parse(_object_or_list(CryptoTransfer), response)

    def list_crypto_wallets(
        self,
        account_id: Union[UUID, str],
        filter: Optional[ListCryptoWalletsRequest] = None,
    ) -> Union[List[CryptoWallet], CryptoWallet, RawData]:
        """Retrieve crypto funding wallets.

        The response is one wallet when an asset is requested and an array of
        wallets otherwise. A single object is also accepted.
        """
        response = self.get(
            f"/accounts/{_resource_id(account_id)}/wallets", self._query(filter)
        )
        return self._parse(_object_or_list(CryptoWallet), response)

    def list_whitelisted_addresses(
        self, account_id: Union[UUID, str]
    ) -> Union[List[WhitelistedAddress], WhitelistedAddress, RawData]:
        """Retrieve whitelisted withdrawal addresses.

        The documented payload is an array. A single object is also accepted
        because the schema ``$ref`` is ``WhitelistedAddress``.
        """
        response = self.get(f"/accounts/{_resource_id(account_id)}/wallets/whitelists")
        return self._parse(_object_or_list(WhitelistedAddress), response)

    def search_vasps(
        self, filter: Optional[SearchVaspsRequest] = None
    ) -> Union[SearchVASPsResponse, RawData]:
        """Search for VASPs."""
        response = self.get("/wallets/travel-rule/vasps", self._query(filter))
        return self._parse(SearchVASPsResponse, response)

    def update_whitelisted_address_travel_rule(
        self,
        account_id: Union[UUID, str],
        whitelisted_address_id: Union[UUID, str],
        request: UpdateWhitelistedAddressTravelRuleInfoRequest,
    ) -> Union[RawData, None]:
        """Update travel rule information for a whitelisted wallet."""
        response = self.patch(
            f"/accounts/{_resource_id(account_id)}/wallets/whitelists/{_resource_id(whitelisted_address_id)}/travel-rule-info",
            self._payload(request),
        )
        return response

    def estimate_order_for_account(
        self,
        account_id: Union[UUID, str],
        request: GetV1TradingAccountsAccountIdOrdersEstimationRequest,
    ) -> Union[Order, RawData]:
        """Estimate an Order."""
        response = self.post(
            f"/trading/accounts/{_resource_id(account_id)}/orders/estimation",
            self._payload(request),
        )
        return self._parse(Order, response)

    def do_not_exercise_options_position_for_account(
        self, account_id: Union[UUID, str], symbol_or_contract_id: Union[UUID, str]
    ) -> Union[RawData, None]:
        """Do Not Exercise an Options Position."""
        response = self.post(
            f"/trading/accounts/{_resource_id(account_id)}/positions/{_resource_id(symbol_or_contract_id)}/do-not-exercise",
            {},
        )
        return response

    def get_v2_calendar(
        self, market: Union[UUID, str], filter: Optional[GetV2CalendarRequest] = None
    ) -> Union[PublicCalendarResp, RawData]:
        """Get Market Calendar."""
        response = self.get(
            f"/calendar/{_resource_id(market)}", self._query(filter), api_version="v2"
        )
        return self._parse(PublicCalendarResp, response)

    def get_v2_clock(
        self, filter: Optional[GetV2ClockRequest] = None
    ) -> Union[ClockResp, RawData]:
        """Get Market Clock."""
        response = self.get("/clock", self._query(filter), api_version="v2")
        return self._parse(ClockResp, response)

    def get_asset_entry_requirements(
        self, filter: Optional[GetAssetEntryRequirementsRequest] = None
    ) -> Union[List[AssetEntryRequirements], RawData]:
        """Retrieve Entry Requirements for requested assets."""
        response = self.get("/assets/entry-requirements", self._query(filter))
        return self._parse(List[AssetEntryRequirements], response)

    def get_option_contract(
        self, symbol_or_id: Union[UUID, str]
    ) -> Union[OptionContract, RawData]:
        """Get an option contract by ID or Symbol (BETA)."""
        response = self.get(f"/options/contracts/{_resource_id(symbol_or_id)}")
        return self._parse(OptionContract, response)

    def get_option_contracts(
        self, filter: Optional[GetOptionContractsRequest] = None
    ) -> Union[GetOptionsContracts200Response, RawData]:
        """Get Option Contracts (BETA)."""
        response = self.get("/options/contracts", self._query(filter))
        return self._parse(GetOptionsContracts200Response, response)

    def get_logo(
        self,
        symbol: str,
        logo_filter: Optional[GetLogoRequest] = None,
    ) -> bytes:
        """Get Logo.

        Args:
            symbol (str): Stock or crypto symbol.
            logo_filter: Optional placeholder flag. The official parameter is a string.

        Returns:
            bytes: The logo image.
        """
        url = self._base_url + "/v1beta1/logos/" + _resource_id(symbol)
        return self._read_download(url, self._query(logo_filter) or None)

    def get_us_corporate_bonds(
        self, filter: Optional[GetUsCorporateBondsRequest] = None
    ) -> Union[UsCorporatesResp, RawData]:
        """Get US corporates."""
        response = self.get("/assets/fixed_income/us_corporates", self._query(filter))
        return self._parse(UsCorporatesResp, response)

    def get_us_treasuries(
        self, filter: Optional[GetUsTreasuriesRequest] = None
    ) -> Union[UsTreasuriesResp, RawData]:
        """Get US treasuries."""
        response = self.get("/assets/fixed_income/us_treasuries", self._query(filter))
        return self._parse(UsTreasuriesResp, response)

    def authorize_oauth_token(
        self, request: OAuthTokenRequest
    ) -> Union[AuthorizeOAuthTokenResponse, RawData]:
        """Authorize an OAuth Token."""
        response = self.post("/oauth/authorize", self._payload(request))
        return self._parse(AuthorizeOAuthTokenResponse, response)

    def get_oauth_client(
        self,
        client_id: Union[UUID, str],
        filter: Optional[GetOauthClientRequest] = None,
    ) -> Union[OathClientResponse, RawData]:
        """Get an OAuth client."""
        response = self.get(
            f"/oauth/clients/{_resource_id(client_id)}", self._query(filter)
        )
        return self._parse(OathClientResponse, response)

    def issue_oauth_token(
        self, request: OAuthTokenRequest
    ) -> Union[IssueOAuthTokenResponse, RawData]:
        """Issue an OAuth token."""
        response = self.post("/oauth/token", self._payload(request))
        return self._parse(IssueOAuthTokenResponse, response)

    def get_acats_transfer(
        self, account_id: Union[UUID, str], acats_id: Union[UUID, str]
    ) -> Union[AcatsTransfer, RawData]:
        """Get transfer details."""
        response = self.get(
            f"/acats/{_resource_id(account_id)}/{_resource_id(acats_id)}",
            api_version="v1beta1",
        )
        return self._parse(AcatsTransfer, response)

    def list_acats_assets(
        self, account_id: Union[UUID, str], acats_id: Union[UUID, str]
    ) -> Union[List[AcatsAsset], RawData]:
        """List assets for a transfer."""
        response = self.get(
            f"/acats/{_resource_id(account_id)}/{_resource_id(acats_id)}/assets",
            api_version="v1beta1",
        )
        return self._parse(List[AcatsAsset], response)

    def list_acats_contra_brokers(
        self,
    ) -> Union[AcatsListContraBrokersResponse, RawData]:
        """List contra brokers."""
        response = self.get("/acats/contrabrokers", api_version="v1beta1")
        return self._parse(AcatsListContraBrokersResponse, response)

    def list_acats_transfers(
        self, filter: Optional[ListAcatsTransfersRequest] = None
    ) -> Union[AcatsListTransfersResponse, RawData]:
        """List transfers."""
        response = self.get("/acats", self._query(filter), api_version="v1beta1")
        return self._parse(AcatsListTransfersResponse, response)

    def list_acats_transfers_for_account(
        self,
        account_id: Union[UUID, str],
        filter: Optional[ListAcatsTransfersForAccountRequest] = None,
    ) -> Union[AcatsListTransfersResponse, RawData]:
        """List transfers for an account."""
        response = self.get(
            f"/acats/{_resource_id(account_id)}",
            self._query(filter),
            api_version="v1beta1",
        )
        return self._parse(AcatsListTransfersResponse, response)

    def request_acats_transfer(
        self, account_id: Union[UUID, str], request: AcatsInitiateTransferRequest
    ) -> Union[AcatsInitiateTransferResponse, RawData]:
        """Initiate an incoming transfer."""
        response = self.post(
            f"/acats/{_resource_id(account_id)}",
            self._payload(request),
            api_version="v1beta1",
        )
        return self._parse(AcatsInitiateTransferResponse, response)

    def get_ipo_offering(
        self, offering_reference: Union[UUID, str]
    ) -> Union[IPOOfferingResponse, RawData]:
        """Retrieve an IPO Offering."""
        response = self.get(f"/ipos/{_resource_id(offering_reference)}")
        return self._parse(IPOOfferingResponse, response)

    def list_ipo_offerings(
        self, filter: Optional[ListIpoOfferingsRequest] = None
    ) -> Union[IPOOfferingListResponse, RawData]:
        """List IPO Offerings."""
        response = self.get("/ipos", self._query(filter))
        return self._parse(IPOOfferingListResponse, response)

    def get_tokenization_request_by_client_request_id(
        self,
        account_id: Union[UUID, str],
        filter: Optional[GetTokenizationRequestByClientRequestIdRequest] = None,
    ) -> Union[TokenizationRequest, RawData]:
        """Get Tokenization Request by `client_request_id`."""
        response = self.get(
            f"/accounts/{_resource_id(account_id)}/tokenization/requests:by_client_request_id",
            self._query(filter),
        )
        return self._parse(TokenizationRequest, response)

    def get_tokenization_request_by_id(
        self, account_id: Union[UUID, str], tokenization_request_id: Union[UUID, str]
    ) -> Union[TokenizationRequest, RawData]:
        """Get Tokenization Request by ID."""
        response = self.get(
            f"/accounts/{_resource_id(account_id)}/tokenization/requests/{_resource_id(tokenization_request_id)}"
        )
        return self._parse(TokenizationRequest, response)

    def get_tokenization_request_by_issuer_request_id(
        self,
        account_id: Union[UUID, str],
        filter: Optional[GetTokenizationRequestByIssuerRequestIdRequest] = None,
    ) -> Union[TokenizationRequest, RawData]:
        """Get Tokenization Request by `issuer_request_id`."""
        response = self.get(
            f"/accounts/{_resource_id(account_id)}/tokenization/requests:by_issuer_request_id",
            self._query(filter),
        )
        return self._parse(TokenizationRequest, response)

    def list_tokenization_requests(
        self,
        account_id: Union[UUID, str],
        filter: Optional[ListTokenizationRequestsRequest] = None,
    ) -> Union[List[TokenizationRequest], RawData]:
        """List Tokenization Requests."""
        response = self.get(
            f"/accounts/{_resource_id(account_id)}/tokenization/requests",
            self._query(filter),
        )
        return self._parse(List[TokenizationRequest], response)

    def submit_tokenization_mint_callback(
        self, account_id: Union[UUID, str], request: TokenizationMintCallback
    ) -> Union[TokenizationRequest, RawData]:
        """Confirm Tokenized Asset Minted."""
        response = self.post(
            f"/accounts/{_resource_id(account_id)}/tokenization/callback/mint",
            self._payload(request),
        )
        return self._parse(TokenizationRequest, response)

    def create_tokenization_mint(
        self, account_id: Union[UUID, str], request: TokenizationMintRequest
    ) -> Union[TokenizationMintResponse, RawData]:
        """Mint a Tokenized Asset."""
        response = self.post(
            f"/accounts/{_resource_id(account_id)}/tokenization/mint",
            self._payload(request),
        )
        return self._parse(TokenizationMintResponse, response)

    def submit_tokenization_redeem_callback(
        self, account_id: Union[UUID, str], request: TokenizationRedeemRequest
    ) -> Union[TokenizationRedeemResponse, RawData]:
        """Redeem a Tokenized Asset."""
        response = self.post(
            f"/accounts/{_resource_id(account_id)}/tokenization/callback/redeem",
            self._payload(request),
        )
        return self._parse(TokenizationRedeemResponse, response)

    def get_fpsl_account_loans(
        self,
        account_id: Union[UUID, str],
        filter: Optional[GetFpslAccountLoansRequest] = None,
    ) -> Union[FPSLAnalyticsLoansResponse, RawData]:
        """Read FPSL Loans Analytics for an Account."""
        response = self.get(
            f"/fpsl/analytics/{_resource_id(account_id)}/loans", self._query(filter)
        )
        return self._parse(FPSLAnalyticsLoansResponse, response)

    def list_apr_tiers(self) -> Union[ListAPRTiersResponse, RawData]:
        """List APR Tiers."""
        response = self.get("/cash_interest/apr_tiers")
        return self._parse(ListAPRTiersResponse, response)

    def list_fpsl_loans(
        self, filter: Optional[ListFpslLoansRequest] = None
    ) -> Union[ListFPSLLoansResponse, RawData]:
        """List FPSL Loans."""
        response = self.get("/fpsl/loans", self._query(filter))
        return self._parse(ListFPSLLoansResponse, response)

    def list_fpsl_tiers(self) -> Union[List[FPSLTier], RawData]:
        """List FPSL Tiers."""
        response = self.get("/fpsl/tiers")
        return self._parse(List[FPSLTier], response)

    def get_eod_cash_interest_report(
        self, filter: Optional[GetEodCashInterestReportRequest] = None
    ) -> Union[EoDCashInterestReportResponse, RawData]:
        """Retrieve EOD Cash Interest Details."""
        response = self.get("/reporting/eod/cash_interest", self._query(filter))
        return self._parse(EoDCashInterestReportResponse, response)

    def get_eod_aggregate_positions(
        self, filter: Optional[GetEodAggregatePositionsRequest] = None
    ) -> Union[List[AggregatePositionResponse], RawData]:
        """Retrieve Aggregate Positions."""
        response = self.get("/reporting/eod/aggregate_positions", self._query(filter))
        return self._parse(List[AggregatePositionResponse], response)

    def get_eod_positions(
        self, filter: Optional[GetEodPositionsRequest] = None
    ) -> Union[GetV1ReportingEodPositions200Response, RawData]:
        """Retrieve EOD Positions."""
        response = self.get("/reporting/eod/positions", self._query(filter))
        return self._parse(GetV1ReportingEodPositions200Response, response)

    def subscribe_to_activity_events(
        self, events_filter: Optional[GetEventsRequest] = None
    ) -> Iterator[str]:
        """Subscribe to Activity Events (SSE).

        Args:
            events_filter (Optional[GetEventsRequest]): Since, until, and id filters.

        Returns:
            Iterator[str]: Event payloads as they arrive.
        """
        return self._iter_server_events(
            "/events/activities", events_filter, api_version="v2beta1"
        )

    def subscribe_to_admin_action_events(
        self, events_filter: Optional[GetEventsRequest] = None
    ) -> Iterator[str]:
        """Subscribe to Admin Action Events (SSE).

        Args:
            events_filter (Optional[GetEventsRequest]): Since, until, and id filters.

        Returns:
            Iterator[str]: Event payloads as they arrive.
        """
        return self._iter_server_events(
            "/events/admin-actions", events_filter, api_version="v2"
        )

    def subscribe_to_funding_status_events(
        self, events_filter: Optional[GetEventsRequest] = None
    ) -> Iterator[str]:
        """Subscribe to Funding Status Events (SSE).

        Args:
            events_filter (Optional[GetEventsRequest]): Since, until, and id filters.

        Returns:
            Iterator[str]: Event payloads as they arrive.
        """
        return self._iter_server_events(
            "/events/funding/status", events_filter, api_version="v2"
        )

    def subscribe_to_ipo_events(
        self, events_filter: Optional[GetEventsRequest] = None
    ) -> Iterator[str]:
        """Subscribe to IPO Events (SSE).

        Args:
            events_filter (Optional[GetEventsRequest]): Since, until, and id filters.

        Returns:
            Iterator[str]: Event payloads as they arrive.
        """
        return self._iter_server_events("/events/ipos", events_filter, api_version="v2")

    def subscribe_to_journal_status_events_v2(
        self, events_filter: Optional[GetEventsRequest] = None
    ) -> Iterator[str]:
        """Subscribe to Journal Events (SSE).

        Args:
            events_filter (Optional[GetEventsRequest]): Since, until, and id filters.

        Returns:
            Iterator[str]: Event payloads as they arrive.
        """
        return self._iter_server_events(
            "/events/journals/status", events_filter, api_version="v2"
        )

    def subscribe_to_system_events(
        self, events_filter: Optional[GetEventsRequest] = None
    ) -> Iterator[str]:
        """Subscribe to System Events (SSE).

        Args:
            events_filter (Optional[GetEventsRequest]): Since, until, and id filters.

        Returns:
            Iterator[str]: Event payloads as they arrive.
        """
        return self._iter_server_events(
            "/events/system", events_filter, api_version="v2"
        )

    def subscribe_to_trade_events_v2(
        self, events_filter: Optional[GetEventsRequest] = None
    ) -> Iterator[str]:
        """Subscribe to Trade Events (SSE).

        Args:
            events_filter (Optional[GetEventsRequest]): Since, until, and id filters.

        Returns:
            Iterator[str]: Event payloads as they arrive.
        """
        return self._iter_server_events(
            "/events/trades", events_filter, api_version="v2"
        )
