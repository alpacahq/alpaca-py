from uuid import UUID

from requests_mock import Mocker

from alpaca.broker.client import BrokerClient
from alpaca.broker.enums import WeightType
from alpaca.broker.models import Portfolio, RebalancingRun, Subscription
from alpaca.broker.requests import (
    CreatePortfolioRequest,
    CreateRunRequest,
    CreateSubscriptionRequest,
    GetPortfoliosRequest,
    GetRunsRequest,
    GetSubscriptionsRequest,
    UpdatePortfolioRequest,
)
from alpaca.common.enums import BaseURL


def test_create_portfolio(reqmock: Mocker, client: BrokerClient) -> None:
    """Test to create a portfolio."""
    reqmock.post(
        f"{BaseURL.BROKER_SANDBOX.value}/v1/rebalancing/portfolios",
        text="""
        {
            "id": "6819ecd2-db92-4688-821d-8fac2a8f4744",
            "name": "Balanced",
            "description": "A balanced portfolio of stocks and bonds",
            "status": "active",
            "cooldown_days": 7,
            "created_at": "2022-08-06T19:12:13.555858187-04:00",
            "updated_at": "2022-08-06T19:12:13.628551899-04:00",
            "weights": [
                {
                    "type": "cash",
                    "symbol": null,
                    "percent": "5"
                },
                {
                    "type": "asset",
                    "symbol": "SPY",
                    "percent": "60"
                },
                {
                    "type": "asset",
                    "symbol": "TLT",
                    "percent": "35"
                }
            ],
            "rebalance_conditions": [
                {
                    "type": "drift_band",
                    "sub_type": "absolute",
                    "percent": "5",
                    "day": null
                },
                {
                    "type": "drift_band",
                    "sub_type": "relative",
                    "percent": "20",
                    "day": null
                }
            ]
        }
        """,
    )

    portfolio_request = CreatePortfolioRequest(
        **{
            "name": "Balanced",
            "description": "A balanced portfolio of stocks and bonds",
            "weights": [
                {"type": "cash", "percent": "5"},
                {"type": "asset", "symbol": "SPY", "percent": "60"},
                {"type": "asset", "symbol": "TLT", "percent": "35"},
            ],
            "cooldown_days": 7,
            "rebalance_conditions": [
                {"type": "drift_band", "sub_type": "absolute", "percent": "5"},
                {"type": "drift_band", "sub_type": "relative", "percent": "20"},
            ],
        }
    )
    ptf = client.create_portfolio(portfolio_request)

    assert reqmock.called_once
    assert isinstance(ptf, Portfolio)


