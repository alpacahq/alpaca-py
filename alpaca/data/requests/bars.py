from datetime import datetime
from typing import Optional, Union, List

from alpaca.common import NonEmptyRequest
from alpaca.data import Adjustment, DataFeed
from alpaca.data.time import TimeFrame

# TODO: Remove duplication?


class BaseBarsRequest(NonEmptyRequest):
    """
    A base request object for retrieving bar data for securities. You most likely should not use this directly and instead
    use the asset class specific request objects.

    Attributes:
        symbol_or_symbols (Union[str, List[str]]): The ticker identifier or list of ticker identifiers.
        start (Optional[datetime]): The beginning of the time interval for desired data.
        end (Optional[datetime]): The end of the time interval for desired data. Defaults to None.
        limit (Optional[int]): Upper limit of number of data points to return. Defaults to None.
        timeframe (TimeFrame): The period over which the bars should be aggregated. (i.e. 5 Min bars, 1 Day bars)
    """

    symbol_or_symbols: Union[str, List[str]]
    start: Optional[Union[datetime, str]]
    end: Optional[Union[datetime, str]]
    limit: Optional[int]
    timeframe: TimeFrame

    # Allows TimeFrame as a non-pydantic BaseModel field
    class Config:
        arbitrary_types_allowed = True


class StockBarsRequest(BaseBarsRequest):
    """
    The request model for retrieving bar data for equities.

    See BaseGetBarsRequest for more information on available parameters.

    Attributes:
        adjustment (Optional[Adjustment]): The type of corporate action data normalization.
        feed (Optional[DataFeed]): The stock data feed to retrieve from.
    """

    adjustment: Optional[Adjustment]
    feed: Optional[DataFeed]


class CryptoBarsRequest(BaseBarsRequest):
    """
    The request model for retrieving bar data for cryptocurrencies.

    See BaseGetBarsRequest for more information on available parameters.
    """

    pass
