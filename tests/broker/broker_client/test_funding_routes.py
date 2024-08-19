from typing import Iterator
from uuid import UUID

from alpaca.broker.client import BrokerClient
from alpaca.broker.enums import (
    ACHRelationshipStatus,
    IdentifierType,
    TransferDirection,
    TransferTiming,
)
from alpaca.broker.models import (
    ACHRelationship,
    Bank,
    Transfer,
)

from alpaca.broker.requests import (
    CreateACHRelationshipRequest,
    CreateACHTransferRequest,
    CreateBankRequest,
    GetTransfersRequest,
)

from alpaca.common.enums import BaseURL, PaginationType


def test_create_ach_relationship_for_account(reqmock, client: BrokerClient):
    account_id = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"

    reqmock.post(
        f"{BaseURL.BROKER_SANDBOX.value}/v1/accounts/{account_id}/ach_relationships",
        text="""
        {
            "id": "15ef9978-cb1e-4872-9565-bd0a720b8b76",
            "account_id": "2a87c088-ffb6-472b-a4a3-cd9305c8605c",
            "created_at": "2022-04-14T15:51:14.523349Z",
            "updated_at": "2022-04-14T15:51:14.523349Z",
            "status": "QUEUED",
            "account_owner_name": "John Doe",
            "bank_account_type": "SAVINGS",
            "bank_account_number": "123456789abc",
            "bank_routing_number": "123456789"
        }
        """,
    )

    ach_data = CreateACHRelationshipRequest(
        account_owner_name="John Doe",
        bank_account_type="SAVINGS",
        bank_account_number="123456789abc",
        bank_routing_number="123456789",
    )
    ach_relationship = client.create_ach_relationship_for_account(account_id, ach_data)

    assert reqmock.called_once
    assert isinstance(ach_relationship, ACHRelationship)
    assert ach_relationship.account_id == UUID(account_id)


def test_get_ach_relationships_for_account(reqmock, client: BrokerClient):
    account_id = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"

    reqmock.get(
        f"{BaseURL.BROKER_SANDBOX.value}/v1/accounts/{account_id}/ach_relationships",
        text="""
        [
            {
                "id": "15ef9978-cb1e-4872-9565-bd0a720b8b76",
                "account_id": "2a87c088-ffb6-472b-a4a3-cd9305c8605c",
                "created_at": "2022-04-14T15:51:14.523349Z",
                "updated_at": "2022-04-14T15:51:14.523349Z",
                "status": "QUEUED",
                "account_owner_name": "John Doe",
                "bank_account_type": "SAVINGS",
                "bank_account_number": "123456789abc",
                "bank_routing_number": "123456789"
            }
        ]
        """,
    )

    ach_relationships = client.get_ach_relationships_for_account(account_id)

    assert reqmock.called_once
    assert isinstance(ach_relationships, list)
    assert isinstance(ach_relationships[0], ACHRelationship)


def test_get_ach_relationships_for_account_with_statuses(reqmock, client: BrokerClient):
    account_id = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"

    reqmock.get(
        f"{BaseURL.BROKER_SANDBOX.value}/v1/accounts/{account_id}/ach_relationships",
        text="""
        [
            {
                "id": "15ef9978-cb1e-4872-9565-bd0a720b8b76",
                "account_id": "2a87c088-ffb6-472b-a4a3-cd9305c8605c",
                "created_at": "2022-04-14T15:51:14.523349Z",
                "updated_at": "2022-04-14T15:51:14.523349Z",
                "status": "QUEUED",
                "account_owner_name": "John Doe",
                "bank_account_type": "SAVINGS",
                "bank_account_number": "123456789abc",
                "bank_routing_number": "123456789"
            }
        ]
        """,
    )

    statuses = [
        ACHRelationshipStatus.QUEUED,
        ACHRelationshipStatus.APPROVED,
        ACHRelationshipStatus.PENDING,
    ]
    ach_relationships = client.get_ach_relationships_for_account(account_id, statuses)

    assert reqmock.called_once
    assert isinstance(ach_relationships, list)
    assert isinstance(ach_relationships[0], ACHRelationship)

    assert reqmock.request_history[0].qs == {"statuses": [",".join(statuses).lower()]}


