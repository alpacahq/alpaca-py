from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, parse_obj_as, validator, root_validator

from .enums import (
    AccountEntities,
    AccountStatus,
    AgreementType,
    DocumentType,
    EmploymentStatus,
    FundingSource,
    TaxIdType,
    VisaType,
)
from ..common.enums import Sort


class NonEmptyRequest(BaseModel):
    """
    Mixin for models that represent requests where we don't want to send nulls for optional fields.
    """

    def to_request_fields(self) -> dict:
        """
        the equivalent of self::dict but removes empty values.

        Ie say we only set trusted_contact.given_name instead of generating a dict like:
          {contact: {city: None, country: None...}, etc}
        we generate just:
          {trusted_contact:{given_name: "new value"}}

        Returns:
            dict: a dict containing any set fields
        """

        # pydantic almost has what we need by passing exclude_none to dict() but it returns:
        #  {trusted_contact: {}, contact: {}, identity: None, etc}
        # so we do a simple list comprehension to filter out None and {}

        return {
            key: val
            for key, val in self.dict(exclude_none=True).items()
            if val and len(val) > 0
        }


class Contact(BaseModel, validate_assignment=True):
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
    phone_number: str
    street_address: List[str]
    unit: Optional[str] = None
    city: str
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None

    @validator("state")
    def usa_state_has_value(cls, v: str, values: dict, **kwargs) -> str:
        """Validates that the state has a value if the country is USA

        Args:
            v (str): The state field's value
            values (dict): The values of each field

        Raises:
            ValueError: State is required for country USA

        Returns:
            str: The value of the state field
        """
        if "country" in values and values["country"] == "USA" and v is None:
            raise ValueError("State is required for country USA.")
        return v


class Identity(BaseModel, validate_assignment=True):
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
    date_of_birth: str
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


class Disclosures(BaseModel, validate_assignment=True):
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

    is_control_person: bool
    is_affiliated_exchange_or_finra: bool
    is_politically_exposed: bool
    immediate_family_exposed: bool
    employment_status: Optional[EmploymentStatus] = None
    employer_name: Optional[str] = None
    employer_address: Optional[str] = None
    employment_position: Optional[str] = None


class Agreement(BaseModel, validate_assignment=True):
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
    revision: Optional[str]


class Document(BaseModel, validate_assignment=True):
    """User documents provided within Account Model

    see https://alpaca.markets/docs/broker/api-references/accounts/accounts/#the-account-model

    Attributes:
        document_type (DocumentType): The type of document uploaded
        document_sub_type (str): The specific type of document, e.g. passport
        content (str): Base64 string representing the document
        mime_type (str): The format of content encoded by the string
    """

    id: UUID
    document_type: DocumentType
    document_sub_type: Optional[str] = None
    content: str
    mime_type: Optional[str] = None

    def __init__(__pydantic_self__, **data: Any) -> None:
        # validate the incoming id field for uuid
        if type(data["id"]) == str:
            data["id"] = UUID(data["id"])
        elif type(data["id"]) != UUID:
            raise ValueError("id must be a UUID or a UUID str")

        super().__init__(**data)