def test_get_all_portfolios(reqmock: Mocker, client: BrokerClient) -> None:
    """Test the get_all_portfolios method."""
    reqmock.get(
        f"{BaseURL.BROKER_SANDBOX.value}/v1/rebalancing/portfolios",
        text="""
        [
    {
        "id": "57d4ec79-9658-4916-9eb1-7c672be97e3e",
        "name": "My Portfolio",
        "description": "Some description",
        "status": "active",
        "cooldown_days": 2,
        "created_at": "2022-07-28T20:33:59.665962Z",
        "updated_at": "2022-07-28T20:33:59.786528Z",
        "weights": [
            {
                "type": "asset",
                "symbol": "AAPL",
                "percent": "35"
            },
            {
                "type": "asset",
                "symbol": "TSLA",
                "percent": "20"
            },
            {
                "type": "asset",
                "symbol": "SPY",
                "percent": "45"
            }
        ],
        "rebalance_conditions": [
            {
                "type": "drift_band",
                "sub_type": "absolute",
                "percent": "5",
                "day": null
            },
            {
                "type": "drift_band",
                "sub_type": "relative",
                "percent": "20",
                "day": null
            }
        ]
    },
    {
        "id": "6819ecd2-db92-4688-821d-8fac2a8f4744",
        "name": "Balanced",
        "description": "A balanced portfolio of stocks and bonds",
        "status": "active",
        "cooldown_days": 7,
        "created_at": "2022-08-06T23:12:13.555858Z",
        "updated_at": "2022-08-06T23:12:13.628551Z",
        "weights": [
            {
                "type": "cash",
                "symbol": null,
                "percent": "5"
            },
            {
                "type": "asset",
                "symbol": "SPY",
                "percent": "60"
            },
            {
                "type": "asset",
                "symbol": "TLT",
                "percent": "35"
            }
        ],
        "rebalance_conditions": [
            {
                "type": "drift_band",
                "sub_type": "absolute",
                "percent": "5",
                "day": null
            },
            {
                "type": "drift_band",
                "sub_type": "relative",
                "percent": "20",
                "day": null
            }
        ]
    },
    {
        "id": "2d49d00e-ab1c-4014-89d8-70c5f64df2fc",
        "name": "Balanced Two",
        "description": "A balanced portfolio of stocks and bonds",
        "status": "active",
        "cooldown_days": 7,
        "created_at": "2022-08-07T18:56:45.116867Z",
        "updated_at": "2022-08-07T18:56:45.196857Z",
        "weights": [
            {
                "type": "cash",
                "symbol": null,
                "percent": "5"
            },
            {
                "type": "asset",
                "symbol": "SPY",
                "percent": "60"
            },
            {
                "type": "asset",
                "symbol": "TLT",
                "percent": "35"
            }
        ],
        "rebalance_conditions": [
            {
                "type": "drift_band",
                "sub_type": "absolute",
                "percent": "5",
                "day": null
            },
            {
                "type": "drift_band",
                "sub_type": "relative",
                "percent": "20",
                "day": null
            }
        ]
    }
]
        """,
    )
    response = client.get_all_portfolios(filter=GetPortfoliosRequest())

    assert reqmock.called_once
    assert len(response) > 0
    assert isinstance(response[0], Portfolio)


def test_get_portfolio_by_id(reqmock: Mocker, client: BrokerClient) -> None:
    """Test the get_portfolio_by_id method."""
    ptf_id = UUID("57d4ec79-9658-4916-9eb1-7c672be97e3e")
    reqmock.get(
        f"{BaseURL.BROKER_SANDBOX.value}/v1/rebalancing/portfolios/{ptf_id}",
        text="""
            {
                "id": "57d4ec79-9658-4916-9eb1-7c672be97e3e",
                "name": "My Portfolio",
                "description": "Some description",
                "status": "active",
                "cooldown_days": 2,
                "created_at": "2022-07-28T20:33:59.665962Z",
                "updated_at": "2022-07-28T20:33:59.786528Z",
                "weights": [
                    {
                        "type": "asset",
                        "symbol": "AAPL",
                        "percent": "35"
                    },
                    {
                        "type": "asset",
                        "symbol": "TSLA",
                        "percent": "20"
                    },
                    {
                        "type": "asset",
                        "symbol": "SPY",
                        "percent": "45"
                    }
                ],
                "rebalance_conditions": [
                    {
                        "type": "drift_band",
                        "sub_type": "absolute",
                        "percent": "5",
                        "day": null
                    },
                    {
                        "type": "drift_band",
                        "sub_type": "relative",
                        "percent": "20",
                        "day": null
                    }
                ]
            }
    """,
    )
    response = client.get_portfolio_by_id(portfolio_id=ptf_id)

    assert reqmock.called_once
    assert isinstance(response, Portfolio)
    assert response.id == ptf_id


