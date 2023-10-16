from datetime import datetime
from typing import Optional
from uuid import UUID

from alpaca.broker.requests import CreatePortfolioRequest, CreateSubscriptionRequest


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
