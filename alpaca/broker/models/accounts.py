from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import (
    BeforeValidator,
    PlainSerializer,
    TypeAdapter,
    ValidationInfo,
    field_validator,
    model_validator,
)

from alpaca._deprecating_enum import _warn_at_user_code

from alpaca.broker.enums import (
    AccountSubType,
    AccountType,
    AgreementType,
    ClearingBroker,
    EmploymentStatus,
    FundingSource,
    TaxIdType,
    VisaType,
)
from alpaca.broker.models.documents import AccountDocument
from alpaca.common.models import ModelWithID
from alpaca.common.models import ValidateBaseModel as BaseModel
from alpaca.trading.enums import AccountStatus, AssetClass, TradeConfirmationEmail
from alpaca.trading.models import TradeAccount as BaseTradeAccount

# Present while an account payload is parsed from the API.
_TRUSTED_CONTACT_RESPONSE_KEY = "trusted_contact_from_response"


def _validate_trusted_street_address(
    value: Any, info: ValidationInfo
) -> Optional[Union[str, List[str]]]:
    """Accept a string or a list and preserve the value that was supplied.

    The Broker API schema is an array of strings. A list is stored unchanged.
    A string remains a string so existing readers keep working; building a
    request with a string warns. Parsing an account response stays silent.
    """
    if isinstance(value, str):
        context = info.context
        from_response = (
            isinstance(context, dict)
            and context.get(_TRUSTED_CONTACT_RESPONSE_KEY) is True
        )
        if not from_response:
            _warn_at_user_code(
                "Passing street_address as a str is deprecated and will be removed "
                "in the next release. Pass a list of strings."
            )
        return value
    if value is None or (
        isinstance(value, list) and all(isinstance(item, str) for item in value)
    ):
        return value
    raise ValueError("street_address must be a string or a list of strings")


def _serialize_trusted_street_address(
    value: Optional[Union[str, List[str]]],
) -> Optional[List[str]]:
    """Send the Broker API array shape. A stored string becomes one address line."""
    if isinstance(value, str):
        return [value]
    return value


class _TrustedStreetAddressSchema:
    """Accept a string or a list without changing the public field annotation.

    The string alternative is deprecated. The Broker API type is an array of
    strings, which is the form callers should pass.
    """

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: Any) -> Any:
        return handler.generate_schema(Union[str, List[str], None])

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema: Any, handler: Any) -> dict:
        schema = handler(core_schema)
        for variant in schema.get("anyOf", []):
            if variant.get("type") == "string":
                variant["deprecated"] = True
        return schema


# The published annotation stays Optional[str]. A string is stored as a string.
# A list is accepted and stored as a list. Serialization always publishes the
# Broker API array.
_TrustedStreetAddress = Annotated[
    Optional[str],
    _TrustedStreetAddressSchema,
    BeforeValidator(_validate_trusted_street_address),
    PlainSerializer(_serialize_trusted_street_address, return_type=Optional[List[str]]),
]


class KycResults(BaseModel):
    """
    Hold information about the result of KYC.
    ref. https://docs.alpaca.markets/reference/getaccount

    Attributes:
        reject (Optional[Dict[str, Any]]): The reason for the rejection
        accept (Optional[Dict[str, Any]]): The reason for the acceptance
        indeterminate (Optional[Dict[str, Any]]): The reason for the indeterminate result
        additional_information (Optional[str]): Used to display a custom message
        summary (Optional[str]): Either pass or fail. Used to indicate if KYC has completed and passed or not.
    """

    reject: Optional[Dict[str, Any]] = None
    accept: Optional[Dict[str, Any]] = None
    indeterminate: Optional[Dict[str, Any]] = None
    additional_information: Optional[str] = None
    summary: Optional[str] = None


