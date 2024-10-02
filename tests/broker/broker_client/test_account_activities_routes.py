from datetime import datetime
from typing import Iterator, List

import pytest
from requests_mock import Mocker

from alpaca.broker.client import BrokerClient, PaginationType
from alpaca.broker.requests import (
    GetAccountActivitiesRequest,
)
from alpaca.common.enums import BaseURL
from alpaca.trading.models import (
    BaseActivity,
    NonTradeActivity,
    TradeActivity,
)


def setup_reqmock_for_paginated_account_activities_response(reqmock: Mocker):
    resp_one = """
    [
      {
        "id": "20220419000000000::fd84741b-59c5-4ddd-a303-69f70eb7753f",
        "account_id": "aba134b6-217d-4fd2-b460-e3c80bbfb9b4",
        "activity_type": "CSD",
        "date": "2022-04-19",
        "net_amount": "33324.35",
        "description": "",
        "status": "executed"
      },
      {
        "id": "20220419000000000::fb876acb-76b0-405c-8c7f-96a1c171ec5c",
        "account_id": "673272aa-2aa7-484b-9d5b-dd2bd19e9bca",
        "activity_type": "CSD",
        "date": "2022-04-19",
        "net_amount": "29161.91",
        "description": "",
        "status": "executed"
      },
      {
        "id": "20220304095318500::092cd749-b783-49cb-a36e-4d8666be201f",
        "account_id": "6e8cb861-e8b9-4278-8ed2-c8452535a165",
        "activity_type": "FILL",
        "transaction_time": "2022-03-04T14:53:18.500245Z",
        "type": "fill",
        "price": "2630.95",
        "qty": "9",
        "side": "buy",
        "symbol": "GOOGL",
        "leaves_qty": "0",
        "order_id": "b677e464-c2d0-4fdd-a4b1-8830b386aa50",
        "cum_qty": "10.177047834",
        "order_status": "filled"
      },
      {
        "id": "20220419000000000::f77b60bf-ea39-4551-a3d6-000548e6f11c",
        "account_id": "6188a8e4-4551-4c00-9387-fcb38ff8eef3",
        "activity_type": "CSD",
        "date": "2022-04-19",
        "net_amount": "45850.47",
        "description": "",
        "status": "executed"
      }
    ]
    """
    resp_two = """
    [
      {
        "id": "20220419000000000::ed22fc4d-897c-474b-876a-b492d40f83d2",
        "account_id": "e1bade5e-7988-4449-8791-86d47d721d19",
        "activity_type": "CSD",
        "date": "2022-04-19",
        "net_amount": "43864.18",
        "description": "",
        "status": "executed"
      },
      {
        "id": "20220419000000000::ec75b06d-1d29-4d1e-9143-c7e59aa842bc",
        "account_id": "a3f59eac-7c03-42b2-a336-d078b3671308",
        "activity_type": "CSD",
        "date": "2022-04-19",
        "net_amount": "32155.97",
        "description": "",
        "status": "executed"
      },
      {
        "id": "20220419000000000::ec624f60-ca70-42d6-9086-f47a1eeebeb7",
        "account_id": "34f33a89-390d-4001-aced-a5e978864b8d",
        "activity_type": "CSD",
        "date": "2022-04-19",
        "net_amount": "20979.69",
        "description": "",
        "status": "executed"
      },
      {
        "id": "20220419000000000::e96b84c0-15b8-4821-9c78-cce1d836ff5b",
        "account_id": "f78eb5ae-76c0-48ef-b5d9-07613da2e827",
        "activity_type": "CSD",
        "date": "2022-04-19",
        "net_amount": "22386.64",
        "description": "",
        "status": "executed"
      }
    ]
    """

    reqmock.get(
        BaseURL.BROKER_SANDBOX.value + "/v1/accounts/activities",
        [{"text": resp_one}, {"text": resp_two}, {"text": """[]"""}],
    )


