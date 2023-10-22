from datetime import date, datetime
from typing import List, Optional, Union, Dict, Any
from uuid import UUID

from pydantic import model_validator, field_validator

from alpaca.broker.models.accounts import (
    AccountDocument,
    Agreement,
    Contact,
    Disclosures,
    Identity,
    TrustedContact,
)
from alpaca.broker.models.documents import W8BenDocument
from alpaca.broker.models.trading import Order
from alpaca.broker.enums import (
    AccountEntities,
    BankAccountType,
    DocumentType,
    EmploymentStatus,
    FeePaymentMethod,
    FundingSource,
    IdentifierType,
    TaxIdType,
    TradeDocumentType,
    TransferDirection,
    TransferTiming,
    TransferType,
    UploadDocumentMimeType,
    UploadDocumentSubType,
    VisaType,
    JournalEntryType,
    JournalStatus,
)
from alpaca.common.enums import Sort, SupportedCurrencies
from alpaca.trading.enums import ActivityType, AccountStatus, OrderType, AssetClass
from alpaca.common.requests import NonEmptyRequest
from alpaca.trading.requests import (
    OrderRequest as BaseOrderRequest,
    MarketOrderRequest as BaseMarketOrderRequest,
    LimitOrderRequest as BaseLimitOrderRequest,
    StopOrderRequest as BaseStopOrderRequest,
    StopLimitOrderRequest as BaseStopLimitOrderRequest,
    TrailingStopOrderRequest as BaseTrailingStopOrderRequest,
    CancelOrderResponse as BaseCancelOrderResponse,
)


# ############################## Accounts ################################# #


class CreateAccountRequest(NonEmptyRequest):
    """Class used to format data necessary for making a request to create a brokerage account

    Attributes:
        contact (Contact): The contact details for the account holder
        identity (Identity): The identity details for the account holder
        disclosures (Disclosures): The account holder's political disclosures
        agreements (List[Agreement]): The agreements the account holder has signed
        documents (List[AccountDocument]): The documents the account holder has submitted
        trusted_contact (TrustedContact): The account holder's trusted contact details
    """

    contact: Contact
    identity: Identity
    disclosures: Disclosures
    agreements: List[Agreement]
    documents: Optional[List[AccountDocument]] = None
    trusted_contact: Optional[TrustedContact] = None
    currency: Optional[SupportedCurrencies] = None  # None = USD
    enabled_assets: Optional[List[AssetClass]] = None  # None = Default to server

    @model_validator(mode="before")
    def validate_parameters_only_optional_in_response(cls, values: dict) -> dict:
        """
        Validate parameters that are optional in the response but not in the request.
        """
        nullable_fields_by_model = {
            "contact": "phone_number",
            "identity": "date_of_birth",
            "disclosures": "is_control_person",
            "disclosures": "is_affiliated_exchange_or_finra",
            "disclosures": "is_politically_exposed",
        }
        for model, field in nullable_fields_by_model.items():
            if dict(values[model]).get(field, None) is None:
                raise ValueError(f"{field} is required to create a new account.")
        return values


class UpdatableContact(Contact):
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
class UpdatableIdentity(NonEmptyRequest):
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


class UpdatableDisclosures(Disclosures):
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


class UpdatableTrustedContact(TrustedContact):
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

    # override the parent and set a new root field_validator that just allows all
    @model_validator(mode="before")
    def root_validator(cls, values: dict) -> dict:
        """Override parent method to allow null contact info"""
        return values


class UpdateAccountRequest(NonEmptyRequest):
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


class ListAccountsRequest(NonEmptyRequest):
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


