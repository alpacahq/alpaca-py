"""A portfolio, a subscription, and a manual run, then everything is inactivated.

The portfolio name is unique to this run. The subscription and the run use only
the account this scenario creates. Inactivating is how a portfolio is retired:
the API has no delete.
"""

from __future__ import annotations

from typing import Any, Dict, List

from alpaca.broker.enums import (
    DriftBandSubType,
    PortfolioStatus,
    RebalancingConditionsType,
    RunType,
    WeightType,
)
from alpaca.broker.models import (
    Portfolio,
    RebalancingRun,
    RebalancingRunPage,
    Subscription,
    SubscriptionPage,
)
from alpaca.broker.requests import (
    CreatePortfolioRequest,
    CreateRunRequest,
    CreateSubscriptionRequest,
    GetPortfoliosRequest,
    GetRunsRequest,
    GetSubscriptionsRequest,
    RebalancingConditions,
    UpdatePortfolioRequest,
    Weight,
)
from alpaca.common.enums import PaginationType
from alpaca.common.exceptions import APIError

from . import Context, scenario
from ._broker import opened_account

BROKER = "broker"


def _weights() -> List[Weight]:
    return [
        Weight(type=WeightType.CASH, percent=5),
        Weight(type=WeightType.ASSET, symbol="SPY", percent=60),
        Weight(type=WeightType.ASSET, symbol="TLT", percent=35),
    ]


@scenario(
    covers=[
        "BrokerClient.create_portfolio",
        "BrokerClient.get_all_portfolios",
        "BrokerClient.get_portfolio_by_id",
        "BrokerClient.update_portfolio_by_id",
        "BrokerClient.inactivate_portfolio_by_id",
        "BrokerClient.create_subscription",
        "BrokerClient.get_subscriptions",
        "BrokerClient.get_all_subscriptions",
        "BrokerClient.get_subscription_by_id",
        "BrokerClient.unsubscribe_account",
        "BrokerClient.create_manual_run",
        "BrokerClient.get_runs",
        "BrokerClient.get_all_runs",
        "BrokerClient.get_run_by_id",
        "BrokerClient.cancel_run_by_id",
    ],
    credentials=BROKER,
)
def portfolio_subscription_and_run(ctx: Context) -> Dict[str, Any]:
    name = f"consumer-check-{ctx.unique_id('portfolio')[:12]}"
    portfolio = ctx.broker.create_portfolio(
        CreatePortfolioRequest(
            name=name,
            description="consumer-check portfolio",
            weights=_weights(),
            cooldown_days=7,
            rebalance_conditions=[
                RebalancingConditions(
                    type=RebalancingConditionsType.DRIFT_BAND,
                    sub_type=DriftBandSubType.ABSOLUTE,
                    percent=5,
                )
            ],
        )
    )
    assert isinstance(portfolio, Portfolio)
    subscription_id = None
    try:
        with opened_account(ctx, "rebalance") as session:
            session.wait_until_ready()
            account_id = session.account.id

            fetched = ctx.broker.get_portfolio_by_id(portfolio.id)
            assert isinstance(fetched, Portfolio)
            assert fetched.id == portfolio.id

            renamed = f"{name}-renamed"
            updated = ctx.broker.update_portfolio_by_id(
                portfolio.id,
                UpdatePortfolioRequest(name=renamed, cooldown_days=8),
            )
            assert isinstance(updated, Portfolio)
            assert updated.name == renamed

            # Filtered by the name we set, so other portfolios on the sandbox
            # are not part of the response.
            matches = ctx.broker.get_all_portfolios(GetPortfoliosRequest(name=renamed))
            assert isinstance(matches, list)
            # Every row must be ours, or the recording would hold other
            # portfolios on the sandbox.
            assert matches and all(
                isinstance(item, Portfolio) and item.id == portfolio.id
                for item in matches
            )

            subscription = ctx.broker.create_subscription(
                CreateSubscriptionRequest(
                    account_id=account_id, portfolio_id=portfolio.id
                )
            )
            assert isinstance(subscription, Subscription)
            subscription_id = subscription.id
            by_id = ctx.broker.get_subscription_by_id(subscription.id)
            assert isinstance(by_id, Subscription)
            assert by_id.id == subscription.id

            page = ctx.broker.get_subscriptions(
                GetSubscriptionsRequest(account_id=account_id, limit=10),
                handle_pagination=PaginationType.NONE,
            )
            assert isinstance(page, SubscriptionPage)
            assert page.subscriptions
            # account_id is scrubbed in recordings; compare the id we created.
            assert all(item.id == subscription.id for item in page.subscriptions)
            listed = ctx.broker.get_subscriptions(
                GetSubscriptionsRequest(account_id=account_id),
                max_items_limit=10,
            )
            deprecated = ctx.broker.get_all_subscriptions(
                GetSubscriptionsRequest(account_id=account_id),
                max_items_limit=10,
            )
            # Correspondent-wide endpoint filtered by a query parameter: every
            # row must be the subscription we created.
            for rows in (listed, deprecated):
                assert isinstance(rows, list) and rows
                assert all(
                    isinstance(item, Subscription) and item.id == subscription.id
                    for item in rows
                )

            run = ctx.broker.create_manual_run(
                CreateRunRequest(
                    account_id=account_id,
                    type=RunType.FULL_REBALANCE,
                    weights=_weights(),
                )
            )
            assert isinstance(run, RebalancingRun)
            run_by_id = ctx.broker.get_run_by_id(run.id)
            assert isinstance(run_by_id, RebalancingRun)
            assert run_by_id.id == run.id
            # A run that has already left the cancelable statuses returns 4xx.
            # Replay follows whichever response was recorded.
            try:
                ctx.broker.cancel_run_by_id(run.id)
                cancel_status = None
            except APIError as error:
                assert isinstance(error.status_code, int)
                assert 400 <= error.status_code < 500
                cancel_status = error.status_code

            runs = ctx.broker.get_runs(
                GetRunsRequest(account_id=account_id, limit=10),
                handle_pagination=PaginationType.NONE,
            )
            assert isinstance(runs, RebalancingRunPage)
            assert runs.runs
            assert all(item.id == run.id for item in runs.runs)
            all_runs = ctx.broker.get_all_runs(
                GetRunsRequest(account_id=account_id),
                max_items_limit=10,
            )
            assert isinstance(all_runs, list) and all_runs
            assert all(
                isinstance(item, RebalancingRun) and item.id == run.id
                for item in all_runs
            )

            ctx.broker.unsubscribe_account(subscription.id)
            subscription_id = None
    finally:
        # Inactivate fails while a subscription remains, including when the body
        # raised before unsubscribe.
        if subscription_id is not None:
            try:
                ctx.broker.unsubscribe_account(subscription_id)
            except APIError:
                pass
        ctx.broker.inactivate_portfolio_by_id(portfolio.id)

    inactive = ctx.broker.get_portfolio_by_id(portfolio.id)
    assert isinstance(inactive, Portfolio)
    assert inactive.status == PortfolioStatus.INACTIVE
    return {
        "updated": updated,
        "subscription": by_id,
        "run": run_by_id,
        "cancel_status": cancel_status,
        "inactive": inactive,
    }
