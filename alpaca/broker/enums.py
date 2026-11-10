from enum import Enum

from typing_extensions import deprecated as _deprecated

from alpaca._deprecating_enum import DeprecatingEnumMeta as _DeprecatingEnumMeta

# Explicit rather than `import *`: the hand-written overrides bound below (same
# names: compatibility shapes or SDK subclasses) are left out, so static analysis
# (type checkers, AexPy) sees the same classes as runtime. The generated-
# compatibility tests fail when a new generated name is missing here.
from alpaca.broker._generated.enums import (
    AcatsAccountType,
    AcatsAssetAssetClass,
    AcatsAssetStatus,
    AcatsCashBalanceCurrency,
    AcatsContraBrokerType,
    AcatsDtccStatus,
    AcatsDtccTransferType,
    AcatsEquityPosition,
    AcatsInitiateTransferType,
    AcatsPosition,
    AcatsRejectionDetailsRejectionReason,
    AcatsSortDirection,
    AcatsTransferDirection,
    AcatsTransferStatus,
    AccountConfigurationsMaxOptionsTradingLevel,
    AccountConfigurationsTradeConfirmEmail,
    AccountCreationRequestInvestmentObjective,
    AccountCreationRequestInvestmentTimeHorizon,
    AccountCreationRequestLiquidityNeeds,
    AccountCreationRequestRiskTolerance,
    AccountCreationType,
    AccountDocumentType,
    AccountStatus,
    AccountSubType,
    AccountType,
    ACHRelationshipBankAccountType,
    ACHRelationshipStatus,
    ActivityType,
    ActivityV2DetailTRDExecutionType,
    ActivityV2DetailTRDSide,
    AdminActionAcatsTransferDirection,
    AdminActionAcatsTransferType,
    AdminActionBelongsToKind,
    AdminActionCategory,
    AdminActionContextAcatsStatusType,
    AdminActionContextLegacyNoteType,
    AdminActionContextLiquidationType,
    AdminActionContextTransactionCancelType,
    AdminActionCreatedByKind,
    AdminActionType,
    AdminActionVisibility,
    AdminConfigurationsMaxOptionsTradingLevel,
    AdvancedInstructionsAlgorithm,
    AdvancedInstructionsDestination,
    AnnouncementCASubType,
    AnnouncementCAType,
    AssetBorrowStatus,
    AssetClass,
    AssetStatus,
    BankBankCodeType,
    BankStatus,
    BatchJournalRequestEntryType,
    BeneficiaryRelationship,
    BeneficiaryTaxIdType,
    BeneficiaryType,
    BondStatus,
    CalendarTimezoneParameter,
    CallType,
    CIPKYCApprovalStatus,
    CIPPhotoStatus,
    CommissionType,
    CommonCDIVActivityV2Foreign,
    CommonCDIVActivityV2Special,
    CountryInfoCryptoRiskRating,
    CountryInfoSecuritiesRiskRating,
    CouponFrequency,
    CouponType,
    CreateACHRelationshipRequestBankAccountType,
    CreateCryptoTransferRequestChain,
    CreateFundingWalletRecipientBankRequestAccountType,
    CreateFundingWalletRecipientBankRequestRoutingCodeType,
    CreateWhitelistedAddressRequestChain,
    CryptoTransferStatus,
    DayCount,
    DisclosureContextAnnotationContextType,
    DisclosuresEmploymentSector,
    DisclosuresEmploymentStatus,
    EnabledAssetClass,
    Exchange,
    FeePaymentType,
    FeeType,
    FixedIncomeInterestType,
    FundingDetailPaymentType,
    FundingDetailRoutingCodeType,
    FundingWalletStatus,
    FundingWalletTransferDirection,
    FundingWalletTransferStatus,
    GetAccountActivitiesCategoryParameter,
    GetAllAccountsEntitiesParameter,
    GetAllAccountsSortParameter,
    GetAllJournalsEntryTypeParameter,
    GetAllOrdersForAccountAssetClassParameterInner,
    GetAllOrdersForAccountStatusParameter,
    GetAssetsAssetClassParameter,
    GetAssetsAttributesParameterInner,
    GetAssetsStatusParameter,
    GetCorporateAnnouncementsDateTypeParameter,
    GetDocsForAccountTypeParameter,
    GetOAuthClientResponseTypeParameter,
    GetOptionsContractsStatusParameter,
    GetOptionsContractsStyleParameter,
    GetOptionsContractsTypeParameter,
    GetRecipientBanksStatusParameter,
    GetTokenizationRequestsBrokerStatusParameter,
    GetTokenizationRequestsBrokerTypeParameter,
    GetTransfersForAccountDirectionParameter,
    GetV1RebalancingPortfoliosStatusParameter,
    GetV1TradingAccountsAccountIdAccountPortfolioHistoryIntradayReportingParameter,
    GetV1TradingAccountsAccountIdAccountPortfolioHistoryPnlResetParameter,
    GetV1TransfersJitReportsAssetClassParameter,
    GetV1TransfersJitReportsResponseTypeParameter,
    IdentityFundingSourceInner,
    IdentityInvestmentExperienceWithOptions,
    IdentityInvestmentExperienceWithStocks,
    IdentityInvestmentObjective,
    IdentityInvestmentTimeHorizon,
    IdentityLiquidityNeeds,
    IdentityMaritalStatus,
    IdentityRiskTolerance,
    IFFeeType,
    InstantFundingStatus,
    IPOEventVerb,
    IPOOfferingAvailability,
    IssueOAuthTokenResponseTokenType,
    JITAssetClass,
    JITReportType,
    JNLCAllOfEntryType,
    JNLSAllOfEntryType,
    JournalStatus,
    JournalStatusEventV2IdempotencyKeyType,
    JournalStatusFromOneOf,
    LegacyCalendarDateTypeParameter,
    ListACATSTransfersSortByParameter,
    ListIPOOfferingsAvailabilityParameter,
    ListSortBy,
    Market,
    NonTradeActivityEventStatus,
    NonTradeActivityStatus,
    OathClientResponseStatus,
    OptionContractStatus,
    OptionContractStyle,
    OptionContractType,
    OptionDeliverableSettlementMethod,
    OptionDeliverableSettlementType,
    OptionDeliverableType,
    OptionsApprovalRequestLevel,
    OptionsApprovalResponseApprovedLevel,
    OptionsApprovalResponseRequestedLevel,
    OptionsApprovalResponseRequester,
    OptionsApprovalStatus,
    OrderClass,
    OrderGroupRole,
    OrderSide,
    OrderStatus,
    OrderType,
    OwnerDocumentType,
    PartyAgreementType,
    PartyErrorResponseError,
    PerAccountAgreementType,
    Phase,
    PortfolioHistoryTimeframe,
    PortfolioRunInitiatedFrom,
    PortfolioRunStatus,
    PortfolioRunType,
    PortfolioStatus,
    PortfolioWeightRequestType,
    PositionIntent,
    PositionSide,
    PostV1RebalancingRunsRequestType,
    RequestListOptionsApprovalsApprovedLevelParameter,
    RequestListOptionsApprovalsRequestedLevelParameter,
    SettlementStatus,
    SignedAgreementType,
    SortOrder,
    SpOutlook,
    SystemEventV2Type,
    TimeInForce,
    TokenizationIssuer,
    TokenizationNetwork,
    TokenizationRequestStatus,
    TokenizationRequestType,
    TokenizationTransferStatus,
    TradeAccountOptionsApprovedLevel,
    TradeAccountOptionsTradingLevel,
    TradeActivitySide,
    TradeActivityType,
    TradeUpdateEventType,
    TransferDirection,
    TransferType,
    TravelRuleNextActionType,
    TravelRuleRequiredFieldValueType,
    TravelRuleValidationErrorCode,
    TreasurySubtype,
    V1AccountsAccountIdWalletsChainParameter,
    V1AccountsAccountIdWalletsNetworkParameter,
    V1AccountsActivitiesActivityTypeActivityTypeParameter,
    WhitelistedAddressStatus,
)

