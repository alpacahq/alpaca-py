from datetime import date, datetime
from typing import Any, List, Optional, Union

import pytz
from pydantic import ConfigDict

from alpaca.common.enums import Sort, SupportedCurrencies
from alpaca.common.requests import NonEmptyRequest
from alpaca.data.enums import (
    Adjustment,
    CorporateActionsType,
    DataFeed,
    MarketType,
    MostActivesBy,
    OptionsFeed,
)
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.enums import ContractType


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
        sort: (Optional[Sort]): The chronological order of response based on the timestamp. Defaults to ASC.
    """

    symbol_or_symbols: Union[str, List[str]]
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    limit: Optional[int] = None
    currency: Optional[SupportedCurrencies] = None  # None = USD
    sort: Optional[Sort] = None  # None = asc

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
        sort (Optional[Sort]): The chronological order of response based on the timestamp. Defaults to ASC.
    """

    timeframe: TimeFrame

    # Allows TimeFrame as a non-pydantic BaseModel field
    model_config = ConfigDict(arbitrary_types_allowed=True)


class StockBarsRequest(BaseBarsRequest):
    """
    The request model for retrieving bar data for equities.

    See BaseBarsRequest for more information on available parameters.

    Attributes:
        symbol_or_symbols (Union[str, List[str]]): The ticker identifier or list of ticker identifiers.
        timeframe (TimeFrame): The period over which the bars should be aggregated. (i.e. 5 Min bars, 1 Day bars)
        start (Optional[datetime]): The beginning of the time interval for desired data. Timezone naive inputs assumed to be in UTC.
        end (Optional[datetime]): The end of the time interval for desired data. Defaults to now. Timezone naive inputs assumed to be in UTC.
        limit (Optional[int]): Upper limit of number of data points to return. Defaults to None.
        adjustment (Optional[Adjustment]): The type of corporate action data normalization.
        feed (Optional[DataFeed]): The stock data feed to retrieve from.
        sort (Optional[Sort]): The chronological order of response based on the timestamp. Defaults to ASC.
        asof (Optional[str]): The asof date of the queried stock symbol(s) in YYYY-MM-DD format.
        currency (Optional[SupportedCurrencies]): The currency of all prices in ISO 4217 format. Default is USD.
    """

    adjustment: Optional[Adjustment] = None
    feed: Optional[DataFeed] = None
    asof: Optional[str] = None


class CryptoBarsRequest(BaseBarsRequest):
    """
    The request model for retrieving bar data for cryptocurrencies.

    See BaseBarsRequest for more information on available parameters.

    Attributes:
        symbol_or_symbols (Union[str, List[str]]): The ticker identifier or list of ticker identifiers.
        timeframe (TimeFrame): The period over which the bars should be aggregated. (i.e. 5 Min bars, 1 Day bars)
        start (Optional[datetime]): The beginning of the time interval for desired data. Timezone naive inputs assumed to be in UTC.
        end (Optional[datetime]): The end of the time interval for desired data. Defaults to now. Timezone naive inputs assumed to be in UTC.
        limit (Optional[int]): Upper limit of number of data points to return. Defaults to None.
        sort (Optional[Sort]): The chronological order of response based on the timestamp. Defaults to ASC.
    """

    pass


class OptionBarsRequest(BaseBarsRequest):
    """
    The request model for retrieving bar data for option contracts.

    See BaseBarsRequest for more information on available parameters.

    Attributes:
        symbol_or_symbols (Union[str, List[str]]): The ticker identifier or list of ticker identifiers.
        timeframe (TimeFrame): The length of time (also known as time interval) for which each Bar represents (i.e. 5 Min bars, 1 Day bars).
        start (Optional[datetime]): The beginning of the time period for desired data. Timezone naive inputs assumed to be in UTC.
        end (Optional[datetime]): The end of the time period for desired data. Defaults to now. Timezone naive inputs assumed to be in UTC.
        limit (Optional[int]): Upper limit of number of data points to return. Defaults to None.
        sort (Optional[Sort]): The chronological order of response based on the timestamp. Defaults to ASC.
    """


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
        sort (Optional[Sort]): The chronological order of response based on the timestamp. Defaults to ASC.
        asof (Optional[str]): The asof date of the queried stock symbol(s) in YYYY-MM-DD format.
        currency (Optional[SupportedCurrencies]): The currency of all prices in ISO 4217 format. Default is USD.
    """

    feed: Optional[DataFeed] = None
    asof: Optional[str] = None


class CryptoQuoteRequest(BaseTimeseriesDataRequest):
    """
    This request class is used to submit a request for crypto quote data.

    See BaseTimeseriesDataRequest for more information on available parameters.

    Attributes:
        symbol_or_symbols (Union[str, List[str]]): The ticker identifier or list of ticker identifiers.
        start (Optional[datetime]): The beginning of the time interval for desired data. Timezone naive inputs assumed to be in UTC.
        end (Optional[datetime]): The end of the time interval for desired data. Defaults to now. Timezone naive inputs assumed to be in UTC.
        limit (Optional[int]): Upper limit of number of data points to return. Defaults to None.
        sort (Optional[Sort]): The chronological order of response based on the timestamp. Defaults to ASC.

    """

    pass


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
        sort (Optional[Sort]): The chronological order of response based on the timestamp. Defaults to ASC.
        asof (Optional[str]): The asof date of the queried stock symbol(s) in YYYY-MM-DD format.
        currency (Optional[SupportedCurrencies]): The currency of all prices in ISO 4217 format. Default is USD.
    """

    feed: Optional[DataFeed] = None
    asof: Optional[str] = None


