from datetime import datetime
from typing import List, Optional
from uuid import UUID

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