def test_update_portfolio_by_id(reqmock: Mocker, client: BrokerClient) -> None:
    """Test the update_portfolio_by_id method."""
    ptf_id = UUID("57d4ec79-9658-4916-9eb1-7c672be97e3e")
    reqmock.patch(
        f"{BaseURL.BROKER_SANDBOX.value}/v1/rebalancing/portfolios/{ptf_id}",
        text="""
            {
                "id": "57d4ec79-9658-4916-9eb1-7c672be97e3e",
                "name": "My Portfolio",
                "description": "Some description",
                "status": "active",
                "cooldown_days": 2,
                "created_at": "2022-07-28T20:33:59.665962Z",
                "updated_at": "2022-07-28T20:33:59.786528Z",
                "weights": [
                    {
                        "type": "cash",
                        "percent": "10"
                    },
                    {
                        "type": "asset",
                        "symbol": "GOOG",
                        "percent": "90"
                    }
                ],
                "rebalance_conditions": [
                    {
                        "type": "drift_band",
                        "sub_type": "absolute",
                        "percent": "5",
                        "day": null
                    },
                    {
                        "type": "drift_band",
                        "sub_type": "relative",
                        "percent": "20",
                        "day": null
                    }
                ]
            }
    """,
    )
    response = client.update_portfolio_by_id(
        portfolio_id=ptf_id,
        update_request=UpdatePortfolioRequest(
            **{
                "weights": [
                    {"type": "cash", "percent": "10"},
                    {"type": "asset", "symbol": "GOOG", "percent": "90"},
                ]
            }
        ),
    )

    assert reqmock.called_once
    assert isinstance(response, Portfolio)
    assert response.id == ptf_id
    assert response.weights[0].type == WeightType.CASH
    assert response.weights[0].percent == 10
    assert response.weights[1].type == WeightType.ASSET
    assert response.weights[1].percent == 90


def test_inactivate_portfolio_by_id(reqmock: Mocker, client: BrokerClient) -> None:
    """Test the inactivate_portfolio_by_id method."""
    ptf_id = UUID("57d4ec79-9658-4916-9eb1-7c672be97e3e")
    reqmock.delete(f"{BaseURL.BROKER_SANDBOX.value}/v1/rebalancing/portfolios/{ptf_id}")
    client.inactivate_portfolio_by_id(
        portfolio_id=ptf_id,
    )
    assert reqmock.called_once


def test_create_subscription(reqmock: Mocker, client: BrokerClient) -> None:
    """Test to create a portfolio subscription."""
    reqmock.post(
        f"{BaseURL.BROKER_SANDBOX.value}/v1/rebalancing/subscriptions",
        text="""
            {
                "id": "2ded098b-ee17-4f48-9496-f8b66e3627aa",
                "account_id": "bf2b0f93-f296-4276-a9cf-288586cf4fb7",
                "portfolio_id": "57d4ec79-9658-4916-9eb1-7c672be97e3e",
                "last_rebalanced_at": null,
                "created_at": "2022-08-06T19:34:43.428080852-04:00"
            }
        """,
    )
    subscription_request = CreateSubscriptionRequest(
        **{
            "account_id": "bf2b0f93-f296-4276-a9cf-288586cf4fb7",
            "portfolio_id": "57d4ec79-9658-4916-9eb1-7c672be97e3e",
        }
    )
    subscription = client.create_subscription(subscription_request)

    assert reqmock.called_once
    assert isinstance(subscription, Subscription)


def test_get_all_subscriptions(reqmock: Mocker, client: BrokerClient) -> None:
    """Test the get_all_subscriptions method."""
    reqmock.get(
        f"{BaseURL.BROKER_SANDBOX.value}/v1/rebalancing/subscriptions",
        text="""
        {
    "subscriptions": [
        {
            "id": "9341be15-8786-4d23-ba1a-fc10ef4f90f4",
            "account_id": "bf2b0f93-f296-4276-a9cf-288586cf4fb7",
            "portfolio_id": "57d4ec79-9658-4916-9eb1-7c672be97e3e",
            "last_rebalanced_at": null,
            "created_at": "2022-08-07T23:52:05.942964Z"
        }
    ],
    "next_page_token": null
}
        """,
    )
    response = client.get_all_subscriptions(filter=GetSubscriptionsRequest())

    assert reqmock.called_once
    assert len(response) > 0
    assert isinstance(response[0], Subscription)


def test_get_subscription_by_id(reqmock: Mocker, client: BrokerClient) -> None:
    """Test the get_subscription_by_id method."""
    sub_id = UUID("9341be15-8786-4d23-ba1a-fc10ef4f90f4")
    reqmock.get(
        f"{BaseURL.BROKER_SANDBOX.value}/v1/rebalancing/subscriptions/{sub_id}",
        text="""
        {
            "id": "9341be15-8786-4d23-ba1a-fc10ef4f90f4",
            "account_id": "bf2b0f93-f296-4276-a9cf-288586cf4fb7",
            "portfolio_id": "57d4ec79-9658-4916-9eb1-7c672be97e3e",
            "last_rebalanced_at": null,
            "created_at": "2022-08-07T23:52:05.942964Z"
        }
        """,
    )
    response = client.get_subscription_by_id(subscription_id=sub_id)

    assert reqmock.called_once
    assert isinstance(response, Subscription)
    assert response.id == sub_id


