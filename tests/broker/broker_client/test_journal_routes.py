from uuid import UUID

from alpaca.broker.client import (
    BrokerClient,
)

from alpaca.broker.enums import JournalEntryType

from alpaca.broker.models import (
    Journal,
    BatchJournalResponse,
)

from alpaca.broker.requests import (
    CreateReverseBatchJournalRequest,
    GetJournalsRequest,
    CreateJournalRequest,
    CreateBatchJournalRequest,
)
from alpaca.common.enums import BaseURL, SupportedCurrencies

from ..factories import (
    create_dummy_batch_journal_entries,
    create_dummy_reverse_batch_journal_entries,
)


def test_create_journal(reqmock, client: BrokerClient):
    reqmock.post(
        f"{BaseURL.BROKER_SANDBOX}/v1/journals",
        text="""
               {
              "id": "a7a50677-2983-4c68-96dc-aff62fe3b8cf",
              "to_account": "a4c80770-edca-45bc-b35c-cfdf2ed46649",
              "entry_type": "JNLC",
              "status": "executed",
              "from_account": "ff7b9e35-90e7-453d-a410-b508e1971a36",
              "settle_date": "2020-12-24",
              "system_date": "2020-12-24",
              "net_amount": "115.5",
              "currency": "USD"
             }
            """,
    )

    request = CreateJournalRequest(
        to_account="a4c80770-edca-45bc-b35c-cfdf2ed46649",
        entry_type=JournalEntryType.CASH,
        from_account="ff7b9e35-90e7-453d-a410-b508e1971a36",
        amount=115.5,
    )

    response = client.create_journal(request)

    assert reqmock.called_once
    assert isinstance(response, Journal)
    assert response.to_account == UUID("a4c80770-edca-45bc-b35c-cfdf2ed46649")


def test_create_lct_journal(reqmock, client: BrokerClient):
    reqmock.post(
        f"{BaseURL.BROKER_SANDBOX}/v1/journals",
        text="""
               {
              "id": "a7a50677-2983-4c68-96dc-aff62fe3b8cf",
              "to_account": "a4c80770-edca-45bc-b35c-cfdf2ed46649",
              "entry_type": "JNLC",
              "status": "executed",
              "from_account": "ff7b9e35-90e7-453d-a410-b508e1971a36",
              "settle_date": "2020-12-24",
              "system_date": "2020-12-24",
              "net_amount": "115.5",
              "currency": "EUR"
             }
            """,
    )

    currency = SupportedCurrencies.EUR

    request = CreateJournalRequest(
        to_account="a4c80770-edca-45bc-b35c-cfdf2ed46649",
        entry_type=JournalEntryType.CASH,
        from_account="ff7b9e35-90e7-453d-a410-b508e1971a36",
        amount=115.5,
        currency=currency,
    )

    response = client.create_journal(request)

    assert reqmock.called_once
    assert isinstance(response, Journal)
    assert response.to_account == UUID("a4c80770-edca-45bc-b35c-cfdf2ed46649")
    assert response.currency == currency


def test_batch_journal(reqmock, client: BrokerClient):
    reqmock.post(
        f"{BaseURL.BROKER_SANDBOX}/v1/journals/batch",
        text="""
        [
          {
            "error_message": "",
            "id": "0a9152c4-d232-4b00-9102-5fa19aca40cb",
            "entry_type": "JNLC",
            "from_account": "8f8c8cee-2591-4f83-be12-82c659b5e748",
            "to_account": "d7017fd9-60dd-425b-a09a-63ff59368b62",
            "symbol": "",
            "qty": null,
            "price": null,
            "status": "pending",
            "settle_date": null,
            "system_date": null,
            "net_amount": "10",
            "description": "",
            "currency": "USD"
          },
          {
            "error_message": "",
            "id": "84379534-bcee-4c22-abe8-a4a6286dd100",
            "entry_type": "JNLC",
            "from_account": "8f8c8cee-2591-4f83-be12-82c659b5e748",
            "to_account": "94fa473d-9a92-40cd-908c-25da9fba1e65",
            "symbol": "",
            "qty": null,
            "price": null,
            "status": "pending",
            "settle_date": null,
            "system_date": null,
            "net_amount": "100",
            "description": "",
            "currency": "USD"
          }
        ]
            """,
    )

    response = client.create_batch_journal(
        CreateBatchJournalRequest(
            from_account="8f8c8cee-2591-4f83-be12-82c659b5e748",
            entry_type=JournalEntryType.CASH,
            entries=create_dummy_batch_journal_entries(),
        )
    )

    assert reqmock.called_once
    assert len(response) == 2
    assert isinstance(response[0], BatchJournalResponse)


