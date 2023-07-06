from datetime import datetime
from typing import Optional, Union, List, Any
import pytz
from alpaca.common.enums import SupportedCurrencies
from alpaca.common.requests import NonEmptyRequest
from alpaca.data.enums import Adjustment, DataFeed
from alpaca.data.timeframe import TimeFrame


class BaseTimeseriesDataRequest(NonEmptyRequest):
    """
    A base class for requests for time series data between a start and an end. This shouldn't be
    instantiated directly. Instead, you should use one of the data type specific classes.

    Attributes:
        symbol_or_symbols (Union[str, List[str]]): The ticker identifier or list of ticker identifiers.
        start (Optional[datetime]): The beginning of the time interval for desired data. Timezone naive inputs assumed to be in UTC.
        end (Optional[datetime]): The end of the time interval for desired data. Timezone naive inputs assumed to be in UTC.
        limit (Optional[int]): Upper limit of number of data points to return. Defaults to None.
        currency (Optional[SupportedCurrencies]): The currency the data should be returned in. Default to USD.
    """

    symbol_or_symbols: Union[str, List[str]]
    start: Optional[datetime]
    end: Optional[datetime]
    limit: Optional[int]
    currency: Optional[SupportedCurrencies] = None  # None = USD

    def __init__(self, **data: Any) -> None:

        # convert timezone aware datetime to timezone naive UTC datetime
        if (
            "start" in data
            and data["start"] is not None
            and isinstance(data["start"], datetime)
            and data["start"].tzinfo is not None
        ):
            data["start"] = data["start"].astimezone(pytz.utc).replace(tzinfo=None)

        if (
            "end" in data
            and data["end"] is not None
            and isinstance(data["end"], datetime)
            and data["end"].tzinfo is not None
        ):
            data["end"] = data["end"].astimezone(pytz.utc).replace(tzinfo=None)

        super().__init__(**data)


# ############################## Bars ################################# #


class BaseBarsRequest(BaseTimeseriesDataRequest):
    """
    A base request object for retrieving bar data for securities. You most likely should not use this directly and instead
    use the asset class specific request objects.

    Attributes:
        symbol_or_symbols (Union[str, List[str]]): The ticker identifier or list of ticker identifiers.
        start (Optional[datetime]): The beginning of the time interval for desired data. Timezone naive inputs assumed to be in UTC.
        end (Optional[datetime]): The end of the time interval for desired data. Defaults to now. Timezone naive inputs assumed to be in UTC.
        limit (Optional[int]): Upper limit of number of data points to return. Defaults to None.
        timeframe (TimeFrame): The period over which the bars should be aggregated. (i.e. 5 Min bars, 1 Day bars)
    """

    timeframe: TimeFrame

    # Allows TimeFrame as a non-pydantic BaseModel field
    class Config:
        arbitrary_types_allowed = True


class StockBarsRequest(BaseBarsRequest):
    """
    The request model for retrieving bar data for equities.

    See BaseBarsRequest for more information on available parameters.

    Attributes:
        symbol_or_symbols (Union[str, List[str]]): The ticker identifier or list of ticker identifiers.
        start (Optional[datetime]): The beginning of the time interval for desired data. Timezone naive inputs assumed to be in UTC.
        end (Optional[datetime]): The end of the time interval for desired data. Defaults to now. Timezone naive inputs assumed to be in UTC.
        limit (Optional[int]): Upper limit of number of data points to return. Defaults to None.
        adjustment (Optional[Adjustment]): The type of corporate action data normalization.
        feed (Optional[DataFeed]): The stock data feed to retrieve from.
    """

    adjustment: Optional[Adjustment]
    feed: Optional[DataFeed]


class CryptoBarsRequest(BaseBarsRequest):
    """
    The request model for retrieving bar data for cryptocurrencies.

    See BaseBarsRequest for more information on available parameters.

    Attributes:
        symbol_or_symbols (Union[str, List[str]]): The ticker identifier or list of ticker identifiers.
        start (Optional[datetime]): The beginning of the time interval for desired data. Timezone naive inputs assumed to be in UTC.
        end (Optional[datetime]): The end of the time interval for desired data. Defaults to now. Timezone naive inputs assumed to be in UTC.
        limit (Optional[int]): Upper limit of number of data points to return. Defaults to None.
    """

    pass


# ############################## Quotes ################################# #


class StockQuotesRequest(BaseTimeseriesDataRequest):
    """
    This request class is used to submit a request for stock quote data.

    See BaseTimeseriesDataRequest for more information on available parameters.

    Attributes:
        symbol_or_symbols (Union[str, List[str]]): The ticker identifier or list of ticker identifiers.
        start (Optional[datetime]): The beginning of the time interval for desired data. Timezone naive inputs assumed to be in UTC.
        end (Optional[datetime]): The end of the time interval for desired data. Defaults to now. Timezone naive inputs assumed to be in UTC.
        limit (Optional[int]): Upper limit of number of data points to return. Defaults to None.
        feed (Optional[DataFeed]): The stock data feed to retrieve from.
    """

    feed: Optional[DataFeed]


# ############################## Trades ################################# #


class StockTradesRequest(BaseTimeseriesDataRequest):
    """
    This request class is used to submit a request for stock trade data.

    See BaseTimeseriesDataRequest for more information on available parameters.

    Attributes:
        symbol_or_symbols (Union[str, List[str]]): The ticker identifier or list of ticker identifiers.
        start (Optional[datetime]): The beginning of the time interval for desired data. Timezone naive inputs assumed to be in UTC.
        end (Optional[datetime]): The end of the time interval for desired data. Defaults to now. Timezone naive inputs assumed to be in UTC.
        limit (Optional[int]): Upper limit of number of data points to return. Defaults to None.
        feed (Optional[DataFeed]): The stock data feed to retrieve from.
    """

    feed: Optional[DataFeed]