class GetAccountActivitiesRequest(NonEmptyRequest):
    """
    Represents the filtering values you can specify when getting AccountActivities for an Account

    **Notes on pagination and the `page_size` and `page_token` fields**.

    The BrokerClient::get_account_activities function by default will automatically handle the pagination of results
    for you to get all results at once. However, if you're requesting a very large amount of results this can use a
    large amount of memory and time to gather all the results. If you instead want to handle
    pagination yourself `page_size` and `page_token` are how you would handle this.

    Say you put in a request with `page_size` set to 4, you'll only get 4 results back to get
    the next "page" of results you would set `page_token` to be the `id` field of the last Activity returned in the
    result set.

    This gets more indepth if you start specifying the `sort` field as well. If specified with a direction of Sort.DESC,
    for example, the results will end before the activity with the specified ID. However, specified with a direction of
    Sort.ASC, results will begin with the activity immediately after the one specified.

    Also, to note if `date` is not specified, the default and maximum `page_size` value is 100. If `date` is specified,
    the default behavior is to return all results, and there is no maximum page size; page size is still supported in
    this state though.

    Please see https://alpaca.markets/docs/api-references/broker-api/accounts/account-activities/#retrieving-account-activities
    for more information

    Attributes:
        account_id (Optional[Union[UUID, str]]): Specifies to filter to only activities for this Account
        activity_types (Optional[List[ActivityType]]): A list of ActivityType's to filter results down to
        date (Optional[datetime]): Filter to Activities only on this date.
        until (Optional[datetime]): Filter to Activities before this date. Cannot be used if `date` is also specified.
        after (Optional[datetime]): Filter to Activities after this date. Cannot be used if `date` is also specified.
        direction (Optional[Sort]): Which direction to sort results in. Defaults to Sort.DESC
        page_size (Optional[int]): The maximum number of entries to return in the response
        page_token (Optional[Union[UUID, str]]): If you're not using the built-in pagination this field is what you
          would use to mark the end of the results of your last page.
    """

    account_id: Optional[Union[UUID, str]] = None
    activity_types: Optional[List[ActivityType]] = None
    date: Optional[datetime] = None
    until: Optional[datetime] = None
    after: Optional[datetime] = None
    direction: Optional[Sort] = None
    page_size: Optional[int] = None
    page_token: Optional[Union[UUID, str]] = None

    def __init__(self, *args, **kwargs):
        if "account_id" in kwargs and type(kwargs["account_id"]) == str:
            kwargs["account_id"] = UUID(kwargs["account_id"])

        super().__init__(*args, **kwargs)

    @model_validator(mode="before")
    def root_validator(cls, values: dict) -> dict:
        """Verify that certain conflicting params aren't set"""

        date_set = "date" in values and values["date"] is not None
        after_set = "after" in values and values["after"] is not None
        until_set = "until" in values and values["until"] is not None

        if date_set and after_set:
            raise ValueError("Cannot set date and after at the same time")

        if date_set and until_set:
            raise ValueError("Cannot set date and until at the same time")

        return values


# ############################## Documents ################################# #


class GetTradeDocumentsRequest(NonEmptyRequest):
    """
    Represents the various filters you can specify when making a call to get TradeDocuments for an Account

    Attributes:
        start (Optional[Union[date, str]]): Filter to TradeDocuments created after this Date. str values will attempt to
          be upcast into date instances. Format must be in YYYY-MM-DD.
        end (Optional[Union[date, str]]): Filter to TradeDocuments created before this Date. str values will attempt to
          be upcast into date instances. Format must be in YYYY-MM-DD.
        type (Optional[TradeDocumentType]): Filter to only these types of TradeDocuments
    """

    start: Optional[Union[date, str]] = None
    end: Optional[Union[date, str]] = None
    type: Optional[TradeDocumentType] = None

    def __init__(self, **data) -> None:
        if "start" in data and isinstance(data["start"], str):
            data["start"] = date.fromisoformat(data["start"])

        if "end" in data and isinstance(data["end"], str):
            data["end"] = date.fromisoformat(data["end"])

        super().__init__(**data)

    @model_validator(mode="before")
    def root_validator(cls, values: dict) -> dict:
        if (
            "start" in values
            and values["start"] is not None
            and "end" in values
            and values["end"] is not None
            and values["start"] > values["end"]
        ):
            raise ValueError("start must not be after end!!")

        return values


class UploadDocumentRequest(NonEmptyRequest):
    """
    Attributes:
        document_type (DocumentType): The type of document you are uploading
        document_sub_type (Optional[UploadDocumentSubType]): If supported for the corresponding `document_type` this
          field allows you to specify a sub type to be even more specific.
        content (str): A string containing Base64 encoded data to upload.
        mime_type (UploadDocumentMimeType): The mime type of the data in `content`
    """

    document_type: DocumentType
    document_sub_type: Optional[UploadDocumentSubType] = None
    content: str
    mime_type: UploadDocumentMimeType

    @model_validator(mode="before")
    def root_validator(cls, values: dict) -> dict:
        if values["document_type"] == DocumentType.W8BEN:
            raise ValueError(
                "Error please use the UploadW8BenDocument class for uploading W8BEN documents"
            )

        if values.get("document_sub_type", None) == UploadDocumentSubType.FORM_W8_BEN:
            raise ValueError(
                "Error please use the UploadW8BenDocument class for uploading W8BEN documents"
            )

        return values