def test_get_activities_for_account_default_asserts(reqmock, client: BrokerClient):
    setup_reqmock_for_paginated_account_activities_response(reqmock)

    result = client.get_account_activities(GetAccountActivitiesRequest())

    assert reqmock.call_count == 3
    assert isinstance(result, List)
    assert len(result) == 8
    assert isinstance(result[0], NonTradeActivity)
    assert isinstance(result[2], TradeActivity)

    # verify we asked for the correct ids when paginating
    assert reqmock.request_history[1].qs == {
        "page_token": ["20220419000000000::f77b60bf-ea39-4551-a3d6-000548e6f11c"]
    }
    assert reqmock.request_history[2].qs == {
        "page_token": ["20220419000000000::e96b84c0-15b8-4821-9c78-cce1d836ff5b"]
    }


def test_get_activities_for_account_full_pagination(reqmock, client: BrokerClient):
    setup_reqmock_for_paginated_account_activities_response(reqmock)

    result = client.get_account_activities(
        GetAccountActivitiesRequest(), handle_pagination=PaginationType.FULL
    )

    assert reqmock.call_count == 3
    assert isinstance(result, List)
    assert len(result) == 8
    assert isinstance(result[0], NonTradeActivity)
    assert isinstance(result[2], TradeActivity)


def test_get_activities_for_account_max_items_and_single_request_date(
    reqmock,
    client: BrokerClient,
):
    """
    The api when `date` is specified is allowed to drop the pagination defaults and return all results at once.
    This test is to ensure in this case if there is a max items requested that we still only request
    that max items amount.
    """

    # Note we purposly have this returning more than requested, the api currently respects paging even in this state
    # but we should still be able to handle the case where it doesn't, so we don't go over max items
    reqmock.get(
        BaseURL.BROKER_SANDBOX.value + "/v1/accounts/activities",
        text="""
        [
          {
            "id": "20220304135420903::047e252a-a8a3-4e35-84e2-29814cbf5057",
            "account_id": "3dcb795c-3ccc-402a-abb9-07e26a1b1326",
            "activity_type": "FILL",
            "transaction_time": "2022-03-04T18:54:20.903569Z",
            "type": "partial_fill",
            "price": "2907.15",
            "qty": "1.792161878",
            "side": "buy",
            "symbol": "AMZN",
            "leaves_qty": "1",
            "order_id": "cddf433b-1a41-497d-ae31-50b1fee56fff",
            "cum_qty": "1.792161878",
            "order_status": "partially_filled"
          },
          {
            "id": "20220304135420898::2b9e8979-48b4-4b70-9ba0-008210b76ebf",
            "account_id": "3dcb795c-3ccc-402a-abb9-07e26a1b1326",
            "activity_type": "FILL",
            "transaction_time": "2022-03-04T18:54:20.89822Z",
            "type": "fill",
            "price": "2907.15",
            "qty": "1",
            "side": "buy",
            "symbol": "AMZN",
            "leaves_qty": "0",
            "order_id": "cddf433b-1a41-497d-ae31-50b1fee56fff",
            "cum_qty": "2.792161878",
            "order_status": "filled"
          },
          {
            "id": "20220304123922801::3b8a937c-b1d9-4ebe-ae94-5e0b52c3f350",
            "account_id": "3dcb795c-3ccc-402a-abb9-07e26a1b1326",
            "activity_type": "FILL",
            "transaction_time": "2022-03-04T17:39:22.801228Z",
            "type": "fill",
            "price": "2644.84",
            "qty": "0.058773239",
            "side": "sell",
            "symbol": "GOOGL",
            "leaves_qty": "0",
            "order_id": "642695e3-def7-4637-9525-2e7f698ebfc7",
            "cum_qty": "0.058773239",
            "order_status": "filled"
          },
          {
            "id": "20220304123922310::b53b6d71-a644-4be1-9f88-39d1c8d29831",
            "account_id": "3dcb795c-3ccc-402a-abb9-07e26a1b1326",
            "activity_type": "FILL",
            "transaction_time": "2022-03-04T17:39:22.310917Z",
            "type": "partial_fill",
            "price": "837.45",
            "qty": "1.998065556",
            "side": "sell",
            "symbol": "TSLA",
            "leaves_qty": "4",
            "order_id": "5f4a07dc-6503-4cbf-902a-8c6608401d97",
            "cum_qty": "1.998065556",
            "order_status": "partially_filled"
          },
          {
            "id": "20220304123922305::bc84b8a8-8758-42aa-be3b-618d097c2867",
            "account_id": "3dcb795c-3ccc-402a-abb9-07e26a1b1326",
            "activity_type": "FILL",
            "transaction_time": "2022-03-04T17:39:22.305629Z",
            "type": "fill",
            "price": "837.45",
            "qty": "4",
            "side": "sell",
            "symbol": "TSLA",
            "leaves_qty": "0",
            "order_id": "5f4a07dc-6503-4cbf-902a-8c6608401d97",
            "cum_qty": "5.998065556",
            "order_status": "filled"
          }
        ]
        """,
    )

    max_limit = 2
    date_str = "2022-03-04"

    result = client.get_account_activities(
        GetAccountActivitiesRequest(date=datetime.strptime(date_str, "%Y-%m-%d")),
        handle_pagination=PaginationType.FULL,
        max_items_limit=max_limit,
    )

    assert reqmock.call_count == 1
    assert isinstance(result, List)
    assert len(result) == max_limit

    request = reqmock.request_history[0]
    assert "date" in request.qs and request.qs["date"] == [f"{date_str}t00:00:00+00:00"]
    assert "page_size" in request.qs and request.qs["page_size"] == ["2"]


