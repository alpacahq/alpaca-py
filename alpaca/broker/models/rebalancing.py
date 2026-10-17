from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import Field, field_validator

from alpaca.broker.enums import PortfolioStatus, RunInitiatedFrom, RunStatus, RunType
from alpaca.broker.models import Order
from alpaca.broker.requests import RebalancingConditions, Weight
from alpaca.common.models import ValidateBaseModel as BaseModel


class Portfolio(BaseModel):
    """
    Portfolio response model.

    https://docs.alpaca.markets/reference/get-v1-rebalancing-portfolios
    """

    id: UUID
    name: str
    description: str
    status: PortfolioStatus
    cooldown_days: int
    created_at: datetime
    updated_at: datetime
    weights: List[Weight]
    rebalance_conditions: Optional[List[RebalancingConditions]] = None


class Subscription(BaseModel):
    """
    Subscription response model.

    https://docs.alpaca.markets/reference/get-v1-rebalancing-subscriptions-1
    """

    id: UUID
    account_id: UUID
    portfolio_id: UUID
    created_at: datetime
    last_rebalanced_at: Optional[datetime] = None


class SubscriptionPage(BaseModel):
    """
    One page from the list-subscriptions endpoint.

    ``BrokerClient.get_subscriptions`` returns this when ``handle_pagination``
    is ``PaginationType.NONE``. The token is how a caller requests the next page.
    An empty body or ``"subscriptions": null`` is an empty page.

    https://docs.alpaca.markets/reference/get-v1-rebalancing-subscriptions-1
    """

    subscriptions: List[Subscription] = Field(default_factory=list)
    next_page_token: Optional[str] = None

    @field_validator("subscriptions", mode="before")
    @classmethod
    def _null_as_empty(cls, value):
        return [] if value is None else value


class SkippedOrder(BaseModel):
    """
    Skipped order response model.

    https://docs.alpaca.markets/reference/get-v1-rebalancing-runs-run_id-1
    """

    symbol: str
    side: Optional[str] = None
    notional: Optional[str] = None
    currency: Optional[str] = None
    reason: str
    reason_details: str


class RebalancingRun(BaseModel):
    """
    Rebalancing run response model.

    https://docs.alpaca.markets/reference/get-v1-rebalancing-runs
    """

    id: UUID
    account_id: UUID
    type: RunType
    amount: Optional[str] = None
    portfolio_id: UUID
    weights: List[Weight]
    initiated_from: Optional[RunInitiatedFrom] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    canceled_at: Optional[datetime] = None
    status: RunStatus
    reason: Optional[str] = None
    orders: Optional[List[Order]] = None
    failed_orders: Optional[List[Order]] = None
    skipped_orders: Optional[List[SkippedOrder]] = None


class RebalancingRunPage(BaseModel):
    """
    One page from the list-runs endpoint.

    ``BrokerClient.get_runs`` returns this when ``handle_pagination`` is
    ``PaginationType.NONE``. The token is how a caller requests the next page.
    An empty body or ``"runs": null`` is an empty page.

    https://docs.alpaca.markets/reference/get-v1-rebalancing-runs
    """

    runs: List[RebalancingRun] = Field(default_factory=list)
    next_page_token: Optional[str] = None

    @field_validator("runs", mode="before")
    @classmethod
    def _null_as_empty(cls, value):
        return [] if value is None else value