class Contact(BaseModel):
    """User contact details within Account Model

    see https://alpaca.markets/docs/broker/api-references/accounts/accounts/#the-account-model

    Attributes:
        email_address (str): The user's email address
        phone_number (str): The user's phone number. It should include the country code.
        street_address (List[str]): The user's street address lines.
        unit (Optional[str]): The user's apartment unit, if any.
        city (str): The city the user resides in.
        state (Optional[str]): The state the user resides in. This is required if country is 'USA'.
        postal_code (str): The user's postal
        country (str): The country the user resides in. 3 letter country code is permissible.
    """

    email_address: str
    phone_number: Optional[str] = None
    street_address: List[str]
    unit: Optional[str] = None
    city: str
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None

    @field_validator("state")
    def usa_state_has_value(cls, v: str, validation: ValidationInfo, **kwargs) -> str:
        """Validates that the state has a value if the country is USA

        Args:
            v (str): The state field's value
            values (dict): The values of each field

        Raises:
            ValueError: State is required for country USA

        Returns:
            str: The value of the state field
        """
        values: dict = validation.data
        if "country" in values and values["country"] == "USA" and v is None:
            raise ValueError("State is required for country USA.")
        return v


class Identity(BaseModel):
    """User identity details within Account Model

    see https://alpaca.markets/docs/broker/api-references/accounts/accounts/#the-account-model

    Attributes:
        given_name (str): The user's first name
        middle_name (Optional[str]): The user's middle name, if any
        family_name (str): The user's last name
        date_of_birth (str): The user's date of birth
        tax_id (Optional[str]): The user's country specific tax id, required if tax_id_type is provided
        tax_id_type (Optional[TaxIdType]): The tax_id_type for the tax_id provided, required if tax_id provided
        country_of_citizenship (Optional[str]): The country the user is a citizen
        country_of_birth (Optional[str]): The country the user was born
        country_of_tax_residence (str): The country the user files taxes
        visa_type (Optional[VisaType]): Only used to collect visa types for users residing in the USA.
        visa_expiration_date (Optional[str]): The date of expiration for visa, Required if visa_type is set.
        date_of_departure_from_usa (Optional[str]): Required if visa_type = B1 or B2
        permanent_resident (Optional[bool]): Only used to collect permanent residence status in the USA.
        funding_source (Optional[List[FundingSource]]): How the user will fund their account
        annual_income_min (Optional[float]): The minimum of the user's income range
        annual_income_max (Optional[float]): The maximum of the user's income range
        liquid_net_worth_min (Optional[float]): The minimum of the user's liquid net worth range
        liquid_net_worth_max (Optional[float]): The maximum of the user's liquid net worth range
        total_net_worth_min (Optional[float]): The minimum of the user's total net worth range
        total_net_worth_max (Optional[float]): The maximum of the user's total net worth range
    """

    given_name: str
    middle_name: Optional[str] = None
    family_name: str
    date_of_birth: Optional[str] = None
    tax_id: Optional[str] = None
    tax_id_type: Optional[TaxIdType] = None
    country_of_citizenship: Optional[str] = None
    country_of_birth: Optional[str] = None
    country_of_tax_residence: str
    visa_type: Optional[VisaType] = None
    visa_expiration_date: Optional[str] = None
    date_of_departure_from_usa: Optional[str] = None
    permanent_resident: Optional[bool] = None
    funding_source: Optional[List[FundingSource]] = None
    annual_income_min: Optional[float] = None
    annual_income_max: Optional[float] = None
    liquid_net_worth_min: Optional[float] = None
    liquid_net_worth_max: Optional[float] = None
    total_net_worth_min: Optional[float] = None
    total_net_worth_max: Optional[float] = None