class TrustedContact(BaseModel, validate_assignment=True):
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
    """

    given_name: str
    family_name: str
    email_address: Optional[str] = None
    phone_number: Optional[str] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None

    @root_validator()
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


class Account(BaseModel, validate_assignment=True):
    """Contains information pertaining to a specific brokerage account

    see https://alpaca.markets/docs/broker/api-references/accounts/accounts/#the-account-model

    The fields contact, identity, disclosures, agreements, documents, trusted_contact, and trading_configurations
    are all optional and won't always be provided by the api depending on what endpoint you use and what options you
    pass

    Attributes:
        id (str): The account uuid used to reference this account
        account_number (str): A more human friendly identifier for this account
        status (AccountStatus): The approval status of this account
        crypto_status (Optional[AccountStatus]): The crypto trading status. Only present if crypto trading is enabled.
        currency (str): The currency the account's values are returned in
        last_equity (str): The total equity value stored in the account
        created_at (str): The timestamp when the account was created
        contact (Optional[Contact]): The contact details for the account holder
        identity (Optional[Identity]): The identity details for the account holder
        disclosures (Optional[Disclosures]): The account holder's political disclosures
        agreements (Optional[List[Agreement]]): The agreements the account holder has signed
        documents (Optional[List[Document]]): The documents the account holder has submitted
        trusted_contact (Optional[TrustedContact]): The account holder's trusted contact details
    """

    id: str
    account_number: str
    status: AccountStatus
    crypto_status: Optional[AccountStatus] = None
    currency: str
    last_equity: str
    created_at: str
    contact: Optional[Contact] = None
    identity: Optional[Identity] = None
    disclosures: Optional[Disclosures] = None
    agreements: Optional[List[Agreement]] = None
    documents: Optional[List[Document]] = None
    trusted_contact: Optional[TrustedContact] = None

    def __init__(self, **response):
        super().__init__(
            id=(response["id"]),
            account_number=(response["account_number"]),
            status=(response["status"]),
            crypto_status=(
                response["crypto_status"] if "crypto_status" in response else None
            ),
            currency=(response["currency"]),
            last_equity=(response["last_equity"]),
            created_at=(response["created_at"]),
            contact=(
                parse_obj_as(Contact, response["contact"])
                if "contact" in response
                else None
            ),
            identity=(
                parse_obj_as(Identity, response["identity"])
                if "identity" in response
                else None
            ),
            disclosures=(
                parse_obj_as(Disclosures, response["disclosures"])
                if "disclosures" in response
                else None
            ),
            agreements=(
                parse_obj_as(List[Agreement], response["agreements"])
                if "agreements" in response
                else None
            ),
            documents=(
                parse_obj_as(List[Document], response["documents"])
                if "documents" in response
                else None
            ),
            trusted_contact=(
                parse_obj_as(TrustedContact, response["trusted_contact"])
                if "trusted_contact" in response
                else None
            ),
        )


class AccountCreationRequest(BaseModel, validate_assignment=True):
    """Class used to format data necessary for making a request to create a brokerage account

    Attributes:
        contact (Contact): The contact details for the account holder
        identity (Identity): The identity details for the account holder
        disclosures (Disclosures): The account holder's political disclosures
        agreements (List[Agreement]): The agreements the account holder has signed
        documents (List[Document]): The documents the account holder has submitted
        trusted_contact (TrustedContact): The account holder's trusted contact details
    """

    contact: Contact
    identity: Identity
    disclosures: Disclosures
    agreements: List[Agreement]
    documents: Optional[List[Document]] = None
    trusted_contact: Optional[TrustedContact] = None


class UpdatableContact(Contact, validate_assignment=True):
    """
    An extended version of Contact that has all fields as optional, so you don't need to specify all fields if you only
    want to update a subset of them.

    Attributes:
        email_address (Optional[str]): The user's email address
        phone_number (Optional[str]): The user's phone number. It should include the country code.
        street_address (Optional[List[str]]): The user's street address lines.
        unit (Optional[str]): The user's apartment unit, if any.
        city (Optional[str]): The city the user resides in.
        state (Optional[str]): The state the user resides in. This is required if country is 'USA'.
        postal_code (Optional[str]): The user's postal
        country (Optional[str]): The country the user resides in. 3 letter country code is permissible.
    """

    # override the non-optional fields to now be optional
    email_address: Optional[str] = None
    phone_number: Optional[str] = None
    street_address: Optional[List[str]] = None
    city: Optional[str] = None


# We don't extend the Identity model because we have to remove fields, not all of them are updatable
class UpdatableIdentity(BaseModel, validate_assignment=True):
    """
       This class is a subset version of Identity. Currently, not all fields on accounts are modifiable so this class
       represents which ones are modifiable on the `identity` field of an account when making an
       BrokerClient::update_account call.

       Also has all fields as optional, so you don't need to specify all fields if you only want to update a subset

    Attributes:
           given_name (Optional[str]): The user's first name
           middle_name (Optional[str]): The user's middle name, if any
           family_name (Optional[str]): The user's last name
           tax_id (Optional[str]): The user's country specific tax id, required if tax_id_type is provided
           tax_id_type (Optional[TaxIdType]): The tax_id_type for the tax_id provided, required if tax_id provided
           country_of_citizenship (Optional[str]): The country the user is a citizen
           country_of_birth (Optional[str]): The country the user was born
           country_of_tax_residence (Optional[str]): The country the user files taxes
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

    given_name: Optional[str] = None
    middle_name: Optional[str] = None
    family_name: Optional[str] = None
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


