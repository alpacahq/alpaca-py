from datetime import datetime
from typing import List

from alpaca.common.models import ValidateBaseModel as BaseModel
from alpaca.data.enums import MarketType


class ActiveStock(BaseModel):
    """
    Represent one asset that was a most active on the most actives endpoint.

    Attributes:
        symbol (str): Symbol of market moving asset.
        volume (float): Cumulative volume for the current trading day.
        trade_count (float): Cumulative trade count for the current trading day.
    """

    symbol: str
    volume: float
    trade_count: float


class MostActives(BaseModel):
    """
    Represent the response model for the MostActives endpoint.
    Attributes:
        most_actives (List[ActiveStock]): list of top N most active symbols.
        last_updated (datetime):
            Time when the MostActives were last computed.
            Formatted as a RFC 3339 formatted datetime with nanosecond precision.
    """

    most_actives: List[ActiveStock]
    last_updated: datetime


class Mover(BaseModel):
    """
    Represent one asset that was a top mover on the top market movers endpoint.
    Attributes:
        symbol (str): Symbol of market moving asset.
        percent_change (float): Percentage difference change for the day.
        change (float): Difference in change for the day.
        price (float): Current price of market moving asset.
    """

    symbol: str
    percent_change: float
    change: float
    price: float


class Movers(BaseModel):
    """
    Represent the response model for the top market movers endpoint.
    Attributes:
        gainers (List[Mover]): list of top N gainers.
        losers (List[Mover]): list of top N losers.
        market_type (MarketType): Market type (stocks or crypto).
        last_updated (datetime):
            Time when the movers were last computed.
            Formatted as a RFC 3339 formatted datetime with nanosecond precision.
    """

    gainers: List[Mover]
    losers: List[Mover]
    market_type: MarketType
    last_updated: datetime