class Disclosures(BaseModel):
    """User disclosures within Account Model

    see https://alpaca.markets/docs/broker/api-references/accounts/accounts/#the-account-model

    Attributes:
        is_control_person (bool): Whether user holds a controlling position in a publicly traded company
        is_affiliated_exchange_or_finra (bool): If user is affiliated with any exchanges or FINRA
        is_politically_exposed (bool): If user is politically exposed
        immediate_family_exposed (bool): If user’s immediate family member is either politically exposed or holds a control position.
        employment_status (EmploymentStatus): The employment status of the user
        employer_name (str): The user's employer's name, if any
        employer_address (str): The user's employer's address, if any
        employment_position (str): The user's employment position, if any
    """

    is_control_person: Optional[bool] = None
    is_affiliated_exchange_or_finra: Optional[bool] = None
    is_politically_exposed: Optional[bool] = None
    immediate_family_exposed: bool
    employment_status: Optional[EmploymentStatus] = None
    employer_name: Optional[str] = None
    employer_address: Optional[str] = None
    employment_position: Optional[str] = None


class AccountDisclosures(Disclosures):
    """
    Disclosures parsed for ``GET /v1/accounts/{account_id}``.

    ``is_discretionary`` appears on that response. It is not part of the
    Disclosures schema used when creating or updating an account, so
    ``Account.disclosures`` stays ``Disclosures``.
    """

    is_discretionary: Optional[bool] = None


class Agreement(BaseModel):
    """User agreements signed within Account Model

    see https://alpaca.markets/docs/broker/api-references/accounts/accounts/#the-account-model

    Attributes:
        agreement (Agreement): The type of agreement signed by the user
        signed_at (str): The timestamp the agreement was signed
        ip_address (str): The ip_address the signed agreements were sent from by the user
        revision (str): The revision date
    """

    agreement: AgreementType
    signed_at: str
    ip_address: str
    revision: Optional[str] = None


class TrustedContact(BaseModel):
    """User's trusted contact details within Account Model

    see https://alpaca.markets/docs/broker/api-references/accounts/accounts/#the-account-model

    Attributes:given_name
        given_name (str): The first name of the user's trusted contact
        family_name (str): The last name of the user's trusted contact
        email_address (Optional[str]): The email address of the user's trusted contact
        phone_number (Optional[str]): The email address of the user's trusted contact
        city (Optional[str]): The email address of the user's trusted contact
        state (Optional[str]): The email address of the user's trusted contact
        postal_code (Optional[str]): The email address of the user's trusted contact
        country (Optional[str]): The email address of the user's trusted contact
        street_address (Optional[str]): Street address. The Broker API uses an array of strings. Pass a list to store and send those lines. A string still works and is stored as a string, but it is deprecated and will be removed in the next release; it is sent as a one-item list.
    """

    given_name: str
    family_name: str
    email_address: Optional[str] = None
    phone_number: Optional[str] = None
    street_address: _TrustedStreetAddress = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None

    @model_validator(mode="before")
    def root_validator(cls, values: dict) -> dict:
        has_phone_number = (
            "phone_number" in values and values["phone_number"] is not None
        )
        has_street_address = (
            "street_address" in values and values["street_address"] is not None
        )
        has_email_address = (
            "email_address" in values and values["email_address"] is not None
        )

        if has_phone_number or has_street_address or has_email_address:
            return values

        raise ValueError("At least one method of contact required for trusted contact")


class MinorIdentity(BaseModel):
    """
    Identity of the minor on a custodial account.

    Required when creating an account with ``account_type=custodial``.

    Attributes:
        given_name (str): The minor's first name.
        family_name (str): The minor's last name.
        date_of_birth (str): Date of birth in ``YYYY-MM-DD`` format.
        tax_id_type (TaxIdType): The tax identifier type.
        country_of_tax_residence (str): ISO 3166-1 alpha-3 country code.
        state (str): State or province of the minor.
        email (str): Email address of the minor.
        country_of_birth (Optional[str]): ISO 3166-1 alpha-3 country of birth.
        country_of_citizenship (Optional[str]): ISO 3166-1 alpha-3 citizenship.
        tax_id (Optional[str]): The minor's tax identifier.
    """

    given_name: str
    family_name: str
    date_of_birth: str
    tax_id_type: TaxIdType
    country_of_tax_residence: str
    state: str
    email: str
    country_of_birth: Optional[str] = None
    country_of_citizenship: Optional[str] = None
    tax_id: Optional[str] = None


