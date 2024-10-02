from datetime import datetime
from typing import List, Optional
from uuid import UUID
from alpaca.broker.enums import RunInitiatedBy, RunStatus

from alpaca.broker.requests import (
    CreatePortfolioRequest,
    CreateRunRequest,
    CreateSubscriptionRequest,
)
from alpaca.common.models import ValidateBaseModel as BaseModel
from alpaca.broker.models import Order


class Portfolio(CreatePortfolioRequest):
    """
    Portfolio response model.

    https://alpaca.markets/docs/api-references/broker-api/rebalancing/#portfolio-model
    """

    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime


class Subscription(CreateSubscriptionRequest):
    """
    Subscription response model.

    https://alpaca.markets/docs/api-references/broker-api/rebalancing/#subscription-model
    """

    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_rebalanced_at: Optional[datetime] = None


class RebalancingRun(CreateRunRequest):
    """
    Rebalancing run response model.

    https://alpaca.markets/docs/api-references/broker-api/rebalancing/#run-model
    """

    id: UUID
    portfolio_id: UUID
    initiated_by: Optional[RunInitiatedBy] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    canceled_at: Optional[datetime] = None
    status: RunStatus
    reason: Optional[str] = None
    orders: List[Order]
    failed_orders: Optional[List[Order]] = None
    skipped_orders: Optional[List[Order]] = None