# Same-name generated enums with matching members are used as-is via the import above:
# AccountSubType, AccountType, ACHRelationshipStatus, BankStatus, JournalStatus,
# PortfolioStatus, TransferDirection, TransferType
#
# AgreementType, JournalEntryType, TaxIdType and TransferStatus share their name with
# a generated twin, so users have nothing else to migrate to. Their deprecation is
# static only (category=None): type checkers and IDEs flag them, naming the members
# the twin lacks, while runtime warnings come only from those members. The public
# name switches to the generated enum once those members are removed.
#
# Deprecated enums pass stacklevel=2 so the warning from ``Enum(value)`` points at
# the caller rather than at enum.py, where Python's default filters would hide it.


_AGREEMENT_TYPE_RENAMES = {
    "MARGIN": "MARGIN_AGREEMENT",
    "ACCOUNT": "ACCOUNT_AGREEMENT",
    "CUSTOMER": "CUSTOMER_AGREEMENT",
    "CRYPTO": "CRYPTO_AGREEMENT",
    "OPTIONS": "OPTIONS_AGREEMENT",
}

_DEPRECATED_AGREEMENT_TYPES = {
    old_name: (
        f"AgreementType.{old_name} is deprecated and will be removed in the next release. "
        f"Use AgreementType.{new_name}."
    )
    for old_name, new_name in _AGREEMENT_TYPE_RENAMES.items()
}
_DEPRECATED_AGREEMENT_TYPES["CUSTODIAL_CUSTOMER"] = (
    "AgreementType.CUSTODIAL_CUSTOMER is deprecated and will be removed in the next release. "
    "It is no longer a valid agreement type."
)