class UploadW8BenDocumentRequest(NonEmptyRequest):
    """
    Attributes:
        content (Optional[str]): A string containing Base64 encoded data to upload. Must be set if `content_data` is not
          set.
        content_data (Optional[W8BenDocument]): The data representing a W8BEN document in field form. Must be set if
          `content` is not set.
        mime_type (UploadDocumentMimeType): The mime type of the data in `content`, or if using `content_data` must be
          UploadDocumentMimeType.JSON. If `content_data` is set this will default to JSON
    """

    # These 2 are purposely undocumented as they should be here for NonEmptyRequest but they shouldn't be touched or
    # set by users since they always need to be set values
    document_type: DocumentType
    document_sub_type: UploadDocumentSubType

    content: Optional[str] = None
    content_data: Optional[W8BenDocument] = None
    mime_type: UploadDocumentMimeType

    def __init__(self, **data) -> None:
        # Always set these to their expected values
        data["document_type"] = DocumentType.W8BEN
        data["document_sub_type"] = UploadDocumentSubType.FORM_W8_BEN

        if (
            "mime_type" not in data
            and "content_data" in data
            and data["content_data"] is not None
        ):
            data["mime_type"] = UploadDocumentMimeType.JSON

        super().__init__(**data)

    @model_validator(mode="before")
    def root_validator(cls, values: dict) -> dict:
        content_is_none = values.get("content", None) is None
        content_data_is_none = values.get("content_data", None) is None

        if content_is_none and content_data_is_none:
            raise ValueError(
                "You must specify one of either the `content` or `content_data` fields"
            )

        if not content_is_none and not content_data_is_none:
            raise ValueError(
                "You can only specify one of either the `content` or `content_data` fields"
            )

        if values["document_type"] != DocumentType.W8BEN:
            raise ValueError("document_type must be W8BEN.")

        if values["document_sub_type"] != UploadDocumentSubType.FORM_W8_BEN:
            raise ValueError("document_sub_type must be FORM_W8_BEN.")

        if (
            not content_data_is_none
            and values["mime_type"] != UploadDocumentMimeType.JSON
        ):
            raise ValueError("If `content_data` is set then `mime_type` must be JSON")

        return values


# ############################## Banking and Transfers ################################# #


class CreateACHRelationshipRequest(NonEmptyRequest):
    """
    Attributes:
        account_owner_name (str): The name of the ACH account owner for the relationship that is being created.
        bank_account_type (BankAccountType): Specifies the type of bank account for the ACH relationship that is being
          created.
        bank_account_number (str): The bank account number associated with the ACH relationship.
        bank_routing_number (str): THe bank routing number associated with the ACH relationship.
        nickname (Optional[str]): Optionally specify a nickname to assign to the created ACH relationship.
    """

    account_owner_name: str
    bank_account_type: BankAccountType
    bank_account_number: str  # TODO: Validate bank account number format.
    bank_routing_number: str  # TODO: Validate bank routing number format.
    nickname: Optional[str] = None


class CreatePlaidRelationshipRequest(NonEmptyRequest):
    """
    This request is made following the Plaid bank account link user flow.

    Upon the user completing their connection with Plaid, a public token specific to the user is returned by Plaid. This
    token is used to get an Alpaca processor token via Plaid's /processor/token/create endpoint, which is subsequently
    used by this endpoint to transfer the user's Plaid information to Alpaca.

    Attributes:
        processor_token (str): The processor token that is specific to Alpaca and was returned by Plaid.
    """

    processor_token: str