def test_reverse_batch_journal(reqmock, client: BrokerClient):
    reqmock.post(
        f"{BaseURL.BROKER_SANDBOX}/v1/journals/reverse_batch",
        text="""
            [
              {
                "error_message": "",
                "id": "0a9152c4-d232-4b00-9102-5fa19aca40cb",
                "entry_type": "JNLC",
                "from_account": "94fa473d-9a92-40cd-908c-25da9fba1e65",
                "to_account": "d7017fd9-60dd-425b-a09a-63ff59368b62",
                "symbol": "",
                "qty": null,
                "price": null,
                "status": "pending",
                "settle_date": null,
                "system_date": null,
                "net_amount": "10",
                "description": "",
                "currency": "USD"
              },
              {
                "error_message": "",
                "id": "84379534-bcee-4c22-abe8-a4a6286dd100",
                "entry_type": "JNLC",
                "from_account": "8f8c8cee-2591-4f83-be12-82c659b5e748",
                "to_account": "d7017fd9-60dd-425b-a09a-63ff59368b62",
                "symbol": "",
                "qty": null,
                "price": null,
                "status": "pending",
                "settle_date": null,
                "system_date": null,
                "net_amount": "100",
                "description": "",
                "currency": "USD"
              }
            ]
                """,
    )

    response = client.create_reverse_batch_journal(
        CreateReverseBatchJournalRequest(
            to_account="d7017fd9-60dd-425b-a09a-63ff59368b62",
            entry_type=JournalEntryType.CASH,
            entries=create_dummy_reverse_batch_journal_entries(),
        )
    )

    assert reqmock.called_once
    assert len(response) == 2
    assert isinstance(response[0], BatchJournalResponse)


def test_get_journals(reqmock, client: BrokerClient):

    reqmock.get(
        f"{BaseURL.BROKER_SANDBOX}/v1/journals",
        text="""
            [
              {
                "id": "0a9152c4-d232-4b00-9102-5fa19aca40cb",
                "entry_type": "JNLC",
                "from_account": "94fa473d-9a92-40cd-908c-25da9fba1e65",
                "to_account": "d7017fd9-60dd-425b-a09a-63ff59368b62",
                "symbol": "",
                "qty": null,
                "price": null,
                "status": "pending",
                "settle_date": null,
                "system_date": null,
                "net_amount": "10",
                "description": "",
                "currency": "USD"
              },
              {
                "id": "84379534-bcee-4c22-abe8-a4a6286dd100",
                "entry_type": "JNLC",
                "from_account": "8f8c8cee-2591-4f83-be12-82c659b5e748",
                "to_account": "d7017fd9-60dd-425b-a09a-63ff59368b62",
                "symbol": "",
                "qty": null,
                "price": null,
                "status": "pending",
                "settle_date": null,
                "system_date": null,
                "net_amount": "100",
                "description": "",
                "currency": "USD"
              }
            ]
                """,
    )

    response = client.get_journals(journal_filter=GetJournalsRequest())

    assert reqmock.called_once
    assert len(response) > 0
    assert isinstance(response[0], Journal)


def test_get_journal_by_id(reqmock, client: BrokerClient):

    journal_id = "0a9152c4-d232-4b00-9102-5fa19aca40cb"

    reqmock.get(
        f"{BaseURL.BROKER_SANDBOX}/v1/journals/{journal_id}",
        text="""
              {
                "id": "0a9152c4-d232-4b00-9102-5fa19aca40cb",
                "entry_type": "JNLC",
                "from_account": "94fa473d-9a92-40cd-908c-25da9fba1e65",
                "to_account": "d7017fd9-60dd-425b-a09a-63ff59368b62",
                "symbol": "",
                "qty": null,
                "price": null,
                "status": "pending",
                "settle_date": null,
                "system_date": null,
                "net_amount": "10",
                "description": ""
              }
                """,
    )

    response = client.get_journal_by_id(journal_id=journal_id)

    assert reqmock.called_once
    assert isinstance(response, Journal)
    assert response.id == UUID(journal_id)


def test_get_journal_by_id(reqmock, client: BrokerClient):

    journal_id = "0a9152c4-d232-4b00-9102-5fa19aca40cb"

    reqmock.delete(
        f"{BaseURL.BROKER_SANDBOX}/v1/journals/{journal_id}", status_code=204
    )

    client.cancel_journal_by_id(journal_id=journal_id)

    assert reqmock.called_once