@_deprecated(
    "AgreementType is a temporary compatibility shape and will be replaced by the "
    "OpenAPI-generated AgreementType in a future release. That enum has no MARGIN, "
    "ACCOUNT, CUSTOMER, CRYPTO, OPTIONS or CUSTODIAL_CUSTOMER members; use the "
    "*_AGREEMENT members.",
    category=None,
)
class AgreementType(
    str,
    Enum,
    metaclass=_DeprecatingEnumMeta,
    deprecations=_DEPRECATED_AGREEMENT_TYPES,
):
    """
    The types of agreements that are to be signed by the user

    see https://docs.alpaca.markets/reference/createaccount

    MARGIN, ACCOUNT, CUSTOMER, CRYPTO, and OPTIONS are deprecated and will be
    removed in the next release. Use MARGIN_AGREEMENT, ACCOUNT_AGREEMENT,
    CUSTOMER_AGREEMENT, CRYPTO_AGREEMENT, and OPTIONS_AGREEMENT. The wire
    values are unchanged.

    CUSTODIAL_CUSTOMER is deprecated and will be removed in the next release.
    It is no longer a valid agreement type.

    .. deprecated:: 0.45.0
        Will be replaced by the OpenAPI-generated ``AgreementType``, which has no
        ``MARGIN``, ``ACCOUNT``, ``CUSTOMER``, ``CRYPTO``, ``OPTIONS`` or
        ``CUSTODIAL_CUSTOMER`` members. Use the ``*_AGREEMENT`` members.
    """

    MARGIN_AGREEMENT = "margin_agreement"
    ACCOUNT_AGREEMENT = "account_agreement"
    CUSTOMER_AGREEMENT = "customer_agreement"
    CRYPTO_AGREEMENT = "crypto_agreement"
    OPTIONS_AGREEMENT = "options_agreement"
    # Deprecated names for the members above. Same wire values.
    MARGIN = MARGIN_AGREEMENT
    ACCOUNT = ACCOUNT_AGREEMENT
    CUSTOMER = CUSTOMER_AGREEMENT
    CRYPTO = CRYPTO_AGREEMENT
    OPTIONS = OPTIONS_AGREEMENT
    CUSTODIAL_CUSTOMER = "custodial_customer_agreement"


_DEPRECATED_JOURNAL_ENTRY_TYPES = {
    "CASH": (
        "JournalEntryType.CASH is deprecated and will be removed in a future version. "
        "Please use `JournalEntryType.JNLC` instead."
    ),
    "SECURITY": (
        "JournalEntryType.SECURITY is deprecated and will be removed in a future "
        "version. Please use `JournalEntryType.JNLS` instead."
    ),
}


