from datetime import date
from typing import Optional
from uuid import UUID

from alpaca.broker.enums import JournalEntryType, JournalStatus
from alpaca.common.models import ModelWithID
from alpaca.common.enums import SupportedCurrencies


class Journal(ModelWithID):
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

    to_account: UUID
    from_account: UUID
    entry_type: JournalEntryType
    status: JournalStatus
    net_amount: Optional[float] = None
    symbol: Optional[str] = None
    qty: Optional[float] = None
    price: Optional[float] = None
    description: Optional[str] = None
    settle_date: Optional[date] = None
    system_date: Optional[date] = None
    transmitter_name: Optional[str] = None
    transmitter_account_number: Optional[str] = None
    transmitter_address: Optional[str] = None
    transmitter_financial_institution: Optional[str] = None
    transmitter_timestamp: Optional[str] = None
    currency: SupportedCurrencies


class BatchJournalResponse(Journal):
    """
    Represents a journal response from a batch journal request.

    Attributes:
        error_message (Optional[str]): An message that contains error details for failed journals.
    """

    error_message: Optional[str] = None
