from typing import List

from alpaca.broker.requests import (
    BatchJournalRequestEntry,
    ReverseBatchJournalRequestEntry,
)


def create_dummy_batch_journal_entries() -> List[BatchJournalRequestEntry]:
    entries = [
        BatchJournalRequestEntry(
            to_account="d7017fd9-60dd-425b-a09a-63ff59368b62", amount="10"
        ),
        BatchJournalRequestEntry(
            to_account="94fa473d-9a92-40cd-908c-25da9fba1e65", amount="100"
        ),
    ]

    return entries


def create_dummy_reverse_batch_journal_entries() -> (
    List[ReverseBatchJournalRequestEntry]
):
    entries = [
        ReverseBatchJournalRequestEntry(
            from_account="d7017fd9-60dd-425b-a09a-63ff59368b62", amount="10"
        ),
        ReverseBatchJournalRequestEntry(
            from_account="94fa473d-9a92-40cd-908c-25da9fba1e65", amount="100"
        ),
    ]

    return entries
