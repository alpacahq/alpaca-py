from typing import List

import pytest

from alpaca.broker import BrokerClient
from alpaca.common.enums import BaseURL
from alpaca.common.models import CreateWatchlistRequest, Watchlist


def test_get_watchlists_for_account(reqmock, client: BrokerClient):
    account_id = "0d969814-40d6-4b2b-99ac-2e37427f1ad2"

    reqmock.get(
        f"{BaseURL.BROKER_SANDBOX}/v1/trading/accounts/{account_id}/watchlists",
        text="""
        [
          {
            "id": "7c3ac77f-894c-4c08-987f-18a2e43e8e2a",
            "account_id": "0d969814-40d6-4b2b-99ac-2e37427f1ad2",
            "created_at": "2022-05-20T16:17:30.159561Z",
            "updated_at": "2022-05-20T16:17:30.159561Z",
            "name": "test watchlist"
          }
        ]
        """,
    )

    result = client.get_watchlists_for_account(account_id=account_id)

    assert reqmock.called_once

    assert isinstance(result, List)
    assert len(result) == 1
    assert isinstance(result[0], Watchlist)


def test_get_watchlists_for_account_validates_account_id(reqmock, client: BrokerClient):
    with pytest.raises(ValueError):
        client.get_watchlists_for_account("not a uuid")


def test_get_watchlist_for_account_by_id(reqmock, client: BrokerClient):
    account_id = "0d969814-40d6-4b2b-99ac-2e37427f1ad2"
    watchlist_id = "7c3ac77f-894c-4c08-987f-18a2e43e8e2a"

    reqmock.get(
        f"{BaseURL.BROKER_SANDBOX}/v1/trading/accounts/{account_id}/watchlists/{watchlist_id}",
        text="""
{
  "id": "7c3ac77f-894c-4c08-987f-18a2e43e8e2a",
  "account_id": "0d969814-40d6-4b2b-99ac-2e37427f1ad2",
  "created_at": "2022-05-20T16:17:30.159561Z",
  "updated_at": "2022-05-20T16:17:30.159561Z",
  "name": "test watchlist",
  "assets": [
    {
      "id": "93f58d0b-6c53-432d-b8ce-2bad264dbd94",
      "class": "us_equity",
      "exchange": "NASDAQ",
      "symbol": "AAPL",
      "name": "Apple Inc. Common Stock",
      "status": "active",
      "tradable": true,
      "marginable": true,
      "shortable": true,
      "easy_to_borrow": true,
      "fractionable": true
    }
  ]
}
        """,
    )

    result = client.get_watchlist_for_account_by_id(
        account_id=account_id, watchlist_id=watchlist_id
    )

    assert reqmock.called_once

    assert isinstance(result, Watchlist)
    assert isinstance(result.assets, List)
    assert len(result.assets) == 1
    assert result.assets[0].symbol == "AAPL"


def test_get_watchlist_for_account_by_id_validates_uuid_params(
    reqmock, client: BrokerClient
):
    uuid = "7c3ac77f-894c-4c08-987f-18a2e43e8e2a"

    with pytest.raises(ValueError):
        client.get_watchlist_for_account_by_id(
            account_id=uuid,
            watchlist_id="not a uuid",
        )

    with pytest.raises(ValueError):
        client.get_watchlist_for_account_by_id(
            account_id="not a uuid",
            watchlist_id=uuid,
        )


def test_create_watchlist_for_account(reqmock, client: BrokerClient):
    account_id = "0d969814-40d6-4b2b-99ac-2e37427f1ad2"

    reqmock.post(
        f"{BaseURL.BROKER_SANDBOX}/v1/trading/accounts/{account_id}/watchlists",
        text="""
{
  "id": "7c3ac77f-894c-4c08-987f-18a2e43e8e2a",
  "account_id": "0d969814-40d6-4b2b-99ac-2e37427f1ad2",
  "created_at": "2022-05-20T16:17:30.159561Z",
  "updated_at": "2022-05-20T16:17:30.159561Z",
  "name": "test watchlist",
  "assets": [
    {
      "id": "93f58d0b-6c53-432d-b8ce-2bad264dbd94",
      "class": "us_equity",
      "exchange": "NASDAQ",
      "symbol": "AAPL",
      "name": "Apple Inc. Common Stock",
      "status": "active",
      "tradable": true,
      "marginable": true,
      "shortable": true,
      "easy_to_borrow": true,
      "fractionable": true
    }
  ]
}
        """,
    )

    name = "Test"
    symbols = ["AAPL"]

    result = client.create_watchlist_for_account(
        account_id=account_id,
        watchlist_data=CreateWatchlistRequest(name=name, symbols=symbols),
    )

    assert reqmock.called_once
    assert isinstance(result, Watchlist)

    request = reqmock.request_history[0]

    assert request.json() == {"name": name, "symbols": symbols}


def test_create_watchlist_for_account_validates_account_id(
    reqmock, client: BrokerClient
):
    with pytest.raises(ValueError):
        client.create_watchlist_for_account(
            account_id="not a uuid", watchlist_data=CreateWatchlistRequest()
        )