def test_unsubscribe_account(reqmock: Mocker, client: BrokerClient) -> None:
    """Test the unsubscribe_account method."""
    sub_id = UUID("9341be15-8786-4d23-ba1a-fc10ef4f90f4")
    reqmock.delete(
        f"{BaseURL.BROKER_SANDBOX.value}/v1/rebalancing/subscriptions/{sub_id}"
    )
    client.unsubscribe_account(
        subscription_id=sub_id,
    )
    assert reqmock.called_once


def test_create_manual_run(reqmock: Mocker, client: BrokerClient) -> None:
    """Test to create a portfolio subscription."""
    reqmock.post(
        f"{BaseURL.BROKER_SANDBOX.value}/v1/rebalancing/runs",
        text="""
            {
                "id": "b4f32f6f-f8b3-4f8e-9b36-30b560000bfa",
                "type": "full_rebalance",
                "amount": null,
                "initiated_from": "api",
                "status": "QUEUED",
                "reason": null,
                "account_id": "bf2b0f93-f296-4276-a9cf-288586cf4fb7",
                "portfolio_id": "448ba7b3-2fda-4d8e-ac9f-61ff2aa36c60",
                "weights": [
                    {
                        "type": "asset",
                        "symbol": "AAPL",
                        "percent": "35"
                    },
                    {
                        "type": "asset",
                        "symbol": "TSLA",
                        "percent": "20"
                    },
                    {
                        "type": "asset",
                        "symbol": "SPY",
                        "percent": "45"
                    }
                ],
                "orders": [],
                "completed_at": null,
                "canceled_at": null,
                "created_at": "2023-10-17T10:16:55.582507Z",
                "updated_at": "2023-10-17T10:16:55.582507Z"
            }
        """,
    )
    run_req = CreateRunRequest(
        **{
            "account_id": "bf2b0f93-f296-4276-a9cf-288586cf4fb7",
            "type": "full_rebalance",
            "weights": [
                {"type": "asset", "symbol": "AAPL", "percent": "35"},
                {"type": "asset", "symbol": "TSLA", "percent": "20"},
                {"type": "asset", "symbol": "SPY", "percent": "45"},
            ],
        }
    )
    run_resp = client.create_manual_run(run_req)

    assert reqmock.called_once
    assert isinstance(run_resp, RebalancingRun)


