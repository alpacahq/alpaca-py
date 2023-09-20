from datetime import datetime
from typing import Optional, Union, List, Any
from pydantic import ConfigDict
import pytz
from alpaca.common.enums import SupportedCurrencies
from alpaca.common.requests import NonEmptyRequest
from alpaca.data.enums import Adjustment, DataFeed, MarketType, MostActivesBy
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
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    limit: Optional[int] = None
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
    model_config = ConfigDict(arbitrary_types_allowed=True)


class StockBarsRequest(BaseBarsRequest):
    """
    The request model for retrieving bar data for equities.

    See BaseGetBarsRequest for more information on available parameters.

    Attributes:
        symbol_or_symbols (Union[str, List[str]]): The ticker identifier or list of ticker identifiers.
        start (Optional[datetime]): The beginning of the time interval for desired data. Timezone naive inputs assumed to be in UTC.
        end (Optional[datetime]): The end of the time interval for desired data. Defaults to now. Timezone naive inputs assumed to be in UTC.
        limit (Optional[int]): Upper limit of number of data points to return. Defaults to None.
        adjustment (Optional[Adjustment]): The type of corporate action data normalization.
        feed (Optional[DataFeed]): The stock data feed to retrieve from.
    """

    adjustment: Optional[Adjustment] = None
    feed: Optional[DataFeed] = None


class CryptoBarsRequest(BaseBarsRequest):
    """
    The request model for retrieving bar data for cryptocurrencies.

    See BaseGetBarsRequest for more information on available parameters.

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

    feed: Optional[DataFeed] = None


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

    feed: Optional[DataFeed] = None


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
    feed: Optional[DataFeed] = None
    currency: Optional[SupportedCurrencies] = None  # None = USD


class StockLatestTradeRequest(BaseStockLatestDataRequest):
    """
    This request class is used to submit a request for the latest stock trade data.

    See BaseLatestStockDataRequest for more information on available parameters.

    Attributes:
        symbol_or_symbols (Union[str, List[str]]): The ticker identifier or list of ticker identifiers.
        feed (Optional[DataFeed]): The stock data feed to retrieve from.
    """

    pass


class StockLatestQuoteRequest(BaseStockLatestDataRequest):
    """
    This request class is used to submit a request for the latest stock quote data.

    See BaseLatestStockDataRequest for more information on available parameters.

    Attributes:
        symbol_or_symbols (Union[str, List[str]]): The ticker identifier or list of ticker identifiers.
        feed (Optional[DataFeed]): The stock data feed to retrieve from.
    """

    pass


class StockLatestBarRequest(BaseStockLatestDataRequest):
    """
    This request class is used to submit a request for the latest stock bar data.

    See BaseLatestStockDataRequest for more information on available parameters.

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

    See BaseLatestCryptoDataRequest for more information on available parameters.

    Attributes:
        symbol_or_symbols (Union[str, List[str]]): The ticker identifier or list of ticker identifiers.
    """

    pass


class CryptoLatestQuoteRequest(BaseCryptoLatestDataRequest):
    """
    This request class is used to submit a request for the latest crypto quote data.

    See BaseLatestCryptoDataRequest for more information on available parameters.

    Attributes:
        symbol_or_symbols (Union[str, List[str]]): The ticker identifier or list of ticker identifiers.
    """

    pass


class CryptoLatestBarRequest(BaseCryptoLatestDataRequest):
    """
    This request class is used to submit a request for the latest crypto bar data.

    See BaseLatestCryptoDataRequest for more information on available parameters.

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
    feed: Optional[DataFeed] = None
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


# ############################## Screener #################################### #


class ScreenerRequest(NonEmptyRequest):
    """
    This request class is used to submit a request for screener endpoints.

    Attributes:
        top (int): Number of top most active stocks to fetch per day.
    """

    top: int = 10


class MostActivesRequest(ScreenerRequest):
    """
    This request class is used to submit a request for most actives screener endpoint.

    Attributes:
        by (MostActivesBy): The metric used for ranking the most active stocks.
        top (int): Number of top most active stocks to fetch per day.
    """

    by: MostActivesBy = MostActivesBy.VOLUME.value


class MarketMoversRequest(ScreenerRequest):
    """
    This request class is used to submit a request for most actives screener endpoint.

    Attributes:
        market_type (MarketType): Screen specific market (stocks or crypto).
        top (int): Number of top most active stocks to fetch per day.
    """

    market_type: MarketType = MarketType.STOCKS


class NewsRequest(NonEmptyRequest):
    """
    This request class is used to submit a request for most actives screener endpoint.

    Attributes:
    start (Optional[datetime]): The inclusive start of the interval. Format: RFC-3339 or YYYY-MM-DD.
        If missing, the default value is the beginning of the current day.
    end (Optional[datetime])): The inclusive end of the interval. Format: RFC-3339 or YYYY-MM-DD.
        If missing, the default value is the current time.
    sort (Optional[str]): Sort articles by updated date.
    symbols (Optional[str]): The comma-separated list of symbols to query news for.
    limit (Optional[int]): Limit of news items to be returned for given page.
    include_content (Optional[bool]): Boolean indicator to include content for news articles (if available)
    exclude_contentless (Optional[bool]): Boolean indicator to exclude news articles that do not contain content
    page_token (Optional[str]): Pagination token to continue from. The value to pass here is returned in specific requests
        when more data is available than the request limit allows.
    """

    start: Optional[datetime] = None
    end: Optional[datetime] = None
    sort: Optional[str] = None
    symbols: Optional[str] = None
    limit: Optional[int] = None
    include_content: Optional[bool] = None
    exclude_contentless: Optional[bool] = None
    page_token: Optional[str] = None
