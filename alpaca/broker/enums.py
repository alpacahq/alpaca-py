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
    Other = "Other"
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

    UNEMPLOYED = "unemployed"
    EMPLOYED = "employed"
    STUDENT = "student"
    RETIRED = "retired"


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
    The types of documents that can be uploaded by the user

    see https://alpaca.markets/docs/broker/api-references/accounts/accounts/#document-type
    """

    IDENTITY_VERIFICATION = "identity_verification"
    ADDRESS_VERIFICATION = "address_verification"
    DATE_OF_BIRTH_VERIFICATION = "date_of_birth_verification"
    TAX_ID_VERIFICATION = "tax_id_verification"
    ACCOUNT_APPROVAL_LETTER = "account_approval_letter"
    W8_BEN = "w8ben"


class AccountStatus(str, Enum):
    """
    The various statuses each brokerage account can take during its lifetime

    see https://alpaca.markets/docs/broker/api-references/accounts/accounts/#account-status
    """

    ACCOUNT_CLOSED = "ACCOUNT_CLOSED"
    ACCOUNT_UPDATED = "ACCOUNT_UPDATED"
    ACTION_REQUIRED = "ACTION_REQUIRED"
    ACTIVE = "ACTIVE"
    AML_REVIEW = "AML_REVIEW"
    APPROVAL_PENDING = "APPROVAL_PENDING"
    APPROVED = "APPROVED"
    DISABLED = "DISABLED"
    DISABLE_PENDING = "DISABLE_PENDING"
    EDITED = "EDITED"
    INACTIVE = "INACTIVE"
    KYC_SUBMITTED = "KYC_SUBMITTED"
    LIMITED = "LIMITED"
    ONBOARDING = "ONBOARDING"
    PAPER_ONLY = "PAPER_ONLY"
    REAPPROVAL_PENDING = "REAPPROVAL_PENDING"
    REJECTED = "REJECTED"
    RESUBMITTED = "RESUBMITTED"
    SIGNED_UP = "SIGNED_UP"
    SUBMISSION_FAILED = "SUBMISSION_FAILED"
    SUBMITTED = "SUBMITTED"


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