class UpdatableDisclosures(Disclosures, validate_assignment=True):
    """
    An extended version of Disclosures that has all fields as optional, so you don't need to specify all fields if you
    only want to update a subset of them.

    Attributes:
        is_control_person (Optional[bool]): Whether user holds a controlling position in a publicly traded company
        is_affiliated_exchange_or_finra (Optional[bool]): If user is affiliated with any exchanges or FINRA
        is_politically_exposed (Optional[bool]): If user is politically exposed
        immediate_family_exposed (Optional[bool]): If user’s immediate family member is either politically exposed or holds a control position.
        employment_status (Optional[EmploymentStatus]): The employment status of the user
        employer_name (Optional[str]): The user's employer's name, if any
        employer_address (Optional[str]): The user's employer's address, if any
        employment_position (Optional[str]): The user's employment position, if any
    """

    is_control_person: Optional[bool] = None
    is_affiliated_exchange_or_finra: Optional[bool] = None
    is_politically_exposed: Optional[bool] = None
    immediate_family_exposed: Optional[bool] = None


class UpdatableTrustedContact(TrustedContact, validate_assignment=True):
    """
    An extended version of TrustedContact that has all fields as optional, so you don't need to specify all fields if
    you only want to update a subset of them.

    Attributes:
        given_name (Optional[str]): The first name of the user's trusted contact
        family_name (Optional[str]): The last name of the user's trusted contact
        email_address (Optional[str]): The email address of the user's trusted contact
        phone_number (Optional[str]): The email address of the user's trusted contact
        city (Optional[str]): The email address of the user's trusted contact
        state (Optional[str]): The email address of the user's trusted contact
        postal_code (Optional[str]): The email address of the user's trusted contact
        country (Optional[str]): The email address of the user's trusted contact
    """

    # only need to override these 2 as other fields were already optional
    given_name: Optional[str] = None
    family_name: Optional[str] = None

    # override the parent and set a new root validator that just allows all
    @root_validator()
    def root_validator(cls, values: dict) -> dict:
        """Override parent method to allow null contact info"""
        return values


class AccountUpdateRequest(NonEmptyRequest, validate_assignment=True):
    """
    Represents the data allowed in a request to update an Account. Note not all fields of an account
    are currently modifiable so this model uses models that represent the subset of modifiable fields.

    Attributes:
        contact (Optional[UpdatableContact]): Contact details to update to
        identity (Optional[UpdatableIdentity]): Identity details to update to
        disclosures (Optional[UpdatableDisclosures]): Disclosure details to update to
        trusted_contact (Optional[UpdatableTrustedContact]): TrustedContact details to update to
    """

    contact: Optional[UpdatableContact] = None
    identity: Optional[UpdatableIdentity] = None
    disclosures: Optional[UpdatableDisclosures] = None
    trusted_contact: Optional[UpdatableTrustedContact] = None


class ListAccountsRequest(BaseModel, validate_assignment=True):
    """
    Represents the values you can specify when making a request to list accounts

    Attributes:
        query (Optional[str]): Pass space-delimited tokens. The response will contain accounts that match with each of
         the tokens (logical AND). A match means the token is present in either the account’s associated account number,
         phone number, name, or e-mail address (logical OR).
        created_before (Optional[datetime]): Accounts that were created before this date
        created_after (Optional[datetime]): Accounts that were created after this date
        status (Optional[AccountStatus]): Accounts that have their status field as one of these
        sort (Sort, optional): The chronological order of response based on the submission time. Defaults to DESC.
        entities (Optional[List[AccountEntities]]): By default, this endpoint doesn't return all information for each
         account to save space in the response. This field lets you specify what additional information you want to be
         included on each account.

         ie, specifying [IDENTITY, CONTACT] would ensure that each returned account has its `identity` and `contact`
         fields filled out.
    """

    query: Optional[str] = None
    created_before: Optional[datetime] = None
    created_after: Optional[datetime] = None
    status: Optional[List[AccountStatus]] = None
    sort: Sort
    entities: Optional[List[AccountEntities]] = None

    def __init__(self, *args, **kwargs):
        # The api itself actually defaults to DESC, but this way our docs won't be incorrect if the api changes under us
        if "sort" not in kwargs or kwargs["sort"] is None:
            kwargs["sort"] = Sort.DESC

        super().__init__(*args, **kwargs)