def test_delete_ach_relationship_for_account(reqmock, client: BrokerClient):
    account_id = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"
    relationship_id = "15ef9978-cb1e-4872-9565-bd0a720b8b76"

    reqmock.delete(
        f"{BaseURL.BROKER_SANDBOX.value}/v1/accounts/{account_id}/ach_relationships/{relationship_id}",
        status_code=204,
    )

    assert (
        client.delete_ach_relationship_for_account(account_id, relationship_id) is None
    )
    assert reqmock.called_once


def test_create_bank_for_account(reqmock, client: BrokerClient):
    account_id = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"

    reqmock.post(
        f"{BaseURL.BROKER_SANDBOX.value}/v1/accounts/{account_id}/recipient_banks",
        text="""
        {
          "id": "9a7fb9b5-1f4d-420f-b6d4-0fd32008cec8",
          "account_id": "2a87c088-ffb6-472b-a4a3-cd9305c8605c",
          "name": "my bank detail",
          "status": "QUEUED",
          "country": "",
          "state_province": "",
          "postal_code": "",
          "city": "",
          "street_address": "",
          "account_number": "123456789abc",
          "bank_code": "123456789",
          "bank_code_type": "ABA",
          "created_at": "2021-01-09T12:14:18.683915267Z",
          "updated_at": "2021-01-09T12:14:18.683915267Z"
        }
        """,
    )

    bank_data = CreateBankRequest(
        name="my bank detail",
        bank_code_type=IdentifierType.ABA,
        bank_code="123456789",
        account_number="123456789abc",
    )

    bank_relationship = client.create_bank_for_account(account_id, bank_data)

    assert reqmock.called_once
    assert isinstance(bank_relationship, Bank)
    assert bank_relationship.account_id == UUID(account_id)


def test_get_banks_for_account(reqmock, client: BrokerClient):
    account_id = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"

    reqmock.get(
        f"{BaseURL.BROKER_SANDBOX.value}/v1/accounts/{account_id}/recipient_banks",
        text="""
        [
            {
              "id": "9a7fb9b5-1f4d-420f-b6d4-0fd32008cec8",
              "account_id": "2a87c088-ffb6-472b-a4a3-cd9305c8605c",
              "name": "my bank detail",
              "status": "QUEUED",
              "country": "",
              "state_province": "",
              "postal_code": "",
              "city": "",
              "street_address": "",
              "account_number": "123456789abc",
              "bank_code": "123456789",
              "bank_code_type": "ABA",
              "created_at": "2021-01-09T12:14:18.683915267Z",
              "updated_at": "2021-01-09T12:14:18.683915267Z"
            }
        ]
        """,
    )

    banks = client.get_banks_for_account(account_id)

    assert reqmock.called_once
    assert isinstance(banks, list)
    assert isinstance(banks[0], Bank)


def test_delete_bank_for_account(reqmock, client: BrokerClient):
    account_id = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"
    bank_id = "15ef9978-cb1e-4872-9565-bd0a720b8b76"

    reqmock.delete(
        f"{BaseURL.BROKER_SANDBOX.value}/v1/accounts/{account_id}/recipient_banks/{bank_id}",
        status_code=204,
    )

    assert client.delete_bank_for_account(account_id, bank_id) is None
    assert reqmock.called_once


def test_create_transfer_for_account(reqmock, client: BrokerClient):
    account_id = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"

    reqmock.post(
        f"{BaseURL.BROKER_SANDBOX.value}/v1/accounts/{account_id}/transfers",
        text="""
        {
          "id": "be3c368a-4c7c-4384-808e-f02c9f5a8afe",
          "relationship_id": "0f08c6bc-8e9f-463d-a73f-fd047fdb5e94",
          "account_id": "2a87c088-ffb6-472b-a4a3-cd9305c8605c",
          "type": "ach",
          "status": "COMPLETE",
          "reason": null,
          "amount": "498",
          "direction": "INCOMING",
          "created_at": "2021-05-05T07:55:31.190788Z",
          "updated_at": "2021-05-05T08:13:33.029539Z",
          "expires_at": "2021-05-12T07:55:31.190719Z",
          "requested_amount": "500",
          "fee": "2",
          "fee_payment_method": "user"
        }
        """,
    )

    transfer_data = CreateACHTransferRequest(
        relationship_id="0f08c6bc-8e9f-463d-a73f-fd047fdb5e94",
        amount="100.0",
        direction=TransferDirection.INCOMING,
        timing=TransferTiming.IMMEDIATE,
    )

    transfer_entity = client.create_transfer_for_account(account_id, transfer_data)

    assert reqmock.called_once
    assert isinstance(transfer_entity, Transfer)
    assert transfer_entity.account_id == UUID(account_id)