class Beneficiary(BaseModel):
    """
    A beneficiary of an account. Used for IRA accounts.

    Attributes:
        given_name (str): Beneficiary given name.
        middle_name (str): Beneficiary middle name.
        family_name (str): Beneficiary family name.
        date_of_birth (str): Date of birth.
        tax_id (str): Tax identifier.
        tax_id_type (str): Tax identifier type.
        relationship (str): Relationship to the account holder.
        type (str): Beneficiary type, such as ``primary``.
        share_pct (str): Share of the account allocated to this beneficiary.
    """

    given_name: str
    middle_name: Optional[str] = None
    family_name: str
    date_of_birth: str
    tax_id: str
    tax_id_type: str
    relationship: str
    type: str
    share_pct: str


class CashInterestProgram(BaseModel):
    """
    USD cash interest program enrollment.

    Attributes:
        apr_tier_name (Optional[str]): Name of the APR tier.
        status (Optional[str]): Enrollment status, such as ``ACTIVE`` or ``INACTIVE``.
    """

    apr_tier_name: Optional[str] = None
    status: Optional[str] = None


class CashInterest(BaseModel):
    """
    Cash interest configuration keyed by currency.

    Attributes:
        USD (Optional[CashInterestProgram]): The USD cash interest program.
    """

    USD: Optional[CashInterestProgram] = None


class FPSLMarket(BaseModel):
    """
    Fully Paid Securities Lending configuration for one market.

    Attributes:
        status (Optional[str]): Enrollment status, such as ``ACTIVE`` or ``INACTIVE``.
        tier_id (Optional[str]): FPSL tier id.
    """

    status: Optional[str] = None
    tier_id: Optional[str] = None


class FPSL(BaseModel):
    """
    Fully Paid Securities Lending configuration.

    Attributes:
        US (Optional[FPSLMarket]): Configuration for the US market.
    """

    US: Optional[FPSLMarket] = None


class AccountUSD(BaseModel):
    """
    USD-denominated values returned for local-currency accounts.

    Attributes:
        last_equity (Optional[str]): End-of-day equity in USD.
    """

    last_equity: Optional[str] = None


class AccountTradingConfigurations(BaseModel):
    """
    Trading configuration returned on an extended account.

    Attributes:
        disable_overnight_trading (Optional[bool]): When true, overnight trading is disabled.
        fractional_trading (Optional[bool]): When true, fractional trading is enabled.
        max_margin_multiplier (Optional[str]): ``"1"`` or ``"2"``.
        max_options_trading_level (Optional[int]): Maximum options trading level, 0 through 3.
        no_shorting (Optional[bool]): When true, the account is long-only.
        ptp_no_exception_entry (Optional[bool]): When true, PTP symbols with no exception are accepted.
        suspend_trade (Optional[bool]): When true, new orders are blocked.
        trade_confirm_email (Optional[TradeConfirmationEmail]): ``all`` or ``none``.
    """

    disable_overnight_trading: Optional[bool] = None
    fractional_trading: Optional[bool] = None
    max_margin_multiplier: Optional[str] = None
    max_options_trading_level: Optional[int] = None
    no_shorting: Optional[bool] = None
    ptp_no_exception_entry: Optional[bool] = None
    suspend_trade: Optional[bool] = None
    trade_confirm_email: Optional[TradeConfirmationEmail] = None