@_deprecated(
    "JournalEntryType is a temporary compatibility shape and will be replaced by the "
    "OpenAPI-generated JournalEntryType in a future release. That enum has no CASH "
    "or SECURITY members; use JNLC and JNLS.",
    category=None,
)
class JournalEntryType(
    str,
    Enum,
    metaclass=_DeprecatingEnumMeta,
    deprecations=_DEPRECATED_JOURNAL_ENTRY_TYPES,
):
    """
    Represents the types of journals. Cash journals are transfers of cash.
    Security journals are transfers of securities like stocks.

    Please see https://alpaca.markets/docs/api-references/broker-api/journals/ for more details.

    CASH and SECURITY are deprecated and will be removed in a future version. Use
    JNLC and JNLS. The wire values are unchanged.

    .. deprecated:: 0.45.0
        Will be replaced by the OpenAPI-generated ``JournalEntryType``, which has no
        ``CASH`` or ``SECURITY`` members. Use ``JNLC`` and ``JNLS``.
    """

    JNLC = "JNLC"
    JNLS = "JNLS"
    # Deprecated names for the members above. Same wire values.
    CASH = JNLC
    SECURITY = JNLS


# The generated twin spells ARG_AR_CUIT as ARG_AG_CUIT, which looks like a spec
# typo (see docs/openapi-spec-discrepancies.md), so ARG_AR_CUIT is not deprecated
# and the switch waits for the spec fix.
@_deprecated(
    "TaxIdType is a temporary compatibility shape and will be replaced by the "
    "OpenAPI-generated TaxIdType in a future release. The switch waits for the "
    "spec to spell ARG_AR_CUIT correctly; it currently has ARG_AG_CUIT.",
    category=None,
)
class TaxIdType(str, Enum):
    """The various country specific tax identification numbers

    see https://alpaca.markets/docs/broker/api-references/accounts/accounts/#tax-id-type

    .. deprecated:: 0.45.0
        Will be replaced by the OpenAPI-generated ``TaxIdType`` once the spec spells
        ``ARG_AR_CUIT`` correctly; it currently has ``ARG_AG_CUIT``.
    """

    USA_SSN = "USA_SSN"
    USA_ITIN = "USA_ITIN"
    ARG_AR_CUIT = "ARG_AR_CUIT"
    AUS_TFN = "AUS_TFN"
    AUS_ABN = "AUS_ABN"
    BOL_NIT = "BOL_NIT"
    BRA_CPF = "BRA_CPF"
    CHL_RUT = "CHL_RUT"
    COL_NIT = "COL_NIT"
    CRI_NITE = "CRI_NITE"
    DEU_TAX_ID = "DEU_TAX_ID"
    DOM_RNC = "DOM_RNC"
    ECU_RUC = "ECU_RUC"
    FRA_SPI = "FRA_SPI"
    GBR_UTR = "GBR_UTR"
    GBR_NINO = "GBR_NINO"
    GTM_NIT = "GTM_NIT"
    HND_RTN = "HND_RTN"
    HUN_TIN = "HUN_TIN"
    IDN_KTP = "IDN_KTP"
    IND_PAN = "IND_PAN"
    ISR_TAX_ID = "ISR_TAX_ID"
    ITA_TAX_ID = "ITA_TAX_ID"
    JPN_TAX_ID = "JPN_TAX_ID"
    MEX_RFC = "MEX_RFC"
    NIC_RUC = "NIC_RUC"
    NLD_TIN = "NLD_TIN"
    PAN_RUC = "PAN_RUC"
    PER_RUC = "PER_RUC"
    PRY_RUC = "PRY_RUC"
    SGP_NRIC = "SGP_NRIC"
    SGP_FIN = "SGP_FIN"
    SGP_ASGD = "SGP_ASGD"
    SGP_ITR = "SGP_ITR"
    SLV_NIT = "SLV_NIT"
    SWE_TAX_ID = "SWE_TAX_ID"
    URY_RUT = "URY_RUT"
    VEN_RIF = "VEN_RIF"
    NATIONAL_ID = "NATIONAL_ID"
    PASSPORT = "PASSPORT"
    PERMANENT_RESIDENT = "PERMANENT_RESIDENT"
    DRIVER_LICENSE = "DRIVER_LICENSE"
    OTHER_GOV_ID = "OTHER_GOV_ID"
    NOT_SPECIFIED = "NOT_SPECIFIED"


_DEPRECATED_TRANSFER_STATUSES = {
    "SETTLED": (
        "TransferStatus.SETTLED is deprecated and will be removed in the next release. "
        "It is no longer a valid transfer status."
    ),
}


