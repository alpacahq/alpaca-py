from enum import Enum


class TaxIdType(str, Enum):
    """The various country specific tax identification numbers

    see https://alpaca.markets/docs/broker/api-references/accounts/accounts/#tax-id-type
    """

    USA_SSN = "USA_SSN"
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
    NOT_SPECIFIED = "NOT_SPECIFIED"


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


class FundingSource(str, Enum):
    """
    Various sources of funding for brokerage accounts.

    see https://alpaca.markets/docs/broker/api-references/accounts/accounts/#funding-source
    """

    EMPLOYMENT_INCOME = "employment_income"
    INVESTMENTS = "investments"
    INHERITANCE = "inheritance"
    BUSINESS_INCOME = "business_income"
    SAVINGS = "savings"
    FAMILY = "family"


class EmploymentStatus(str, Enum):
    """
    The possible employment statuses of the user

    see https://alpaca.markets/docs/broker/api-references/accounts/accounts/#employment-status
    """

    UNEMPLOYED = "UNEMPLOYED"
    EMPLOYED = "EMPLOYED"
    STUDENT = "STUDENT"
    RETIRED = "RETIRED"


class AgreementType(str, Enum):
    """
    The types of agreements that are to be signed by the user

    see https://alpaca.markets/docs/broker/api-references/accounts/accounts/#agreements
    """

    MARGIN = "margin_agreement"
    ACCOUNT = "account_agreement"
    CUSTOMER = "customer_agreement"
    CRYPTO = "crypto_agreement"


class DocumentType(str, Enum):
    """
    Represents the kind of document data you're uploading

    please see https://alpaca.markets/docs/broker/api-references/accounts/accounts/#document-type
    and https://alpaca.markets/docs/api-references/broker-api/documents/#enumuploaddocumenttype
    for more info
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


class AccountEntities(str, Enum):
    """
    An enum representing the different fields to query for when listing accounts.

    ie: asking for CONTACT and IDENTITY will have the api fill those fields when returning the list of Accounts however
    other fields on the account will be nulled out where possible.
    """

    CONTACT = "contact"
    IDENTITY = "identity"
    DISCLOSURES = "disclosures"
    AGREEMENTS = "agreements"
    DOCUMENTS = "documents"
    TRUSTED_CONTACT = "trusted_contact"
    USER_CONFIGURATIONS = "trading_configurations"


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


class CIPStatus(str, Enum):
    """
    An enum representing the status of the CIPInfo

    see https://alpaca.markets/docs/api-references/broker-api/accounts/accounts/#cip-status for more info
    """

    COMPLETE = "complete"
    WITHDRAWN = "withdrawn"


class CIPResult(str, Enum):
    """
    see https://alpaca.markets/docs/api-references/broker-api/accounts/accounts/#cip-result for more info
    """

    CLEAR = "clear"
    CONSIDER = "consider"


class CIPApprovalStatus(str, Enum):
    """
    Either `approved` or `rejected`
    """

    APPROVED = "approved"
    REJECTED = "rejected"


class TradeDocumentType(str, Enum):
    """
    Represents what kind information is inside a TradeDocument

    Most likely will be either of these 3:
      -  ACCOUNT_STATEMENT
      -  TRADE_CONFIRMATION
      -  TAX_STATEMENT

    However, for older accounts with legacy documents the other legacy values might show up.

    please see https://alpaca.markets/docs/api-references/broker-api/documents/#enumdocumenttype for more info
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


class TradeDocumentSubType(str, Enum):
    """
    Represents additional information for whats inside a TradeDocument in combination with a TradeDocumentType

    please see https://alpaca.markets/docs/api-references/broker-api/documents/#the-document-object for more info
    """

    TYPE_1099_COMP = "1099-Comp"
    TYPE_1042_S = "1042-S"
    TYPE_480_6 = "480.6"
    COURTESY_STATEMENT = "courtesy_statement"


class UploadDocumentSubType(str, Enum):
    """
    Represents a sub type for an UploadDocumentRequest

    please see: https://alpaca.markets/docs/api-references/broker-api/documents/#enumuploaddocumentsubtype
    for more info
    """

    ACCOUNT_APPLICATION = "Account Application"
    FORM_W8_BEN = "Form W-8BEN"
    PASSPORT = "passport"