class Account(ModelWithID):
    """Contains information pertaining to a specific brokerage account

    see https://alpaca.markets/docs/broker/api-references/accounts/accounts/#the-account-model

    The fields contact, identity, disclosures, agreements, documents, trusted_contact, and trading_configurations
    are all optional and won't always be provided by the api depending on what endpoint you use and what options you
    pass

    Attributes:
        id (str): The account uuid used to reference this account
        account_number (str): A more human friendly identifier for this account
        account_type (Optional[Union[AccountType, str]]): The type of account
        account_sub_type (Optional[Union[AccountSubType, str]]): The sub type of account
        status (AccountStatus): The approval status of this account
        crypto_status (Optional[AccountStatus]): The crypto trading status. Only present if crypto trading is enabled.
        kyc_results (Optional[KycResult]): Hold information about the result of KYC.
        currency (str): The currency the account's values are returned in
        last_equity (str): The total equity value stored in the account
        created_at (str): The timestamp when the account was created
        contact (Optional[Contact]): The contact details for the account holder
        identity (Optional[Identity]): The identity details for the account holder
        disclosures (Optional[Disclosures]): The account holder's political disclosures
        agreements (Optional[List[Agreement]]): The agreements the account holder has signed
        documents (Optional[List[AccountDocument]]): The documents the account holder has submitted
        trusted_contact (Optional[TrustedContact]): The account holder's trusted contact details
    """

    account_number: str
    account_type: Optional[Union[AccountType, str]] = None
    account_sub_type: Optional[Union[AccountSubType, str]] = None
    status: AccountStatus
    crypto_status: Optional[AccountStatus] = None
    kyc_results: Optional[KycResults] = None
    currency: str
    last_equity: str
    created_at: str
    contact: Optional[Contact] = None
    identity: Optional[Identity] = None
    disclosures: Optional[Disclosures] = None
    agreements: Optional[List[Agreement]] = None
    documents: Optional[List[AccountDocument]] = None
    trusted_contact: Optional[TrustedContact] = None

    def __init__(self, **response):
        super().__init__(
            id=(UUID(response["id"])),
            account_number=(response["account_number"]),
            account_type=response.get("account_type", None),
            account_sub_type=response.get("account_sub_type", None),
            status=(response["status"]),
            crypto_status=(
                response["crypto_status"] if "crypto_status" in response else None
            ),
            kyc_results=(
                TypeAdapter(KycResults).validate_python(response["kyc_results"])
                if "kyc_results" in response and response["kyc_results"] is not None
                else None
            ),
            currency=(response["currency"]),
            last_equity=(response["last_equity"]),
            created_at=(response["created_at"]),
            contact=(
                TypeAdapter(Contact).validate_python(response["contact"])
                if "contact" in response
                else None
            ),
            identity=(
                TypeAdapter(Identity).validate_python(response["identity"])
                if "identity" in response
                else None
            ),
            disclosures=(
                TypeAdapter(Disclosures).validate_python(response["disclosures"])
                if "disclosures" in response
                else None
            ),
            agreements=(
                TypeAdapter(List[Agreement]).validate_python(response["agreements"])
                if "agreements" in response
                else None
            ),
            documents=(
                TypeAdapter(List[AccountDocument]).validate_python(
                    response["documents"]
                )
                if "documents" in response
                else None
            ),
            trusted_contact=(
                TypeAdapter(TrustedContact).validate_python(
                    response["trusted_contact"],
                    context={_TRUSTED_CONTACT_RESPONSE_KEY: True},
                )
                if "trusted_contact" in response
                else None
            ),
        )