def setup_reqmock_for_paginated_transfers_response(account_id, reqmock):
    resp_one = """
    [
        {
          "id": "bf438b6d-4ea3-4241-9e1c-a0e55b47f4e0",
          "account_id": "2d6cab28-c5d1-4ff8-91c6-b6404a9ee114",
          "type": "wire",
          "status": "CANCELED",
          "currency": "USD",
          "amount": "100",
          "instant_amount": "0",
          "direction": "INCOMING",
          "created_at": "2024-07-15T13:40:01.963459Z",
          "updated_at": "2024-07-22T08:22:29.990176Z",
          "reason": null,
          "hold_until": null,
          "requested_amount": "100",
          "fee": "0",
          "fee_payment_method": "user"
        },
        {
          "id": "786b0a11-cdbf-4c0b-b146-6cdbcb94f2d3",
          "relationship_id": "0f08c6bc-8e9f-463d-a73f-fd047fdb5e94",
          "account_id": "2a87c088-ffb6-472b-a4a3-cd9305c8605c",
          "type": "ach",
          "status": "COMPLETE",
          "reason": null,
          "amount": "692.0",
          "direction": "OUTGOING",
          "created_at": "2021-05-05T07:55:31.190788Z",
          "updated_at": "2021-05-05T08:13:33.029539Z",
          "expires_at": "2021-05-12T07:55:31.190719Z",
          "requested_amount": "695.0",
          "fee": "3",
          "fee_payment_method": "user"
        },
        {
          "id": "574bb1af-05ba-49d7-a716-001ba5c84269",
          "relationship_id": "0f08c6bc-8e9f-463d-a73f-fd047fdb5e94",
          "account_id": "2a87c088-ffb6-472b-a4a3-cd9305c8605c",
          "type": "ach",
          "status": "COMPLETE",
          "reason": "reason reason reason",
          "amount": "3921.23",
          "direction": "INCOMING",
          "created_at": "2021-05-05T07:55:31.190788Z",
          "updated_at": "2021-05-05T08:13:33.029539Z",
          "expires_at": "2021-05-12T07:55:31.190719Z",
          "requested_amount": "3923.23",
          "fee": "2",
          "fee_payment_method": "user"
        }
    ]
    """

    resp_two = """
    [
        {
          "id": "87d1fb30-4fab-4af1-a770-d1936ec24eca",
          "relationship_id": "0f08c6bc-8e9f-463d-a73f-fd047fdb5e94",
          "account_id": "2a87c088-ffb6-472b-a4a3-cd9305c8605c",
          "type": "ach",
          "status": "COMPLETE",
          "reason": null,
          "amount": "498",
          "direction": "INCOMING",
          "created_at": "2021-05-05T07:55:31.190788Z",
          "updated_at": "2021-05-05T08:13:33.029539Z",
          "expires_at": "2021-05-12T07:55:31.190719Z",
          "requested_amount": "500",
          "fee": "2",
          "fee_payment_method": "user"
        },
        {
          "id": "99224cf2-afe4-4a7f-8244-c17d61b19512",
          "relationship_id": "0f08c6bc-8e9f-463d-a73f-fd047fdb5e94",
          "account_id": "2a87c088-ffb6-472b-a4a3-cd9305c8605c",
          "type": "ach",
          "status": "COMPLETE",
          "reason": null,
          "amount": "692.0",
          "direction": "OUTGOING",
          "created_at": "2021-05-05T07:55:31.190788Z",
          "updated_at": "2021-05-05T08:13:33.029539Z",
          "expires_at": "2021-05-12T07:55:31.190719Z",
          "requested_amount": "695.0",
          "fee": "3",
          "fee_payment_method": "user"
        },
        {
          "id": "e45b6b24-4e63-467e-9674-3527643a3767",
          "relationship_id": "0f08c6bc-8e9f-463d-a73f-fd047fdb5e94",
          "account_id": "2a87c088-ffb6-472b-a4a3-cd9305c8605c",
          "type": "ach",
          "status": "COMPLETE",
          "reason": "reason reason reason",
          "amount": "3921.23",
          "direction": "INCOMING",
          "created_at": "2021-05-05T07:55:31.190788Z",
          "updated_at": "2021-05-05T08:13:33.029539Z",
          "expires_at": "2021-05-12T07:55:31.190719Z",
          "requested_amount": "3923.23",
          "fee": "2",
          "fee_payment_method": "user"
        }
    ]
    """

    reqmock.get(
        f"{BaseURL.BROKER_SANDBOX.value}/v1/accounts/{account_id}/transfers",
        [{"text": resp_one}, {"text": resp_two}, {"text": """[]"""}],
    )