class CreateBankRequest(NonEmptyRequest):
    """
    Attributes:
        name (str): The name of the recipient bank.
        bank_code_type (IdentifierType): Specifies the type of the bank (international or domestic). See
          enums.IdentifierType for more details.
        bank_code (str): The 9-digit ABA routing number (domestic) or bank identifier code (BIC, international).
        account_number (str): The bank account number.
        country (Optional[str]): The country of the bank, if and only if creating an international bank account
          connection.
        state_province (Optional[str]): The state/province of the bank, if and only if creating an international bank
          account connection.
        postal_code (Optional[str]): The postal code of the bank, if and only if creating an international bank account
          connection.
        city (Optional[str]): The city of the bank, if and only if creating an international bank account connection.
        street_address (Optional[str]): The street address of the bank, if and only if creating an international bank
          account connection.
    """

    name: str
    bank_code_type: IdentifierType
    bank_code: str
    account_number: str
    country: Optional[str] = None
    state_province: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    street_address: Optional[str] = None

    @model_validator(mode="before")
    def root_validator(cls, values: dict) -> dict:
        if "bank_code_type" not in values:
            # Bank code type was not valid, so a ValueError will be thrown regardless.
            return values

        international_parameters = [
            "country",
            "state_province",
            "postal_code",
            "city",
            "street_address",
        ]

        bank_code_type = values["bank_code_type"]
        if bank_code_type == IdentifierType.ABA:
            for international_param in international_parameters:
                if (
                    international_param in values
                    and values[international_param] is not None
                ):
                    raise ValueError(
                        f"You may only specify the {international_param} for international bank accounts."
                    )
        elif bank_code_type == IdentifierType.BIC:
            for international_param in international_parameters:
                if (
                    international_param not in values
                    or values[international_param] is None
                ):
                    raise ValueError(
                        f"You must specify the {international_param} for international bank accounts."
                    )

        return values


class _CreateTransferRequest(NonEmptyRequest):
    """
    Attributes:
        amount (str): Amount of transfer, must be > 0. Any applicable fees will be deducted from this value.
        direction (TransferDirection): Direction of the transfer.
        timing (TransferTiming): Timing of the transfer.
        fee_payment_method (Optional[FeePaymentMethod]): Determines how any applicable fees will be paid. Default value
          is invoice.
    """

    amount: str
    direction: TransferDirection
    timing: TransferTiming
    fee_payment_method: Optional[FeePaymentMethod] = None

    @field_validator("amount")
    def amount_must_be_positive(cls, value: str) -> str:
        if float(value) <= 0:
            raise ValueError("You must provide an amount > 0.")
        return value


class CreateACHTransferRequest(_CreateTransferRequest):
    """
    Attributes:
        transfer_type (TransferType): Type of the transfer.
        relationship_id (Optional[UUID]): ID of the relationship to use for the transfer, required for ACH transfers.
    """

    relationship_id: UUID
    transfer_type: TransferType = TransferType.ACH

    @field_validator("transfer_type")
    def transfer_type_must_be_ach(cls, value: TransferType) -> TransferType:
        if value != TransferType.ACH:
            raise ValueError(
                "Transfer type must be TransferType.ACH for ACH transfer requests."
            )
        return value


class CreateBankTransferRequest(_CreateTransferRequest):
    """
    Attributes:
        bank_id (UUID): ID of the bank to use for the transfer, required for wire transfers.
        additional_information (Optional[str]): Additional wire transfer details.
    """

    bank_id: UUID
    transfer_type: TransferType = TransferType.WIRE
    additional_information: Optional[str] = None

    @field_validator("transfer_type")
    def transfer_type_must_be_wire(cls, value: TransferType) -> TransferType:
        if value != TransferType.WIRE:
            raise ValueError(
                "Transfer type must be TransferType.WIRE for bank transfer requests."
            )
        return value


class GetTransfersRequest(NonEmptyRequest):
    """
    Attributes:
        direction: Optionally filter for transfers of only a single TransferDirection.
    """

    direction: Optional[TransferDirection] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


# ############################## Orders ################################# #