class UploadDocumentMimeType(str, Enum):
    """
    specifies the mime type of the base64 data you're uploading as part of a UploadDocumentRequest

    please see https://alpaca.markets/docs/api-references/broker-api/documents/#parameters for more info
    """

    PDF = "application/pdf"
    PNG = "image/png"
    JPEG = "image/jpeg"
    JSON = "application/json"


class ACHRelationshipStatus(str, Enum):
    """
    Represents the state that an ACHRelationship is in.

    Please see https://alpaca.markets/docs/api-references/broker-api/funding/ach/#attributes for more details
    """

    QUEUED = "QUEUED"
    APPROVED = "APPROVED"
    PENDING = "PENDING"


class BankAccountType(str, Enum):
    """
    Represents a kind of bank account.

    Please see https://alpaca.markets/docs/api-references/broker-api/funding/ach/#attributes
    """

    CHECKING = "CHECKING"
    SAVINGS = "SAVINGS"
    # responses from plaid token connections sometimes return empty
    NONE = ""


class IdentifierType(str, Enum):
    """
    Represents a type of bank account.

    Please see https://alpaca.markets/docs/api-references/broker-api/funding/bank/#creating-a-new-bank-relationship for
    more details.
    """

    ABA = "ABA"
    BIC = "BIC"


class BankStatus(str, Enum):
    """
    Represents the states a Bank instance can be in.

    Please see https://alpaca.markets/docs/api-references/broker-api/funding/bank/#enumbankstatus for more details.
    """

    QUEUED = "QUEUED"
    SENT_TO_CLEARING = "SENT_TO_CLEARING"
    APPROVED = "APPROVED"
    CANCELED = "CANCELED"


class TransferType(str, Enum):
    """
    Represents the types of transfers that can be made.

    Please see https://alpaca.markets/docs/api-references/broker-api/funding/transfers/#enumtransfertype for more
    details.
    """

    ACH = "ach"
    WIRE = "wire"


class TransferStatus(str, Enum):
    """
    Represents the states a Transfer instance can be in.

    Please see https://alpaca.markets/docs/api-references/broker-api/funding/transfers/#enumtransferstatus for more
    details.
    """

    QUEUED = "QUEUED"
    APPROVAL_PENDING = "APPROVAL_PENDING"
    PENDING = "PENDING"
    SENT_TO_CLEARING = "SENT_TO_CLEARING"
    REJECTED = "REJECTED"
    CANCELED = "CANCELED"
    APPROVED = "APPROVED"
    COMPLETE = "COMPLETE"
    RETURNED = "RETURNED"


class TransferDirection(str, Enum):
    """
    Represents the direction of the transfer.

    Please see https://alpaca.markets/docs/api-references/broker-api/funding/transfers/#enumtransferdirection for more
    details.
    """

    INCOMING = "INCOMING"
    OUTGOING = "OUTGOING"


class TransferTiming(str, Enum):
    """
    Represents the timing of a transfer.

    Please see https://alpaca.markets/docs/api-references/broker-api/funding/transfers/#creating-a-transfer-entity for
    more details.
    """

    IMMEDIATE = "immediate"


class FeePaymentMethod(str, Enum):
    """
    Represents who is responsible for paying fees associated with the transfer.

    Please see https://alpaca.markets/docs/api-references/broker-api/funding/transfers/#enumfeepaymentmethod for more
    details.
    """

    USER = "user"
    INVOICE = "invoice"


class JournalEntryType(str, Enum):
    """
    Represents the types of journals. Cash journals are transfers of cash.
    Security journals are transfers of securities like stocks.

    Please see https://alpaca.markets/docs/api-references/broker-api/journals/ for more details.
    """

    CASH = "JNLC"
    SECURITY = "JNLS"


class JournalStatus(str, Enum):
    """
    The various states a journal can be in during its lifecycle.

    Please see https://alpaca.markets/docs/api-references/broker-api/journals/#enumjournalstatus for more details.
    """

    QUEUED = "queued"
    SENT_TO_CLEARING = "sent_to_clearing"
    PENDING = "pending"
    EXECUTED = "executed"
    REJECTED = "rejected"
    CANCELED = "canceled"
    REFUSED = "refused"
    CORRECT = "correct"
    DELETED = "deleted"