def test_get_transfers_for_account_default_pagination(reqmock, client: BrokerClient):
    account_id = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"
    setup_reqmock_for_paginated_transfers_response(account_id, reqmock)

    transfers = client.get_transfers_for_account(account_id)

    assert reqmock.call_count == 3
    assert isinstance(transfers, list)
    assert len(transfers) == 6
    assert all(isinstance(transfer, Transfer) for transfer in transfers)

    assert reqmock.request_history[0].qs == {"offset": ["0"]}
    assert reqmock.request_history[1].qs == {"offset": ["3"]}
    assert reqmock.request_history[2].qs == {"offset": ["6"]}


def test_get_transfers_for_account_full_pagination(reqmock, client: BrokerClient):
    account_id = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"
    setup_reqmock_for_paginated_transfers_response(account_id, reqmock)

    transfers = client.get_transfers_for_account(
        account_id, handle_pagination=PaginationType.FULL
    )

    assert reqmock.call_count == 3
    assert isinstance(transfers, list)
    assert len(transfers) == 6
    assert isinstance(transfers[0], Transfer)


def test_get_transfers_for_account_full_pagination_and_max_items(
    reqmock, client: BrokerClient
):
    account_id = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"
    max_items = 2
    setup_reqmock_for_paginated_transfers_response(account_id, reqmock)

    transfers = client.get_transfers_for_account(
        account_id, max_items_limit=max_items, handle_pagination=PaginationType.FULL
    )

    assert reqmock.call_count == 1
    assert isinstance(transfers, list)
    assert len(transfers) == max_items
    assert isinstance(transfers[0], Transfer)


def test_get_transfers_for_account_none_pagination(reqmock, client: BrokerClient):
    account_id = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"
    setup_reqmock_for_paginated_transfers_response(account_id, reqmock)

    transfers = client.get_transfers_for_account(
        account_id, handle_pagination=PaginationType.NONE
    )

    assert reqmock.call_count == 1
    assert isinstance(transfers, list)
    assert len(transfers) == 3
    assert isinstance(transfers[0], Transfer)


def test_get_transfers_for_account_iterator_pagination(reqmock, client: BrokerClient):
    account_id = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"
    setup_reqmock_for_paginated_transfers_response(account_id, reqmock)

    generator = client.get_transfers_for_account(
        account_id, handle_pagination=PaginationType.ITERATOR
    )

    assert isinstance(generator, Iterator)

    # When asking for an iterator we should not have made any requests yet.
    assert not reqmock.called

    transfers = next(generator)

    assert isinstance(transfers, list)
    assert len(transfers) == 3
    assert isinstance(transfers[0], Transfer)
    assert reqmock.called_once

    transfers = next(generator)
    assert isinstance(transfers, list)
    assert len(transfers) == 3

    # Generator should now be empty.
    transfers = next(generator, None)
    assert reqmock.call_count == 3

    assert transfers is None


def test_get_transfers_for_account_direction_filter_and_full_pagination(
    reqmock, client: BrokerClient
):
    account_id = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"
    setup_reqmock_for_paginated_transfers_response(account_id, reqmock)

    transfers_filter = GetTransfersRequest(direction=TransferDirection.INCOMING)

    transfers = client.get_transfers_for_account(
        account_id, transfers_filter, handle_pagination=PaginationType.FULL
    )

    assert reqmock.call_count == 3
    assert isinstance(transfers, list)
    assert len(transfers) == 6

    for request in reqmock.request_history:
        assert "direction" in request.qs and request.qs["direction"] == ["incoming"]


def test_cancel_transfer_for_account(reqmock, client: BrokerClient):
    account_id = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"
    transfer_id = "be3c368a-4c7c-4384-808e-f02c9f5a8afe"

    reqmock.delete(
        f"{BaseURL.BROKER_SANDBOX.value}/v1/accounts/{account_id}/transfers/{transfer_id}",
        status_code=204,
    )

    assert client.cancel_transfer_for_account(account_id, transfer_id) is None
    assert reqmock.called_once