class OrderRequest(BaseOrderRequest):
    """
    See base alpaca.trading.requests.OrderRequest model for more information.

    Attributes:
        symbol (str): The symbol identifier for the asset being traded
        qty (Optional[float]): The number of shares to trade. Fractional qty for stocks only with market orders.
        notional (Optional[float]): The base currency value of the shares to trade. For stocks, only works with MarketOrders.
            **Does not work with qty**.
        side (OrderSide): Whether the order will buy or sell the asset.
        type (OrderType): The execution logic type of the order (market, limit, etc).
        time_in_force (TimeInForce): The expiration logic of the order.
        extended_hours (Optional[float]): Whether the order can be executed during regular market hours.
        client_order_id (Optional[float]): A string to identify which client submitted the order.
        order_class (Optional[OrderClass]): The class of the order. Simple orders have no other legs.
        take_profit (Optional[TakeProfitRequest]): For orders with multiple legs, an order to exit a profitable trade.
        stop_loss (Optional[StopLossRequest]): For orders with multiple legs, an order to exit a losing trade.
        commission (Optional[float]): The dollar value commission you want to charge the end user.
    """

    commission: Optional[float] = None
    currency: Optional[SupportedCurrencies] = None  # None = USD

    @model_validator(mode="before")
    def order_type_must_be_market_for_lct(
        cls, values: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Order type must always be market if currency is not USD.
        See https://alpaca.markets/docs/broker/integration/lct/#submit-stock-trade
        """
        if (
            values.get("type") != OrderType.MARKET
            and "currency" in values
            and values.get("currency", SupportedCurrencies.USD)
            != SupportedCurrencies.USD
        ):
            raise ValueError(
                "Order type must be OrderType.MARKET if the order is in a local currency."
            )
        return values


class MarketOrderRequest(BaseMarketOrderRequest):
    """
    See base alpaca.trading.requests.MarketOrderRequest model for more information.

    Attributes:
        symbol (str): The symbol identifier for the asset being traded
        qty (Optional[float]): The number of shares to trade. Fractional qty for stocks only with market orders.
        notional (Optional[float]): The base currency value of the shares to trade. For stocks, only works with MarketOrders.
            **Does not work with qty**.
        side (OrderSide): Whether the order will buy or sell the asset.
        type (OrderType): The execution logic type of the order (market, limit, etc).
        time_in_force (TimeInForce): The expiration logic of the order.
        extended_hours (Optional[float]): Whether the order can be executed during regular market hours.
        client_order_id (Optional[float]): A string to identify which client submitted the order.
        order_class (Optional[OrderClass]): The class of the order. Simple orders have no other legs.
        take_profit (Optional[TakeProfitRequest]): For orders with multiple legs, an order to exit a profitable trade.
        stop_loss (Optional[StopLossRequest]): For orders with multiple legs, an order to exit a losing trade.
        commission (Optional[float]): The dollar value commission you want to charge the end user.
    """

    commission: Optional[float] = None


class LimitOrderRequest(BaseLimitOrderRequest):
    """
    See base alpaca.trading.requests.LimitOrderRequest model for more information.

    Attributes:
        symbol (str): The symbol identifier for the asset being traded
        qty (Optional[float]): The number of shares to trade. Fractional qty for stocks only with market orders.
        notional (Optional[float]): The base currency value of the shares to trade. For stocks, only works with MarketOrders.
            **Does not work with qty**.
        side (OrderSide): Whether the order will buy or sell the asset.
        type (OrderType): The execution logic type of the order (market, limit, etc).
        time_in_force (TimeInForce): The expiration logic of the order.
        extended_hours (Optional[float]): Whether the order can be executed during regular market hours.
        client_order_id (Optional[float]): A string to identify which client submitted the order.
        order_class (Optional[OrderClass]): The class of the order. Simple orders have no other legs.
        take_profit (Optional[TakeProfitRequest]): For orders with multiple legs, an order to exit a profitable trade.
        stop_loss (Optional[StopLossRequest]): For orders with multiple legs, an order to exit a losing trade.
        limit_price (float): The worst fill price for a limit or stop limit order.
        commission (Optional[float]): The dollar value commission you want to charge the end user.
    """

    commission: Optional[float] = None


class StopOrderRequest(BaseStopOrderRequest):
    """
    See base alpaca.trading.requests.StopOrderRequest model for more information.

    Attributes:
        symbol (str): The symbol identifier for the asset being traded
        qty (Optional[float]): The number of shares to trade. Fractional qty for stocks only with market orders.
        notional (Optional[float]): The base currency value of the shares to trade. For stocks, only works with MarketOrders.
            **Does not work with qty**.
        side (OrderSide): Whether the order will buy or sell the asset.
        type (OrderType): The execution logic type of the order (market, limit, etc).
        time_in_force (TimeInForce): The expiration logic of the order.
        extended_hours (Optional[float]): Whether the order can be executed during regular market hours.
        client_order_id (Optional[float]): A string to identify which client submitted the order.
        order_class (Optional[OrderClass]): The class of the order. Simple orders have no other legs.
        take_profit (Optional[TakeProfitRequest]): For orders with multiple legs, an order to exit a profitable trade.
        stop_loss (Optional[StopLossRequest]): For orders with multiple legs, an order to exit a losing trade.
        stop_price (float): The price at which the stop order is converted to a market order or a stop limit
            order is converted to a limit order.
        commission (Optional[float]): The dollar value commission you want to charge the end user.
    """

    commission: Optional[float] = None


class StopLimitOrderRequest(BaseStopLimitOrderRequest):
    """
    See base alpaca.trading.requests.StopLimitOrderRequest model for more information.

    Attributes:
        symbol (str): The symbol identifier for the asset being traded
        qty (Optional[float]): The number of shares to trade. Fractional qty for stocks only with market orders.
        notional (Optional[float]): The base currency value of the shares to trade. For stocks, only works with MarketOrders.
            **Does not work with qty**.
        side (OrderSide): Whether the order will buy or sell the asset.
        type (OrderType): The execution logic type of the order (market, limit, etc).
        time_in_force (TimeInForce): The expiration logic of the order.
        extended_hours (Optional[float]): Whether the order can be executed during regular market hours.
        client_order_id (Optional[float]): A string to identify which client submitted the order.
        order_class (Optional[OrderClass]): The class of the order. Simple orders have no other legs.
        take_profit (Optional[TakeProfitRequest]): For orders with multiple legs, an order to exit a profitable trade.
        stop_loss (Optional[StopLossRequest]): For orders with multiple legs, an order to exit a losing trade.
        stop_price (float): The price at which the stop order is converted to a market order or a stop limit
            order is converted to a limit order.
        limit_price (float): The worst fill price for a limit or stop limit order.
        commission (Optional[float]): The dollar value commission you want to charge the end user
    """

    commission: Optional[float] = None


class TrailingStopOrderRequest(BaseTrailingStopOrderRequest):
    """
    See base alpaca.trading.requests.TrailingStopOrderRequest model for more information.

    Attributes:
        symbol (str): The symbol identifier for the asset being traded
        qty (Optional[float]): The number of shares to trade. Fractional qty for stocks only with market orders.
        notional (Optional[float]): The base currency value of the shares to trade. For stocks, only works with MarketOrders.
            **Does not work with qty**.
        side (OrderSide): Whether the order will buy or sell the asset.
        type (OrderType): The execution logic type of the order (market, limit, etc).
        time_in_force (TimeInForce): The expiration logic of the order.
        extended_hours (Optional[float]): Whether the order can be executed during regular market hours.
        client_order_id (Optional[float]): A string to identify which client submitted the order.
        order_class (Optional[OrderClass]): The class of the order. Simple orders have no other legs.
        take_profit (Optional[TakeProfitRequest]): For orders with multiple legs, an order to exit a profitable trade.
        stop_loss (Optional[StopLossRequest]): For orders with multiple legs, an order to exit a losing trade.
        trail_price (Optional[float]): The absolute price difference by which the trailing stop will trail.
        trail_percent (Optional[float]): The percent price difference by which the trailing stop will trail.
        commission (Optional[float]): The dollar value commission you want to charge the end user.
    """

    commission: Optional[float] = None


class CancelOrderResponse(BaseCancelOrderResponse):
    """
    See base alpaca.trading.models.CancelOrderResponse model for more information.

    Attributes:
        body (Order): The order being cancelled.
    """

    body: Order


# ############################## Journals ################################# #


class CreateJournalRequest(NonEmptyRequest):
    """
    Data for request to initiate a single journal.

    Attributes:
        to_account (UUID): The account ID that received the journal.
        from_account (UUID): The account ID that initiates the journal.
        entry_type (JournalEntryType): Whether the journal is a cash or security journal.
        symbol (Optional[str]): For security journals, the symbol identifier of the security being journaled.
        qty (Optional[float]): For security journals, the quantity of the security being journaled.
        amount (Optional[float]): For cash journals, the total cash amount journaled in USD.
        description (Optional[str]): Journal description. It can include fixtures for sandbox API.
        transmitter_name (Optional[str]): For cash journals, travel rule related name info.
        transmitter_account_number (Optional[str]): For cash journals, travel rule account number info.
        transmitter_address (Optional[str]): For cash journals, travel rule related address info.
        transmitter_financial_institution (Optional[str]): For cash journals, travel rule related institution info.
        transmitter_timestamp (Optional[str]): For cash journals, travel rule related timestamp info.
    """

    from_account: UUID
    entry_type: JournalEntryType
    to_account: UUID
    amount: Optional[float] = None
    symbol: Optional[str] = None
    qty: Optional[float] = None
    description: Optional[str] = None
    transmitter_name: Optional[str] = None
    transmitter_account_number: Optional[str] = None
    transmitter_address: Optional[str] = None
    transmitter_financial_institution: Optional[str] = None
    transmitter_timestamp: Optional[str] = None
    currency: Optional[SupportedCurrencies] = None  # None = USD

    @model_validator(mode="before")
    def root_validator(cls, values: dict) -> dict:
        entry_type = values.get("entry_type")
        symbol = values.get("symbol")
        qty = values.get("qty")
        amount = values.get("amount")

        # amount is for cash journals, symbol and qty are for security journals
        # they are mutually exclusive
        if entry_type is not None and entry_type == JournalEntryType.CASH:
            if symbol or qty:
                raise ValueError("Symbol and qty are reserved for security journals.")

            if not amount:
                raise ValueError("Cash journals must contain an amount to transfer.")

        if entry_type is not None and entry_type == JournalEntryType.SECURITY:
            if amount:
                raise ValueError("Amount is reserved for cash journals.")

            if not symbol or not qty:
                raise ValueError(
                    "Security journals must contain a symbol and corresponding qty to transfer."
                )

        return values


class BatchJournalRequestEntry(NonEmptyRequest):
    """
    Entry in batch journal request.

    Attributes:
        to_account (UUID): Account to fund in batch journal request.
        amount (float): The cash amount in USD to fund by.
    """

    to_account: UUID
    amount: float


class ReverseBatchJournalRequestEntry(NonEmptyRequest):
    """
    Entry in reverse batch journal request.

    Attributes:
        to_account (UUID): Account to fund in batch journal request.
        amount (float): The cash amount in USD to fund by.
    """

    from_account: UUID
    amount: float


class CreateBatchJournalRequest(NonEmptyRequest):
    """
    This model represents the fields you can specify when creating
    a request of many Journals out of one account to many others at once.

    Currently, batch journals are only enabled on cash journals.

    Attributes:
        entry_type (JournalEntryType): The type of journal transfer.
        from_account (UUID): The originator of funds. Most likely is your Sweep Firm Account
        description (Optional[str]): Journal description, gets returned in the response.
        entries (List[BatchJournalRequestEntry]): List of journals to execute.
    """

    entry_type: JournalEntryType
    from_account: UUID
    description: Optional[str] = None
    entries: List[BatchJournalRequestEntry]


class CreateReverseBatchJournalRequest(NonEmptyRequest):
    """
    This model represents the fields you can specify when creating
    a request of many Journals into one account from many other accounts at once.

    Currently, reverse batch journals are only enabled on cash journals.

    Attributes:
        entry_type (JournalEntryType): The type of journal transfer.
        to_account (UUID): The destination of funds. Most likely is your Sweep Firm Account
        description (Optional[str]): Journal description, gets returned in the response.
        entries (List[BatchJournalRequestEntry]): List of journals to execute.
    """

    entry_type: JournalEntryType
    to_account: UUID
    description: Optional[str] = None
    entries: List[ReverseBatchJournalRequestEntry]


class GetJournalsRequest(NonEmptyRequest):
    """
    This model represents the fields you can specify when querying from the list of all journals.

    Attributes:
        after (Optional[date]): Journal creation dates after this date.
        before (Optional[date]): Journal creation dates before this date.
        status (Optional[JournalStatus]): Only journals with this status.
        entry_type (Optional[JournalEntryType]): Only journals with this entry type.
        to_account (Optional[UUID]): Only journals to this account.
        from_account (Optional[UUID]): Only journals from this account.
    """

    after: Optional[date] = None
    before: Optional[date] = None
    status: Optional[JournalStatus] = None
    entry_type: Optional[JournalEntryType] = None
    to_account: Optional[UUID] = None
    from_account: Optional[UUID] = None


class GetEventsRequest(NonEmptyRequest):
    id: Optional[str] = None
    since: Optional[Union[date, str]] = None
    until: Optional[Union[date, str]] = None
    since_id: Optional[int] = None
    until_id: Optional[int] = None