class CryptoTradesRequest(BaseTimeseriesDataRequest):
    """
    This request class is used to submit a request for crypto trade data.

    See BaseTimeseriesDataRequest for more information on available parameters.

    Attributes:
        symbol_or_symbols (Union[str, List[str]]): The ticker identifier or list of ticker identifiers.
        start (Optional[datetime]): The beginning of the time interval for desired data. Timezone naive inputs assumed to be in UTC.
        end (Optional[datetime]): The end of the time interval for desired data. Defaults to now. Timezone naive inputs assumed to be in UTC.
        limit (Optional[int]): Upper limit of number of data points to return. Defaults to None.
    """

    pass


# ############################## Latest Endpoints ################################# #


class BaseStockLatestDataRequest(NonEmptyRequest):
    """
    A base request object for retrieving the latest data for stocks. You most likely should not use this directly and
    instead use the asset class specific request objects.

    Attributes:
        symbol_or_symbols (Union[str, List[str]]): The ticker identifier or list of ticker identifiers.
        feed (Optional[DataFeed]): The stock data feed to retrieve from.
        currency (Optional[SupportedCurrencies]): The currency the data should be returned in. Default to USD.
    """

    symbol_or_symbols: Union[str, List[str]]
    feed: Optional[DataFeed]
    currency: Optional[SupportedCurrencies] = None  # None = USD


class StockLatestTradeRequest(BaseStockLatestDataRequest):
    """
    This request class is used to submit a request for the latest stock trade data.

    See BaseStockLatestDataRequest for more information on available parameters.

    Attributes:
        symbol_or_symbols (Union[str, List[str]]): The ticker identifier or list of ticker identifiers.
        feed (Optional[DataFeed]): The stock data feed to retrieve from.
    """

    pass


class StockLatestQuoteRequest(BaseStockLatestDataRequest):
    """
    This request class is used to submit a request for the latest stock quote data.

    See BaseStockLatestDataRequest for more information on available parameters.

    Attributes:
        symbol_or_symbols (Union[str, List[str]]): The ticker identifier or list of ticker identifiers.
        feed (Optional[DataFeed]): The stock data feed to retrieve from.
    """

    pass


class StockLatestBarRequest(BaseStockLatestDataRequest):
    """
    This request class is used to submit a request for the latest stock bar data.

    See BaseStockLatestDataRequest for more information on available parameters.

    Attributes:
        symbol_or_symbols (Union[str, List[str]]): The ticker identifier or list of ticker identifiers.
        feed (Optional[DataFeed]): The stock data feed to retrieve from.
    """

    pass


class BaseCryptoLatestDataRequest(NonEmptyRequest):
    """
    A base request object for retrieving the latest data for crypto. You most likely should not use this directly and
    instead use the asset class specific request objects.

    Attributes:
        symbol_or_symbols (Union[str, List[str]]): The ticker identifier or list of ticker identifiers.
    """

    symbol_or_symbols: Union[str, List[str]]


class CryptoLatestTradeRequest(BaseCryptoLatestDataRequest):
    """
    This request class is used to submit a request for the latest crypto trade data.

    See BaseCryptoLatestDataRequest for more information on available parameters.

    Attributes:
        symbol_or_symbols (Union[str, List[str]]): The ticker identifier or list of ticker identifiers.
    """

    pass


class CryptoLatestQuoteRequest(BaseCryptoLatestDataRequest):
    """
    This request class is used to submit a request for the latest crypto quote data.

    See BaseCryptoLatestDataRequest for more information on available parameters.

    Attributes:
        symbol_or_symbols (Union[str, List[str]]): The ticker identifier or list of ticker identifiers.
    """

    pass


class CryptoLatestBarRequest(BaseCryptoLatestDataRequest):
    """
    This request class is used to submit a request for the latest crypto bar data.

    See BaseCryptoLatestDataRequest for more information on available parameters.

    Attributes:
        symbol_or_symbols (Union[str, List[str]]): The ticker identifier or list of ticker identifiers.
    """

    pass


# ############################## Snapshots ################################# #


class StockSnapshotRequest(NonEmptyRequest):
    """
    This request class is used to submit a request for snapshot data for stocks.

    Attributes:
        symbol_or_symbols (Union[str, List[str]]): The ticker identifier or list of ticker identifiers.
        feed (Optional[DataFeed]): The stock data feed to retrieve from.
        currency (Optional[SupportedCurrencies]): The currency the data should be returned in. Default to USD.
    """

    symbol_or_symbols: Union[str, List[str]]
    feed: Optional[DataFeed]
    currency: Optional[SupportedCurrencies] = None  # None = USD


class CryptoSnapshotRequest(NonEmptyRequest):
    """
    This request class is used to submit a request for snapshot data for crypto.

    Attributes:
        symbol_or_symbols (Union[str, List[str]]): The ticker identifier or list of ticker identifiers.
    """

    symbol_or_symbols: Union[str, List[str]]


# ############################## Orderbooks ################################# #


class CryptoLatestOrderbookRequest(NonEmptyRequest):
    """
    This request class is used to submit a request for latest orderbook data for crypto.

    Attributes:
        symbol_or_symbols (Union[str, List[str]]): The ticker identifier or list of ticker identifiers.
    """

    symbol_or_symbols: Union[str, List[str]]