class AccountExtended(Account):
    """
    Account returned by the account list, account update, and ``GET /v1/accounts/{account_id}``.

    The Broker API documents this payload as AccountExtended. It includes the
    fields on ``Account`` plus the optional extended attributes below.

    Attributes:
        account_name (Optional[str]): Display name of the account.
        allow_instant_ach (Optional[bool]): Whether the partner enabled Instant ACH.
        beneficiaries (Optional[List[Beneficiary]]): IRA beneficiaries.
        cash_interest (Optional[CashInterest]): USD cash interest enrollment.
        custodial_account_type (Optional[str]): Custodial account type for the minor's state.
        enabled_assets (Optional[List[AssetClass]]): Asset classes enabled on the account.
        fpsl (Optional[FPSL]): Fully Paid Securities Lending configuration.
        instant_ach_blocked (Optional[bool]): Whether Alpaca blocked Instant ACH.
        investment_objective (Optional[str]): The user's investment objective.
        investment_time_horizon (Optional[str]): How long the user plans to invest.
        liquidity_needs (Optional[str]): How important liquidity is to the user.
        disclosures (Optional[AccountDisclosures]): Account disclosures, including ``is_discretionary``.
        minor_identity (Optional[MinorIdentity]): Identity of the minor on a custodial account.
        primary_account_holder_id (Optional[UUID]): UUID of the account's primary holder when available.
        risk_tolerance (Optional[str]): The user's risk tolerance.
        trading_configurations (Optional[AccountTradingConfigurations]): Trading settings.
        usd (Optional[AccountUSD]): USD values for a local-currency account.
    """

    disclosures: Optional[AccountDisclosures] = None
    account_name: Optional[str] = None
    allow_instant_ach: Optional[bool] = None
    beneficiaries: Optional[List[Beneficiary]] = None
    cash_interest: Optional[CashInterest] = None
    custodial_account_type: Optional[str] = None
    enabled_assets: Optional[List[AssetClass]] = None
    fpsl: Optional[FPSL] = None
    instant_ach_blocked: Optional[bool] = None
    investment_objective: Optional[str] = None
    investment_time_horizon: Optional[str] = None
    liquidity_needs: Optional[str] = None
    minor_identity: Optional[MinorIdentity] = None
    primary_account_holder_id: Optional[UUID] = None
    risk_tolerance: Optional[str] = None
    trading_configurations: Optional[AccountTradingConfigurations] = None
    usd: Optional[AccountUSD] = None

    def __init__(self, **data: Any) -> None:
        if isinstance(data.get("id"), str):
            data["id"] = UUID(data["id"])
        trusted_contact = data.get("trusted_contact")
        if isinstance(trusted_contact, dict):
            data["trusted_contact"] = TypeAdapter(TrustedContact).validate_python(
                trusted_contact,
                context={_TRUSTED_CONTACT_RESPONSE_KEY: True},
            )
        super(Account, self).__init__(**data)


class TradeAccount(BaseTradeAccount):
    """
    See Base TradeAccount model in common for full details on available fields.
    Represents trading account information for an Account.

    Attributes:
        cash_withdrawable (Optional[str]): Cash available for withdrawal from the account
        cash_transferable (Optional[str]): Cash available for transfer (JNLC) from the account
        previous_close (Optional[datetime]): Previous sessions close time
        last_long_market_value (Optional[str]): Value of all long positions as of previous trading day at 16:00:00 ET
        last_short_market_value (Optional[str]): Value of all short positions as of previous trading day at 16:00:00 ET
        last_cash (Optional[str]): Value of all cash as of previous trading day at 16:00:00 ET
        last_initial_margin (Optional[str]): Value of initial_margin as of previous trading day at 16:00:00 ET
        last_regt_buying_power (Optional[str]): Value of regt_buying_power as of previous trading day at 16:00:00 ET
        last_daytrading_buying_power (Optional[str]): Value of daytrading_buying_power as of previous trading day at 16:00:00 ET.
          Deprecated; removed from Alpaca responses on 2026-07-06 (FINRA intraday-margin migration) and defaults to None.
        last_daytrade_count (Optional[int]): Value of daytrade_count as of previous trading day at 16:00:00 ET.
          Deprecated; removed from Alpaca responses on 2026-07-06 (FINRA intraday-margin migration) and defaults to None.
        last_buying_power (Optional[str]): Value of buying_power as of previous trading day at 16:00:00 ET
        clearing_broker (Optional[ClearingBroker]): The Clearing broker for this account
    """

    cash_withdrawable: Optional[str]
    cash_transferable: Optional[str]
    previous_close: Optional[datetime]
    last_long_market_value: Optional[str]
    last_short_market_value: Optional[str]
    last_cash: Optional[str]
    last_initial_margin: Optional[str]
    last_regt_buying_power: Optional[str]
    last_daytrading_buying_power: Optional[str] = None
    last_daytrade_count: Optional[int] = None
    last_buying_power: Optional[str]
    clearing_broker: Optional[ClearingBroker]