class CryptoTradesRequest(BaseTimeseriesDataRequest):
    """
    This request class is used to submit a request for crypto trade data.

    See BaseTimeseriesDataRequest for more information on available parameters.

    Attributes:
        symbol_or_symbols (Union[str, List[str]]): The ticker identifier or list of ticker identifiers.
        start (Optional[datetime]): The beginning of the time interval for desired data. Timezone naive inputs assumed to be in UTC.
        end (Optional[datetime]): The end of the time interval for desired data. Defaults to now. Timezone naive inputs assumed to be in UTC.
        limit (Optional[int]): Upper limit of number of data points to return. Defaults to None.
        sort (Optional[Sort]): The chronological order of response based on the timestamp. Defaults to ASC.
    """

    pass


class OptionTradesRequest(BaseTimeseriesDataRequest):
    """
    This request class is used to submit a request for option trade data.

    See BaseTimeseriesDataRequest for more information on available parameters.

    Attributes:
        symbol_or_symbols (Union[str, List[str]]): The option identifier or list of option identifiers.
        start (Optional[datetime]): The beginning of the time interval for desired data. Timezone naive inputs assumed to be in UTC.
        end (Optional[datetime]): The end of the time interval for desired data. Defaults to now. Timezone naive inputs assumed to be in UTC.
        limit (Optional[int]): Upper limit of number of data points to return. Defaults to None.
        sort (Optional[Sort]): The chronological order of response based on the timestamp. Defaults to ASC.
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

    See BaseStockLatestDataRequest for more information on available parameters.

    Attributes:
        symbol_or_symbols (Union[str, List[str]]): The ticker identifier or list of ticker identifiers.
        feed (Optional[DataFeed]): The stock data feed to retrieve from.
        currency (Optional[SupportedCurrencies]): The currency the data should be returned in. Default to USD.
    """

    pass


class StockLatestQuoteRequest(BaseStockLatestDataRequest):
    """
    This request class is used to submit a request for the latest stock quote data.

    See BaseStockLatestDataRequest for more information on available parameters.

    Attributes:
        symbol_or_symbols (Union[str, List[str]]): The ticker identifier or list of ticker identifiers.
        feed (Optional[DataFeed]): The stock data feed to retrieve from.
        currency (Optional[SupportedCurrencies]): The currency the data should be returned in. Default to USD.
    """

    pass


class StockLatestBarRequest(BaseStockLatestDataRequest):
    """
    This request class is used to submit a request for the latest stock bar data.

    See BaseStockLatestDataRequest for more information on available parameters.

    Attributes:
        symbol_or_symbols (Union[str, List[str]]): The ticker identifier or list of ticker identifiers.
        feed (Optional[DataFeed]): The stock data feed to retrieve from.
        currency (Optional[SupportedCurrencies]): The currency the data should be returned in. Default to USD.
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


class BaseOptionLatestDataRequest(NonEmptyRequest):
    """
    A base request object for retrieving the latest data for options. You most likely should not use this directly and
    instead use the asset class specific request objects.

    Attributes:
        symbol_or_symbols (Union[str, List[str]]): The option identifier or list of option identifiers.
        feed (Optional[OptionsFeed]): The source feed of the data. `opra` or `indicative`. Default: `opra` if the user has the options subscription, `indicative` otherwise.
    """

    symbol_or_symbols: Union[str, List[str]]
    feed: Optional[OptionsFeed] = None


class OptionLatestQuoteRequest(BaseOptionLatestDataRequest):
    """
    This request class is used to submit a request for the latest option quote data.

    See BaseOptionLatestDataRequest for more information on available parameters.

    Attributes:
        symbol_or_symbols (Union[str, List[str]]): The option identifier or list of option identifiers.
        feed (Optional[OptionsFeed]): The source feed of the data. `opra` or `indicative`. Default: `opra` if the user has the options subscription, `indicative` otherwise.
    """

    pass


class OptionLatestTradeRequest(BaseOptionLatestDataRequest):
    """
    This request class is used to submit a request for the latest option trade data.

    See BaseOptionLatestDataRequest for more information on available parameters.

    Attributes:
        symbol_or_symbols (Union[str, List[str]]): The option identifier or list of option identifiers.
        feed (Optional[OptionsFeed]): The source feed of the data. `opra` or `indicative`. Default: `opra` if the user has the options subscription, `indicative` otherwise.
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


