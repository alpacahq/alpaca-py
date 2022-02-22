from typing import List, Optional

from pydantic import BaseModel, parse_obj_as, validator

from .enums import (AccountStatus, AgreementType, DocumentType,
                    EmploymentStatus, FundingSource, TaxIdType, VisaType)


class Contact(BaseModel):
    """User contact details within Account Model

    see https://alpaca.markets/docs/broker/api-references/accounts/accounts/#the-account-model

    Attributes:
        email_address (str): The user's email address
        phone_number (str): The user's phone number. It should include the country code.
        street_address (List[str]): The user's street address lines.
        unit (str): The user's apartment unit, if any.
        city (str): The city the user resides in.
        state (str): The state the user resides in. This is required if country is 'USA'.
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
    def usa_state_has_value(cls, v: str, values: dict, **kwargs) -> None:
        """Validates that the state has a value if the country is USA

        Args:
            v (str): The state field's value
            values (dict): The values of each field

        Raises:
            ValueError: State is required for country USA

        Returns:
            str: The value of the state field
        """
        if "country" in values and values["country"] == "USA" and v == None:
            raise ValueError("State is required for country USA.")
        return v


class Identity(BaseModel):
    """User identity details within Account Model

    see https://alpaca.markets/docs/broker/api-references/accounts/accounts/#the-account-model

    Attributes:
        given_name (str): The user's first name
        middle_name (str): The user's middle name, if any
        family_name (str): The user's last name
        date_of_birth (str): The user's date of birth
        tax_id (str): The user's country specific tax id, required if tax_id_type is provided
        tax_id_type (TaxIdType): The tax_id_type for the tax_id provided, required if tax_id provided
        country_of_citizenship (str): The country the user is a citizen
        country_of_birth (str): The country the user was born
        country_of_tax_residence (str): The country the user files taxes
        visa_type (VisaType): Only used to collect visa types for users residing in the USA.
        visa_expiration_date (str): The date of expiration for visa, Required if visa_type is set.
        date_of_departure_from_usa (str): Required if visa_type = B1 or B2
        permanent_resident (bool): Only used to collect permanent residence status in the USA.
        funding_source (List[FundingSource]): How the user will fund their account
        annual_income_min (flot): The minimum of the user's income range
        annual_income_max (float): The maximum of the user's income range
        liquid_net_worth_min (float): The minimum of the user's liquid net worth range
        liquid_net_worth_max (float): The maximum of the user's liquid net worth range
        total_net_worth_min (float): The minimum of the user's total net worth range
        total_net_worth_max (float): The maximum of the user's total net worth range
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
    permanent_resident: Optional[str] = None
    funding_source: Optional[List[FundingSource]]
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

    is_control_person: bool
    is_affiliated_exchange_or_finra: bool
    is_politically_exposed: bool
    immediate_family_exposed: bool
    employment_status: Optional[EmploymentStatus] = None
    employer_name: Optional[str] = None
    employer_address: Optional[str] = None
    employment_position: Optional[str] = None

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
    revision: str


class Document(BaseModel):
    """User documents provided within Account Model

    see https://alpaca.markets/docs/broker/api-references/accounts/accounts/#the-account-model

    Attributes:
        document_type (DocumentType): The type of document uploaded
        document_sub_type (str): The specific type of document, e.g. passport
        content (str): Base64 string representing the document
        mime_type (str): The format of content encoded by the string
    """

    document_type: DocumentType
    document_sub_type: Optional[str] = None
    content: str
    mime_type: str


class TrustedContact(BaseModel):
    """User's trusted contact details within Account Model

    see https://alpaca.markets/docs/broker/api-references/accounts/accounts/#the-account-model

    Attributes:
        given_name (str): The first name of the user's trusted contact
        family_name (str): The last name of the user's trusted contact
        email_address (str): The email address of the user's trusted contact
        phone_number (str): The email address of the user's trusted contact
        city (str): The email address of the user's trusted contact
        state (str): The email address of the user's trusted contact
        postal_code (str): The email address of the user's trusted contact
        country (str): The email address of the user's trusted contact
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

    @validator("email_address")
    def has_at_least_one_contact(cls, v: str, values: dict, **kwargs) -> str:
        """Validates whether there is at least one form of contact for the trusted contact

        Args:
            v (str): The email address field value
            values (dict): The values of each field

        Raises:
            ValueError: At least one contact field is required

        Returns:
            str: the value of the email address field
        """
        has_phone_number = "phone_number" in values and values["phone_number"] != None
        has_street_address = (
            "street_address" in values and values["street_address"] != None
        )
        has_email_address = v != None

        if has_phone_number or has_street_address or has_email_address:
            return v

        raise ValueError("At least one method of contact required for trusted contact")


class Account(BaseModel):
    """Contains information pertaining to a specific brokerage account
    
    see https://alpaca.markets/docs/broker/api-references/accounts/accounts/#the-account-model

    Attributes:
        id (str): The account uuid used to reference this account
        account_number (str): A more human friendly identifier for this account
        status (str): The approval status of this account
        crypto_status (str): The crypto trading status; either paper or live.
        currency (str): The currency the account's values are returned in
        last_equity (str): The total equity value stored in the account
        created_at (str): The timestamp when the account was created
        contact (Contact): The contact details for the account holder
        identity (Identity): The identity details for the account holder
        disclosures (Disclosures): The account holder's political disclosures
        agreements (List[Agreement]): The agreements the account holder has signed
        documents (List[Document]): The documents the account holder has submitted
        trusted_contact (TrustedContact): The account holder's trusted contact details
    """

    id: str
    account_number: str
    status: AccountStatus
    crypto_status: str
    currency: str
    last_equity: str
    created_at: str
    contact: Contact
    identity: Identity
    disclosures: Disclosures
    agreements: List[Agreement]
    documents: Optional[List[Document]] = None
    trusted_contact: Optional[TrustedContact] = None

    def __init__(self, **response):

        contact = parse_obj_as(Contact, response['contact'])
        identity = parse_obj_as(Identity, response['identity'])
        disclosures = parse_obj_as(Disclosures, response['disclosures'])
        agreements = parse_obj_as(List[Agreement], response['agreements'])

        id = response['id']
        account_number = response['account_number']
        status = response['status']
        crypto_status = response['crypto_status']
        currency = response['currency']
        last_equity = response['last_equity']
        created_at = response['created_at']

        super().__init__(id=id,
                        account_number=account_number,
                        status=status,
                        crypto_status=crypto_status,
                        currency=currency, 
                        last_equity=last_equity, 
                        created_at=created_at, 
                        contact=contact, 
                        identity=identity, 
                        disclosures=disclosures,
                        agreements=agreements)


class AccountCreationRequest(BaseModel):
    """Class used to format data necessary for making a request to create a brokerage account

    Args:
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