def test_get_activities_for_account_full_pagination_and_max_items(
    reqmock,
    client: BrokerClient,
):
    # Note in this test we'll still have the api return too many results in the response just to validate that
    # we respect max limit regardless of what the api does
    setup_reqmock_for_paginated_account_activities_response(reqmock)

    max_limit = 5

    result = client.get_account_activities(
        GetAccountActivitiesRequest(),
        handle_pagination=PaginationType.FULL,
        max_items_limit=max_limit,
    )

    assert reqmock.call_count == 2
    assert isinstance(result, List)
    assert len(result) == max_limit

    # First limit is irrelevant since we hardcode returning 4 anyway, but second request needs to only request 1 item
    second_request = reqmock.request_history[1]
    assert "page_size" in second_request.qs and second_request.qs["page_size"] == ["1"]


def test_get_activities_for_account_none_pagination(reqmock, client: BrokerClient):
    setup_reqmock_for_paginated_account_activities_response(reqmock)

    result = client.get_account_activities(
        GetAccountActivitiesRequest(), handle_pagination=PaginationType.NONE
    )

    assert reqmock.call_count == 1
    assert isinstance(result, List)
    assert len(result) == 4
    assert isinstance(result[0], BaseActivity)


def test_get_account_activities_iterator_pagination(reqmock, client: BrokerClient):
    setup_reqmock_for_paginated_account_activities_response(reqmock)

    generator = client.get_account_activities(
        GetAccountActivitiesRequest(), handle_pagination=PaginationType.ITERATOR
    )

    assert isinstance(generator, Iterator)

    # When asking for an iterator we should not have made any requests yet
    assert not reqmock.called

    results = next(generator)

    assert isinstance(results, List)
    assert len(results) == 4
    assert isinstance(results[0], BaseActivity)
    assert reqmock.called_once

    results = next(generator)
    assert isinstance(results, List)
    assert len(results) == 4

    # generator should now be empty
    results = next(generator, None)
    assert reqmock.call_count == 3

    assert results is None


def test_get_account_activities_validates_max_items(reqmock, client: BrokerClient):
    with pytest.raises(ValueError) as e:
        client.get_account_activities(
            GetAccountActivitiesRequest(),
            max_items_limit=45,
            handle_pagination=PaginationType.ITERATOR,
        )

    assert "max_items_limit can only be specified for PaginationType.FULL" in str(
        e.value
    )