@_deprecated(
    "TransferStatus is a temporary compatibility shape and will be replaced by the "
    "OpenAPI-generated TransferStatus in a future release. That enum has no SETTLED "
    "member.",
    category=None,
)
class TransferStatus(
    str,
    Enum,
    metaclass=_DeprecatingEnumMeta,
    deprecations=_DEPRECATED_TRANSFER_STATUSES,
):
    """
    Represents the states a Transfer instance can be in.

    Please see https://alpaca.markets/docs/api-references/broker-api/funding/transfers/#enumtransferstatus for more
    details.

    SETTLED is deprecated and will be removed in the next release. It is no
    longer a valid transfer status.

    .. deprecated:: 0.45.0
        Will be replaced by the OpenAPI-generated ``TransferStatus``, which has no
        ``SETTLED`` member.
    """

    QUEUED = "QUEUED"
    APPROVAL_PENDING = "APPROVAL_PENDING"
    PENDING = "PENDING"
    SENT_TO_CLEARING = "SENT_TO_CLEARING"
    REJECTED = "REJECTED"
    CANCELED = "CANCELED"
    APPROVED = "APPROVED"
    SETTLED = "SETTLED"
    COMPLETE = "COMPLETE"
    RETURNED = "RETURNED"


# Public-only handwritten enums (no generated twin under the same name)


@_deprecated(
    "AccountEntities is deprecated and will be removed in a future version. "
    "Please use `GetAllAccountsEntitiesParameter` instead.",
    stacklevel=2,
)
class AccountEntities(str, Enum):
    """
    An enum representing the different fields to query for when listing accounts.

    ie: asking for CONTACT and IDENTITY will have the api fill those fields when returning the list of Accounts however
    other fields on the account will be nulled out where possible.

    .. deprecated:: 0.45.0
        Please use `GetAllAccountsEntitiesParameter` instead. USER_CONFIGURATIONS is
        TRADING_CONFIGURATIONS there; the wire value is unchanged.
    """

    CONTACT = "contact"
    IDENTITY = "identity"
    DISCLOSURES = "disclosures"
    AGREEMENTS = "agreements"
    DOCUMENTS = "documents"
    TRUSTED_CONTACT = "trusted_contact"
    USER_CONFIGURATIONS = "trading_configurations"


_DEPRECATED_BANK_ACCOUNT_TYPES = {
    "NONE": (
        "BankAccountType.NONE is deprecated and will be removed in the next release. "
        "It is no longer a valid bank account type."
    ),
}


# category=None keeps the class-level deprecation static only: a runtime warning
# would fire for every member, doubling the NONE warning and making CHECKING and
# SAVINGS warn too.
@_deprecated(
    "BankAccountType is deprecated and will be removed in a future version. "
    "Please use `ACHRelationshipBankAccountType` for ACH relationships returned by "
    "the API, or `CreateACHRelationshipRequestBankAccountType` when creating one, "
    "instead. Neither has a NONE member.",
    category=None,
)
class BankAccountType(
    str,
    Enum,
    metaclass=_DeprecatingEnumMeta,
    deprecations=_DEPRECATED_BANK_ACCOUNT_TYPES,
):
    """
    Represents a kind of bank account.

    Please see https://alpaca.markets/docs/api-references/broker-api/funding/ach/#attributes

    NONE is deprecated and will be removed in the next release. It is no
    longer a valid bank account type.

    .. deprecated:: 0.45.0
        Please use `ACHRelationshipBankAccountType` for ACH relationships returned
        by the API, or `CreateACHRelationshipRequestBankAccountType` when creating
        one, instead. Neither has a ``NONE`` member.
    """

    CHECKING = "CHECKING"
    SAVINGS = "SAVINGS"
    # responses from plaid token connections sometimes return empty
    NONE = ""


@_deprecated(
    "CIPApprovalStatus is deprecated and will be removed in a future version. "
    "Please use `CIPKYCApprovalStatus` instead.",
    stacklevel=2,
)
class CIPApprovalStatus(str, Enum):
    """
    Either `approved` or `rejected`

    .. deprecated:: 0.45.0
        Please use `CIPKYCApprovalStatus` instead.
    """

    APPROVED = "approved"
    REJECTED = "rejected"


