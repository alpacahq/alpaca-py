from uuid import UUID
from .models import ValidateBaseModel as BaseModel
from datetime import datetime
from .trading import Asset
from typing import List


class Watchlist(BaseModel):
    """
    A watchlist is an ordered list of assets. An account can have multiple watchlists.
    Learn more about watchlists in the documentation. https://alpaca.markets/docs/api-references/trading-api/watchlist/

    Attributes:
        account_id (UUID): The uuid identifying the account the watchlist belongs to
        id (UUID): The unique identifier for the watchlist
        name (str): An arbitrary string up to 64 characters identifying the watchlist
        created_at (datetime): When the watchlist was created
        updated_at (datetime): When the watchlist was last updated
        assets (List[Asset]): The assets in the watchlist
    """

    account_id: UUID
    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime
    assets: List[Asset]
