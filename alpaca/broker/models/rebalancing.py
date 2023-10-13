from datetime import datetime
from typing import List
from uuid import UUID

from alpaca.broker.requests import CreatePortfolioRequest


class Portfolio(CreatePortfolioRequest):
    """
    Portfolio response model.

    https://alpaca.markets/docs/api-references/broker-api/rebalancing/#portfolio-model
    """

    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