class CIPProvider(str, Enum):
    """
    Enum representing what CIP provider was used.

    see https://alpaca.markets/docs/api-references/broker-api/accounts/accounts/#cip-provider for more info
    """

    ALLOY = "alloy"
    TRULIOO = "trulioo"
    ONFIDO = "onfido"
    VERIFF = "veriff"
    JUMIO = "jumio"
    GETMATI = "getmati"


class CIPResult(str, Enum):
    """
    see https://alpaca.markets/docs/api-references/broker-api/accounts/accounts/#cip-result for more info
    """

    CLEAR = "clear"
    CONSIDER = "consider"


class CIPStatus(str, Enum):
    """
    An enum representing the status of the CIPInfo

    see https://alpaca.markets/docs/api-references/broker-api/accounts/accounts/#cip-status for more info
    """

    COMPLETE = "complete"
    WITHDRAWN = "withdrawn"


class CalendarSubType(str, Enum):
    """
    The possible values of the Rebalancing Conditions subtype for drift_band.

    See https://docs.alpaca.markets/reference/post-v1-rebalancing-portfolios
    """

    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"


class ClearingBroker(str, Enum):
    """
    An enum for representing what Clearing broker an Account is assigned to
    """

    Apex = "APEX"
    ETC = "ETC"
    IC = "IC"
    Velox = "VELOX"
    Vision = "VISION"
    Self = "SELF"
    Alpaca_APCA = "ALPACA_APCA"


# category=None keeps the deprecation static only. AccountDocument.document_type falls
# back to OwnerDocumentType for values this enum lacks, and Pydantic calls the enum
# class to look those up, so a runtime warning would fire while parsing accounts.
@_deprecated(
    "DocumentType is deprecated and will be removed in a future version. "
    "Please use `OwnerDocumentType` instead. It has no NULL, OTHER or "
    "SOCIAL_SECURITY_NUMBER_VERIFICATION members.",
    category=None,
)
class DocumentType(str, Enum):
    """
    Represents the kind of document data you're uploading

    please see https://alpaca.markets/docs/broker/api-references/accounts/accounts/#document-type
    and https://alpaca.markets/docs/api-references/broker-api/documents/#enumuploaddocumenttype
    for more info

    .. deprecated:: 0.45.0
        Please use `OwnerDocumentType` instead. It has no ``NULL``, ``OTHER`` or
        ``SOCIAL_SECURITY_NUMBER_VERIFICATION`` members.
    """

    IDENTITY_VERIFICATION = "identity_verification"
    ADDRESS_VERIFICATION = "address_verification"
    DATE_OF_BIRTH_VERIFICATION = "date_of_birth_verification"
    TAX_ID_VERIFICATION = "tax_id_verification"
    ACCOUNT_APPROVAL_LETTER = "account_approval_letter"
    LIMITED_TRADING_AUTHORIZATION = "limited_trading_authorization"
    W8BEN = "w8ben"
    SOCIAL_SECURITY_NUMBER_VERIFICATION = "social_security_number_verification"
    NULL = ""
    CIP_RESULT = "cip_result"
    OTHER = "other"


class DriftBandSubType(str, Enum):
    """
    The possible values of the Rebalancing Conditions subtype for drift_band.

    See https://docs.alpaca.markets/reference/post-v1-rebalancing-portfolios
    """

    ABSOLUTE = "absolute"
    RELATIVE = "relative"


@_deprecated(
    "EmploymentStatus is deprecated and will be removed in a future version. "
    "Please use `DisclosuresEmploymentStatus` instead. Its values are lowercase "
    "(employed) while this enum's are uppercase (EMPLOYED), so check that the API "
    "accepts them before switching.",
    stacklevel=2,
)
class EmploymentStatus(str, Enum):
    """
    The possible employment statuses of the user

    see https://alpaca.markets/docs/broker/api-references/accounts/accounts/#employment-status

    .. deprecated:: 0.45.0
        Please use `DisclosuresEmploymentStatus` instead. Its values are lowercase
        (``employed``) while this enum's are uppercase (``EMPLOYED``), so check that
        the API accepts them before switching.
    """

    UNEMPLOYED = "UNEMPLOYED"
    EMPLOYED = "EMPLOYED"
    STUDENT = "STUDENT"
    RETIRED = "RETIRED"