def test_get_all_runs(reqmock: Mocker, client: BrokerClient) -> None:
    """Test the get_all_runs method."""
    reqmock.get(
        f"{BaseURL.BROKER_SANDBOX.value}/v1/rebalancing/runs",
        response_list=[
            {
                "text": """
                        {
                "runs": [
                    {
                        "id": "2ad28f83-796c-4c4d-895e-d360aeb95297",
                        "type": "full_rebalance",
                        "amount": null,
                        "initiated_from": "system",
                        "status": "CANCELED",
                        "reason": "create OMS order: create closed order exceeded max retries: order not a filled state",
                        "account_id": "cf175fbc-ca19-4741-88ed-70d6c133f8d7",
                        "portfolio_id": "ac89fa84-e3bb-48ff-9b81-d5f313e77463",
                        "weights": [
                            {
                                "type": "cash",
                                "symbol": null,
                                "percent": "5"
                            },
                            {
                                "type": "asset",
                                "symbol": "SPY",
                                "percent": "60"
                            },
                            {
                                "type": "asset",
                                "symbol": "TLT",
                                "percent": "35"
                            }
                        ],
                        "orders": [],
                        "completed_at": null,
                        "canceled_at": null,
                        "created_at": "2022-04-14T10:46:08.045817Z",
                        "updated_at": "2022-04-14T13:11:07.84719Z"
                    }
                ],
                "next_page_token": 1
            }
            """
            },
            {
                "text": """
                        {
                "runs": [
                    {
                        "id": "2ad28f83-796c-4c4d-895e-d360aeb95297",
                        "type": "full_rebalance",
                        "amount": null,
                        "initiated_from": "system",
                        "status": "CANCELED",
                        "reason": "create OMS order: create closed order exceeded max retries: order not a filled state",
                        "account_id": "cf175fbc-ca19-4741-88ed-70d6c133f8d7",
                        "portfolio_id": "ac89fa84-e3bb-48ff-9b81-d5f313e77463",
                        "weights": [
                            {
                                "type": "cash",
                                "symbol": null,
                                "percent": "5"
                            },
                            {
                                "type": "asset",
                                "symbol": "SPY",
                                "percent": "60"
                            },
                            {
                                "type": "asset",
                                "symbol": "TLT",
                                "percent": "35"
                            }
                        ],
                        "orders": [],
                        "skipped_orders": [
                            {
                                "symbol": "SPY",
                                "side": "buy",
                                "notional": "0",
                                "currency": "USD",
                                "reason": "ORDER_LESS_THAN_MIN_NOTIONAL",
                                "reason_details": "order notional value ($0) is less than min-notional set for correspondent ($1)"
                            }
                        ],
                        "completed_at": null,
                        "canceled_at": null,
                        "created_at": "2022-04-14T10:46:08.045817Z",
                        "updated_at": "2022-04-14T13:11:07.84719Z"
                    }
                ],
                "next_page_token": null
            }
            """
            },
        ],
    )
    response = client.get_all_runs(filter=GetRunsRequest())

    assert reqmock.call_count == 2
    assert len(response) == 2
    assert isinstance(response[0], RebalancingRun)


def test_get_run_by_id(reqmock: Mocker, client: BrokerClient) -> None:
    """Test the get_run_by_id method."""
    run_id = UUID("2ad28f83-796c-4c4d-895e-d360aeb95297")
    reqmock.get(
        f"{BaseURL.BROKER_SANDBOX.value}/v1/rebalancing/runs/{run_id}",
        text="""
        {
                        "id": "2ad28f83-796c-4c4d-895e-d360aeb95297",
                        "type": "full_rebalance",
                        "amount": null,
                        "initiated_from": "system",
                        "status": "CANCELED",
                        "reason": "create OMS order: create closed order exceeded max retries: order not a filled state",
                        "account_id": "cf175fbc-ca19-4741-88ed-70d6c133f8d7",
                        "portfolio_id": "ac89fa84-e3bb-48ff-9b81-d5f313e77463",
                        "weights": [
                            {
                                "type": "cash",
                                "symbol": null,
                                "percent": "5"
                            },
                            {
                                "type": "asset",
                                "symbol": "SPY",
                                "percent": "60"
                            },
                            {
                                "type": "asset",
                                "symbol": "TLT",
                                "percent": "35"
                            }
                        ],
                        "orders": [],
                        "skipped_orders": [
                            {
                                "symbol": "SPY",
                                "side": "buy",
                                "notional": "0",
                                "currency": "USD",
                                "reason": "ORDER_LESS_THAN_MIN_NOTIONAL",
                                "reason_details": "order notional value ($0) is less than min-notional set for correspondent ($1)"
                            }
                        ],
                        "completed_at": null,
                        "canceled_at": null,
                        "created_at": "2022-04-14T10:46:08.045817Z",
                        "updated_at": "2022-04-14T13:11:07.84719Z"
                    }
        """,
    )
    response = client.get_run_by_id(run_id=run_id)

    assert reqmock.called_once
    assert isinstance(response, RebalancingRun)
    assert response.id == run_id


def test_cancel_run_by_id(reqmock: Mocker, client: BrokerClient) -> None:
    """Test the cancel_run_by_id method."""
    run_id = UUID("9341be15-8786-4d23-ba1a-fc10ef4f90f4")
    reqmock.delete(f"{BaseURL.BROKER_SANDBOX.value}/v1/rebalancing/runs/{run_id}")
    client.cancel_run_by_id(run_id=run_id)
    assert reqmock.called_once