class OptionSnapshotRequest(NonEmptyRequest):
    """
    This request class is used to submit a request for snapshot data for options.

    Attributes:
        symbol_or_symbols (Union[str, List[str]]): The option identifier or list of option identifiers.
        feed (Optional[OptionsFeed]): The source feed of the data. `opra` or `indicative`. Default: `opra` if the user has the options subscription, `indicative` otherwise.
    """

    symbol_or_symbols: Union[str, List[str]]
    feed: Optional[OptionsFeed] = None


class OptionChainRequest(NonEmptyRequest):
    """
    This request class is used to submit a request for option chain data for options.

    Attributes:
        underlying_symbol (str): The underlying_symbol for option contracts.
        feed (Optional[OptionsFeed]): The source feed of the data. `opra` or `indicative`. Default: `opra` if the user has the options subscription, `indicative` otherwise.
        type (Optional[ContractType]): Filter contracts by the type (call or put).
        strike_price_gte (Optional[float]): Filter contracts with strike price greater than or equal to the specified value.
        strike_price_lte (Optional[float]): Filter contracts with strike price less than or equal to the specified value.
        expiration_date (Optional[Union[date, str]]): Filter contracts by the exact expiration date (format: YYYY-MM-DD).
        expiration_date_gte (Optional[Union[date, str]]): Filter contracts with expiration date greater than or equal to the specified date.
        expiration_date_lte (Optional[Union[date, str]]): Filter contracts with expiration date less than or equal to the specified date.
        root_symbol (Optional[str]): Filter contracts by the root symbol.
        updated_since (Optional[datetime]): Filter to snapshots that were updated since this timestamp.
    """

    underlying_symbol: str
    feed: Optional[OptionsFeed] = None
    type: Optional[ContractType] = None
    strike_price_gte: Optional[float] = None
    strike_price_lte: Optional[float] = None
    expiration_date: Optional[Union[date, str]] = None
    expiration_date_gte: Optional[Union[date, str]] = None
    expiration_date_lte: Optional[Union[date, str]] = None
    root_symbol: Optional[str] = None
    updated_since: Optional[datetime] = None


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


# ############################## News #################################### #


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
    page_token (Optional[str]): Pagination token to continue from. The value to pass here is returned in specific requests when more data is available than the request limit allows. This should not be used, pagination is handled automatically by the SDK.
    """

    start: Optional[datetime] = None
    end: Optional[datetime] = None
    sort: Optional[str] = None
    symbols: Optional[str] = None
    limit: Optional[int] = None
    include_content: Optional[bool] = None
    exclude_contentless: Optional[bool] = None
    page_token: Optional[str] = None


# ############################## CorporateActions #################################### #


class CorporateActionsRequest(NonEmptyRequest):
    """
    This request class is used to submit a request for corporate actions data.
    ref. https://docs.alpaca.markets/reference/corporateactions-1

    Attributes:
        symbols (Optional[List[str]]): The list of ticker identifiers.
        cusips (Optional[List[str]]): The list of CUSIPs.
        types (Optional[List[CorporateActionsType]]): The types of corporate actions to filter by. (default: all types)
        start (Optional[date]): The inclusive start of the interval. Format: YYYY-MM-DD. (default: current day)
        end (Optional[date])): The inclusive end of the interval. Format: YYYY-MM-DD. (default: current day)
        ids (Optional[List[str]]): The list of corporate action IDs. This parameter is mutually exclusive with all other filters (symbols, types, start, end).
        limit (Optional[int]): Upper limit of number of data points to return. (default: 1000)
        sort (Optional[Sort]): The chronological order of response based on the timestamp. Defaults to ASC.
    """

    symbols: Optional[List[str]] = None
    cusips: Optional[List[str]] = None
    types: Optional[List[CorporateActionsType]] = None
    start: Optional[date] = None
    end: Optional[date] = None
    ids: Optional[List[str]] = None
    limit: Optional[int] = 1000
    sort: Optional[Sort] = Sort.ASC