class FeePaymentMethod(str, Enum):
    """
    Represents who is responsible for paying fees associated with the transfer.

    Please see https://alpaca.markets/docs/api-references/broker-api/funding/transfers/#enumfeepaymentmethod for more
    details.
    """

    USER = "user"
    INVOICE = "invoice"


@_deprecated(
    "FundingSource is deprecated and will be removed in a future version. "
    "Please use `IdentityFundingSourceInner` instead.",
    stacklevel=2,
)
class FundingSource(str, Enum):
    """
    Various sources of funding for brokerage accounts.

    see https://alpaca.markets/docs/broker/api-references/accounts/accounts/#funding-source

    .. deprecated:: 0.45.0
        Please use `IdentityFundingSourceInner` instead.
    """

    EMPLOYMENT_INCOME = "employment_income"
    INVESTMENTS = "investments"
    INHERITANCE = "inheritance"
    BUSINESS_INCOME = "business_income"
    SAVINGS = "savings"
    FAMILY = "family"


@_deprecated(
    "IdentifierType is deprecated and will be removed in a future version. "
    "Please use `BankBankCodeType` instead.",
    stacklevel=2,
)
class IdentifierType(str, Enum):
    """
    Represents a type of bank account.

    Please see https://alpaca.markets/docs/api-references/broker-api/funding/bank/#creating-a-new-bank-relationship for
    more details.

    .. deprecated:: 0.45.0
        Please use `BankBankCodeType` instead.
    """

    ABA = "ABA"
    BIC = "BIC"


class RebalancingConditionsType(str, Enum):
    """
    The possible values of the Rebalancing Conditions type.

    See https://docs.alpaca.markets/reference/post-v1-rebalancing-portfolios
    """

    DRIFT_BAND = "drift_band"
    CALENDAR = "calendar"


@_deprecated(
    "RunInitiatedFrom is deprecated and will be removed in a future version. "
    "Please use `PortfolioRunInitiatedFrom` instead.",
    stacklevel=2,
)
class RunInitiatedFrom(str, Enum):
    """
    The possible values of the initiated_from field.

    See https://alpaca.markets/docs/docs/portfolio-rebalancing

    .. deprecated:: 0.45.0
        Please use `PortfolioRunInitiatedFrom` instead.
    """

    SYSTEM = "system"
    API = "api"


@_deprecated(
    "RunStatus is deprecated and will be removed in a future version. "
    "Please use `PortfolioRunStatus` instead.",
    stacklevel=2,
)
class RunStatus(str, Enum):
    """
    The possible values of the Run status.

    See https://docs.alpaca.markets/reference/get-v1-rebalancing-runs

    .. deprecated:: 0.45.0
        Please use `PortfolioRunStatus` instead.
    """

    QUEUED = "QUEUED"
    IN_PROGRESS = "IN_PROGRESS"
    CANCELED = "CANCELED"
    CANCELED_MID_RUN = "CANCELED_MID_RUN"
    ERROR = "ERROR"
    TIMEOUT = "TIMEOUT"
    COMPLETED_SUCCESS = "COMPLETED_SUCCESS"
    COMPLETED_ADJUSTED = "COMPLETED_ADJUSTED"


@_deprecated(
    "RunType is deprecated and will be removed in a future version. "
    "Please use `PortfolioRunType` instead.",
    stacklevel=2,
)
class RunType(str, Enum):
    """
    The possible values of the Run type.

    See https://docs.alpaca.markets/reference/post-v1-rebalancing-runs

    .. deprecated:: 0.45.0
        Please use `PortfolioRunType` instead.
    """

    FULL_REBALANCE = "full_rebalance"
    INVEST_CASH = "invest_cash"


class TradeDocumentSubType(str, Enum):
    """
    Represents additional information for whats inside a TradeDocument in combination with a TradeDocumentType

    please see https://alpaca.markets/docs/api-references/broker-api/documents/#the-document-object for more info
    """

    TYPE_1099_COMP = "1099-Comp"
    TYPE_1042_S = "1042-S"
    TYPE_480_6 = "480.6"
    COURTESY_STATEMENT = "courtesy_statement"


