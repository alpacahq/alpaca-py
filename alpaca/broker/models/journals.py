from datetime import date
from typing import Optional, List
from uuid import UUID

from pydantic import root_validator

from alpaca.broker.enums import JournalEntryType, JournalStatus
from alpaca.common.models import ValidateBaseModel as BaseModel, NonEmptyRequest


class Journal(BaseModel):
    """
    Represents a transfer of cash or securities from one account to another.

    There are two types of journals Cash Journals and Security Journals.

    **Travel Rule**
    In an effort to fight the criminal financial transactions, FinCEN enacted the
    Travel Rule that applies to fund transfers of more than $3,000.
    When you use Journal API to bundle a bulk of transfers for the end-users, you will need to tell about
    the breakdown and each transmitter information using the optional fields of the POST request.

    Learn more about journals here: https://alpaca.markets/docs/api-references/broker-api/journals/

    Attributes:
        id (UUID): The journal ID
        to_account (UUID): The account ID that received the journal.
        from_account (UUID): The account ID that initiates the journal.
        entry_type (JournalEntryType): Whether the journal is a cash or security journal.
        status (JournalStatus): The lifecycle status of the journal.
        symbol (Optional[str]): For security journals, the symbol identifier of the security being journaled.
        qty (Optional[float]): For security journals, the quantity of the security being journaled.
        price (Optional[float]): For security journals, the price at which the security is being journaled at.
        net_amount (Optional[float]): For cash journals, the total cash amount journaled
        description (Optional[str]): Journal description. It can include fixtures for sandbox API.
        settle_date (Optional[date]):
        system_date (Optional[date]):
        transmitter_name (Optional[str]): For cash journals, travel rule related name info.
        transmitter_account_number (Optional[str]): For cash journals, travel rule account number info.
        transmitter_address (Optional[str]): For cash journals, travel rule related address info.
        transmitter_financial_institution (Optional[str]): For cash journals, travel rule related institution info.
        transmitter_timestamp (Optional[str]): For cash journals, travel rule related timestamp info.
    """

    id: UUID
    to_account: UUID
    from_account: UUID
    entry_type: JournalEntryType
    status: JournalStatus
    net_amount: Optional[float]
    symbol: Optional[str]
    qty: Optional[float]
    price: Optional[float]
    description: Optional[str]
    settle_date: Optional[date]
    system_date: Optional[date]
    transmitter_name: Optional[str]
    transmitter_account_number: Optional[str]
    transmitter_address: Optional[str]
    transmitter_financial_institution: Optional[str]
    transmitter_timestamp: Optional[str]


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
    amount: Optional[float]
    symbol: Optional[str]
    qty: Optional[float]
    description: Optional[str]
    transmitter_name: Optional[str]
    transmitter_account_number: Optional[str]
    transmitter_address: Optional[str]
    transmitter_financial_institution: Optional[str]
    transmitter_timestamp: Optional[str]

    @root_validator()
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

        if entry_type is not None and entry_type == JournalEntryType.CASH:

            if amount:
                raise ValueError("Amount is reserved for cash journals.")

            if not symbol or not qty:
                raise ValueError(
                    "Security journals must contain a symbol and corresponding qty to transfer."
                )


class BatchJournalRequestEntry(NonEmptyRequest):
    """
    Entry in batch journal request.

    Attributes:
        to_account (UUID): Account to fund in batch journal request.
        amount (float): The cash amount in USD to fund by.
    """

    to_account: UUID
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
    description: Optional[str]
    entries: List[BatchJournalRequestEntry]


class ReverseBatchJournalRequestEntry(NonEmptyRequest):
    """
    Entry in reverse batch journal request.

    Attributes:
        to_account (UUID): Account to fund in batch journal request.
        amount (float): The cash amount in USD to fund by.
    """

    from_account: UUID
    amount: float


class CreateReverseBatchJournalRequest(NonEmptyRequest):
    """
    This model represents the fields you can specify when creating
    a request of many Journals into one account from many other accounts at once.

    Currently, reverse batch journals are only enabled on cash journals.

    Attributes:
        entry_type (JournalEntryType): The type of journal transfer.
        from_account (UUID): The originator of funds. Most likely is your Sweep Firm Account
        description (Optional[str]): Journal description, gets returned in the response.
        entries (List[BatchJournalRequestEntry]): List of journals to execute.
    """

    entry_type: JournalEntryType
    from_account: UUID
    description: Optional[str]
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

    after: Optional[date]
    before: Optional[date]
    status: Optional[JournalStatus]
    entry_type: Optional[JournalEntryType]
    to_account: Optional[UUID]
    from_account: Optional[UUID]


class BatchJournalResponse(Journal):
    """
    Represents a journal response from a batch journal request.

    Attributes:
        error_message (Optional[str]): An message that contains error details for failed journals.
    """

    error_message: Optional[str]
