from datetime import date, datetime
from ipaddress import IPv4Address, IPv6Address
from typing import Any, Optional, Union
from uuid import UUID

from pydantic import model_validator

from alpaca.broker.enums import DocumentType, TradeDocumentSubType, TradeDocumentType
from alpaca.common.models import ModelWithID, ValidateBaseModel as BaseModel

IPAddress = Union[IPv4Address, IPv6Address]


class AccountDocument(BaseModel):
    """
    User documents provided within Account Model.

    This model is different from the TradeDocument model in that this model represents documents having to do with a
    brokerage Account.

    see https://alpaca.markets/docs/broker/api-references/accounts/accounts/#the-account-model

    Attributes:
        id (UUID): ID of the Document
        document_type (DocumentType): The type of document uploaded
        document_sub_type (Optional[str]): The specific type of document, e.g. passport
        name (Optional(str)): Name of the document if present
        content (str): Base64 string representing the document
        mime_type (str): The format of content encoded by the string
    """

    id: Optional[UUID]
    document_type: Optional[DocumentType]
    document_sub_type: Optional[str] = None
    content: Optional[str] = None
    mime_type: Optional[str] = None

    def __init__(self, **data: Any) -> None:
        # validate the incoming id field for uuid
        _id = data.get("id", None)
        if isinstance(_id, str):
            data["id"] = UUID(_id)

        super().__init__(**data)


class TradeDocument(ModelWithID):
    """
    Similar to the AccountDocument model but this represents documents having to do with a TradeAccount not a regular
    Account.

    IE:  Account Monthly Statements or Trade Confirmations.

    Attributes:
        id (UUID): Unique id of the TradeDocument
        name (str): Name of the document
        type (TradeDocumentType): The kind of TradeDocument this is
        sub_type (Optional[TradeDocumentSubType]): The subtype of the document. The API returns "" in the case of this
          not being specified, however we transform this case into None for convenience.
        date (date): Date on when this TradeDocument was generated
    """

    name: str
    type: TradeDocumentType
    sub_type: Optional[TradeDocumentSubType] = None
    date: date

    def __init__(self, **data: Any) -> None:
        if "id" in data and isinstance(data["id"], str):
            data["id"] = UUID(data["id"])

        if "sub_type" in data and data["sub_type"] == "":
            data["sub_type"] = None

        super().__init__(**data)


class W8BenDocument(BaseModel):
    """
    Represents the information normally contained in a W8BEN document as fields for convenience if you don't
    want to upload a file.

    Please see https://alpaca.markets/docs/api-references/broker-api/accounts/accounts/#international-accounts
    for more information.

    TODO: None of the docs or code explain what any of these fields mean. Guessing based on name alone for
      all of them; but we really need the docs updated.

    Attributes:
        additional_conditions (Optional[str]): Any additional conditions to specify
        country_citizen (str): The Country that the applicant is a citizen of
        date (date): date signed
        date_of_birth (date): DOB of applicant
        foreign_tax_id (Optional[str]): Applicant's tax id in their home country
        ftin_not_required (Optional[bool]): Required if foreign_tax_id and tax_id_ssn are empty.
        full_name (str): Full name of applicant
        income_type (Optional[str]): income type of applicant
        ip_address (IPAddress): ip address of applicant when signed
        mailing_address_city_state (Optional[str]): mailing city/state of applicant
        mailing_address_country (Optional[str]): mailing country for applicant
        mailing_address_street (Optional[str]): mailing street address for applicant
        paragraph_number (Optional[str]): TODO: get documentation for this field
        percent_rate_withholding (Optional[str]): TODO: get documentation for this field
        permanent_address_city_state (str): permanent city/state of applicant
        permanent_address_country (str): permanent country of residence of applicant
        permanent_address_street (str): permanent street address of applicant
        reference_number (Optional[str]): TODO: Get documentation for this field
        residency (Optional[str]): Country of residency of applicant
          TODO: get real documentation for this field. current is just guess based on example
        revision (str): Revision of the W8BEN form
        signer_full_name (str): Full name of signing user
        tax_id_ssn (Optional[str]): TaxID/SSN of applicant
        timestamp (datetime): timestamp when form data was gathered
    """

    country_citizen: str
    date: date
    date_of_birth: date
    full_name: str
    ip_address: IPAddress
    permanent_address_city_state: str
    permanent_address_country: str
    permanent_address_street: str
    revision: str
    signer_full_name: str
    timestamp: datetime

    # optional fields
    additional_conditions: Optional[str] = None
    foreign_tax_id: Optional[str] = None
    ftin_not_required: Optional[bool] = None
    income_type: Optional[str] = None
    mailing_address_city_state: Optional[str] = None
    mailing_address_country: Optional[str] = None
    mailing_address_street: Optional[str] = None
    paragraph_number: Optional[str] = None
    percent_rate_withholding: Optional[str] = None
    reference_number: Optional[str] = None
    residency: Optional[str] = None
    tax_id_ssn: Optional[str] = None

    @model_validator(mode="before")
    def root_validator(cls, values: dict) -> dict:
        foreign_tax_set = (
            "foreign_tax_id" in values and values["foreign_tax_id"] is not None
        )
        tax_id_set = "tax_id_ssn" in values and values["tax_id_ssn"] is not None
        ftin_set = (
            "ftin_not_required" in values and values["ftin_not_required"] is not None
        )

        if not foreign_tax_set and not tax_id_set and not ftin_set:
            raise ValueError(
                "ftin_not_required must be set if foreign_tax_id and tax_id_ssn are not"
            )

        return values
