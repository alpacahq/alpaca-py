import pytest
from uuid import uuid4, UUID

from alpaca.broker.client import BrokerClient
from alpaca.common.enums import BaseURL
from tests.broker.factories import common as factory
from alpaca.broker.models import (
    CreateACHTransferRequest,
    CreateBankTransferRequest,
    CreateACHRelationshipRequest,
    CreateBankRequest,
    ACHRelationship,
    Bank,
    Transfer,
)
from alpaca.broker.enums import (
    TransferType,
    TransferDirection,
    TransferTiming,
    ACHRelationshipStatus,
    IdentifierType,
)


def test_create_ach_relationship_for_account(reqmock, client: BrokerClient):
    account_id = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"

    reqmock.post(
        f"{BaseURL.BROKER_SANDBOX}/v1/accounts/{account_id}/ach_relationships",
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
        f"{BaseURL.BROKER_SANDBOX}/v1/accounts/{account_id}/ach_relationships",
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
        f"{BaseURL.BROKER_SANDBOX}/v1/accounts/{account_id}/ach_relationships",
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
        f"{BaseURL.BROKER_SANDBOX}/v1/accounts/{account_id}/ach_relationships/{relationship_id}",
        status_code=204,
    )

    assert (
        client.delete_ach_relationship_for_account(account_id, relationship_id) is None
    )
    assert reqmock.called_once


def test_create_bank_for_account(reqmock, client: BrokerClient):
    account_id = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"

    reqmock.post(
        f"{BaseURL.BROKER_SANDBOX}/v1/accounts/{account_id}/recipient_banks",
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
        f"{BaseURL.BROKER_SANDBOX}/v1/accounts/{account_id}/recipient_banks",
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
        f"{BaseURL.BROKER_SANDBOX}/v1/accounts/{account_id}/recipient_banks/{bank_id}",
        status_code=204,
    )

    assert client.delete_bank_for_account(account_id, bank_id) is None
    assert reqmock.called_once


def test_create_transfer_for_account(reqmock, client: BrokerClient):
    account_id = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"

    reqmock.post(
        f"{BaseURL.BROKER_SANDBOX}/v1/accounts/{account_id}/transfers",
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


# def test_get_transfers_for_account(reqmock, client: BrokerClient):
#     account_id = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"
#
#     reqmock.get(
#         f"{BaseURL.BROKER_SANDBOX}/v1/accounts/{account_id}/transfers",
#         text="""
#         [
#             {
#               "id": "be3c368a-4c7c-4384-808e-f02c9f5a8afe",
#               "relationship_id": "0f08c6bc-8e9f-463d-a73f-fd047fdb5e94",
#               "account_id": "2a87c088-ffb6-472b-a4a3-cd9305c8605c",
#               "type": "ach",
#               "status": "COMPLETE",
#               "reason": null,
#               "amount": "498",
#               "direction": "INCOMING",
#               "created_at": "2021-05-05T07:55:31.190788Z",
#               "updated_at": "2021-05-05T08:13:33.029539Z",
#               "expires_at": "2021-05-12T07:55:31.190719Z",
#               "requested_amount": "500",
#               "fee": "2",
#               "fee_payment_method": "user"
#             }
#         ]
#         """,
#     )
#
#     transfers = client.get_transfers_for_account(account_id)
#
#     assert reqmock.called_once
#     assert isinstance(transfers, list)
#     assert isinstance(transfers[0], Transfer)


def test_cancel_transfer_for_account(reqmock, client: BrokerClient):
    account_id = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"
    transfer_id = "be3c368a-4c7c-4384-808e-f02c9f5a8afe"

    reqmock.delete(
        f"{BaseURL.BROKER_SANDBOX}/v1/accounts/{account_id}/transfers/{transfer_id}",
        status_code=204,
    )

    assert client.cancel_transfer_for_account(account_id, transfer_id) is None
    assert reqmock.called_once
