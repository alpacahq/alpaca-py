"""Cash journals between two accounts this scenario creates, funds, and closes.

Amounts stay on those two accounts. There is no firm or sweep account in the
request, so a journal cannot move another customer's cash.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict

from alpaca.broker.enums import JournalEntryType, JournalStatus
from alpaca.broker.models import BatchJournalResponse, Journal
from alpaca.broker.requests import (
    BatchJournalRequestEntry,
    CreateBatchJournalRequest,
    CreateJournalRequest,
    CreateReverseBatchJournalRequest,
    GetJournalsRequest,
    ReverseBatchJournalRequestEntry,
)
from alpaca.common.exceptions import APIError

from . import Context, scenario
from ._broker import fund_with_ach, opened_account, wait_for_buying_power

BROKER = "broker"
DONE = (
    JournalStatus.EXECUTED,
    JournalStatus.CORRECT,
    JournalStatus.REJECTED,
    JournalStatus.CANCELED,
    JournalStatus.REFUSED,
)


def _wait(ctx: Context, journal_id: Any, attempts: int = 15) -> Journal:
    last: Journal
    for _ in range(attempts):
        fetched = ctx.broker.get_journal_by_id(journal_id)
        assert isinstance(fetched, Journal)
        last = fetched
        if fetched.status in DONE:
            return fetched
        ctx.sleep(1)
    return last


@scenario(
    covers=[
        "BrokerClient.create_journal",
        "BrokerClient.create_batch_journal",
        "BrokerClient.create_reverse_batch_journal",
        "BrokerClient.get_journals",
        "BrokerClient.get_journal_by_id",
        "BrokerClient.cancel_journal_by_id",
    ],
    credentials=BROKER,
)
def cash_journal_between_two_accounts(ctx: Context) -> Dict[str, Any]:
    with opened_account(ctx, "journal-from") as source, opened_account(
        ctx, "journal-to"
    ) as dest:
        source.wait_until_ready()
        dest.wait_until_ready()
        relationship, _transfer = fund_with_ach(ctx, source.account.id, amount="100")
        try:
            wait_for_buying_power(ctx, source.account.id, minimum="20")

            journal = ctx.broker.create_journal(
                CreateJournalRequest(
                    from_account=source.account.id,
                    to_account=dest.account.id,
                    entry_type=JournalEntryType.CASH,
                    amount=10,
                    description="consumer-check",
                )
            )
            assert isinstance(journal, Journal)
            assert journal.from_account == source.account.id
            assert journal.to_account == dest.account.id
            settled = _wait(ctx, journal.id)

            # A second, small journal is what we try to cancel. Sandbox often
            # executes it before cancel is accepted; either result is recorded.
            cancel_target = ctx.broker.create_journal(
                CreateJournalRequest(
                    from_account=source.account.id,
                    to_account=dest.account.id,
                    entry_type=JournalEntryType.CASH,
                    amount=1,
                    description="consumer-check-cancel",
                )
            )
            assert isinstance(cancel_target, Journal)
            try:
                ctx.broker.cancel_journal_by_id(cancel_target.id)
                cancel_status = None
            except APIError as error:
                assert isinstance(error.status_code, int)
                assert 400 <= error.status_code < 500
                cancel_status = error.status_code

            batch = ctx.broker.create_batch_journal(
                CreateBatchJournalRequest(
                    entry_type=JournalEntryType.CASH,
                    from_account=source.account.id,
                    entries=[
                        BatchJournalRequestEntry(
                            to_account=dest.account.id,
                            amount="1",
                            description="consumer-check-batch",
                        )
                    ],
                )
            )
            assert isinstance(batch, list)
            assert batch and isinstance(batch[0], BatchJournalResponse)

            reverse = ctx.broker.create_reverse_batch_journal(
                CreateReverseBatchJournalRequest(
                    entry_type=JournalEntryType.CASH,
                    to_account=source.account.id,
                    entries=[
                        ReverseBatchJournalRequestEntry(
                            from_account=dest.account.id,
                            amount="1",
                            description="consumer-check-reverse",
                        )
                    ],
                )
            )
            assert isinstance(reverse, list)
            assert reverse and isinstance(reverse[0], BatchJournalResponse)

            found = ctx.broker.get_journals(
                GetJournalsRequest(
                    after=date(2020, 1, 1),
                    before=date(2030, 1, 1),
                    entry_type=JournalEntryType.CASH,
                    from_account=source.account.id,
                    to_account=dest.account.id,
                    limit=10,
                )
            )
            assert isinstance(found, list)
            assert any(item.id == journal.id for item in found)
            # GET /journals is correspondent-wide. Every row must be between our
            # two accounts, or the recording would hold other customers' journals.
            assert all(
                item.from_account == source.account.id
                and item.to_account == dest.account.id
                for item in found
            )
        finally:
            ctx.broker.delete_ach_relationship_for_account(
                source.account.id, relationship.id
            )

    return {
        "journal_status": settled.status,
        "cancel_status": cancel_status,
        "batch_status": batch[0].status,
        "reverse_status": reverse[0].status,
    }