# category=None keeps the deprecation static only. TradeDocument.type falls back to
# AccountDocumentType for values this enum lacks, and Pydantic calls the enum class
# to look those up, so a runtime warning would fire while parsing API responses.
@_deprecated(
    "TradeDocumentType is deprecated and will be removed in a future version. "
    "Please use `AccountDocumentType` for documents returned by the API, or "
    "`GetDocsForAccountTypeParameter` to filter them, instead. Neither has the "
    "legacy TAX_1099_* and TAX_W8 members.",
    category=None,
)
class TradeDocumentType(str, Enum):
    """
    Represents what kind information is inside a TradeDocument

    Most likely will be either of these 3:
      -  ACCOUNT_STATEMENT
      -  TRADE_CONFIRMATION
      -  TAX_STATEMENT

    However, for older accounts with legacy documents the other legacy values might show up.

    please see https://alpaca.markets/docs/api-references/broker-api/documents/#enumdocumenttype for more info

    .. deprecated:: 0.45.0
        Please use `AccountDocumentType` for documents returned by the API, or
        `GetDocsForAccountTypeParameter` to filter them, instead. Neither has the
        legacy ``TAX_1099_*`` and ``TAX_W8`` members.
    """

    ACCOUNT_STATEMENT = "account_statement"
    TRADE_CONFIRMATION = "trade_confirmation"
    TRADE_CONFIRMATION_JSON = "trade_confirmation_json"

    TAX_STATEMENT = "tax_statement"

    ACCOUNT_APPLICATION = "account_application"

    # Legacy Values
    TAX_1099_B_DETAILS = "tax_1099_b_details"
    TAX_1099_B_FORM = "tax_1099_b_form"
    TAX_1099_DIV_DETAILS = "tax_1099_div_details"
    TAX_1099_DIV_FORM = "tax_1099_div_form"
    TAX_1099_INT_DETAILS = "tax_1099_int_details"
    TAX_1099_INT_FORM = "tax_1099_int_form"
    TAX_W8 = "tax_w8"


class UploadDocumentMimeType(str, Enum):
    """
    specifies the mime type of the base64 data you're uploading as part of a UploadDocumentRequest

    please see https://alpaca.markets/docs/api-references/broker-api/documents/#parameters for more info
    """

    PDF = "application/pdf"
    PNG = "image/png"
    JPEG = "image/jpeg"
    JSON = "application/json"


class UploadDocumentSubType(str, Enum):
    """
    Represents a sub type for an UploadDocumentRequest

    please see: https://alpaca.markets/docs/api-references/broker-api/documents/#enumuploaddocumentsubtype
    for more info
    """

    ACCOUNT_APPLICATION = "Account Application"
    FORM_W8_BEN = "Form W-8BEN"
    PASSPORT = "passport"


class VisaType(str, Enum):
    """
    In addition to the following USA visa categories, we accept any sub visas of the list below.
    Sub visas must be passed in according to their parent category.
    Note that United States green card holders are considered permanent residents and should not pass in a visa type.

    Please feel free to reach out to Alpaca if you need other tax ID types.

    see https://alpaca.markets/docs/broker/api-references/accounts/accounts/#visa-type
    """

    B1 = "B1"
    B2 = "B2"
    DACA = "DACA"
    E1 = "E1"
    E2 = "E2"
    E3 = "E3"
    F1 = "F1"
    G4 = "G4"
    H1B = "H1B"
    J1 = "J1"
    L1 = "L1"
    Other = "OTHER"
    O1 = "O1"
    TN1 = "TN1"


@_deprecated(
    "WeightType is deprecated and will be removed in a future version. "
    "Please use `PortfolioWeightRequestType` instead.",
    stacklevel=2,
)
class WeightType(str, Enum):
    """
    The possible values of the Weight type.

    See https://docs.alpaca.markets/reference/post-v1-rebalancing-portfolios

    .. deprecated:: 0.45.0
        Please use `PortfolioWeightRequestType` instead.
    """

    CASH = "cash"
    ASSET = "asset"


@_deprecated(
    "RecipientBankStatus is deprecated and will be removed in a future version. "
    "Please use `GetRecipientBanksStatusParameter` instead.",
    stacklevel=2,
)
class RecipientBankStatus(str, Enum):
    """
    Filter for listing recipient banks.

    This is the ``status`` query on ``GET /v1/accounts/{account_id}/recipient_banks``.
    It is separate from ``BankStatus``, which is the lifecycle state returned on a bank.

    .. deprecated:: 0.45.0
        Please use `GetRecipientBanksStatusParameter` instead.
    """

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
