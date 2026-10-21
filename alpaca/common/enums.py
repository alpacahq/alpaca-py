from enum import Enum

from alpaca._deprecating_enum import DeprecatingEnumMeta as _DeprecatingEnumMeta

_DEPRECATED_BASE_URLS = {
    "OPTION_DATA_STREAM": (
        "BaseURL.OPTION_DATA_STREAM is deprecated. "
        "Use BaseURL.MARKET_DATA_STREAM instead."
    ),
}


class BaseURL(
    str, Enum, metaclass=_DeprecatingEnumMeta, deprecations=_DEPRECATED_BASE_URLS
):
    """Base urls for API endpoints.

    OPTION_DATA_STREAM is deprecated. Use MARKET_DATA_STREAM instead.
    """

    BROKER_SANDBOX = "https://broker-api.sandbox.alpaca.markets"
    BROKER_PRODUCTION = "https://broker-api.alpaca.markets"
    TRADING_PAPER = "https://paper-api.alpaca.markets"
    TRADING_LIVE = "https://api.alpaca.markets"
    DATA = "https://data.alpaca.markets"
    DATA_SANDBOX = "https://data.sandbox.alpaca.markets"
    MARKET_DATA_STREAM = "wss://stream.data.alpaca.markets"
    OPTION_DATA_STREAM = MARKET_DATA_STREAM
    TRADING_STREAM_PAPER = "wss://paper-api.alpaca.markets/stream"
    TRADING_STREAM_LIVE = "wss://api.alpaca.markets/stream"


class PaginationType(str, Enum):
    """
    An enum for choosing what type of pagination of results you'd like for BrokerClient functions that support
    pagination.

    Attributes:
        NONE: Requests that we perform no pagination of results and just return the single response the API gave us.
        FULL: Requests that we perform all the pagination and return just a single List/dict/etc containing all the
          results. This is the default for most functions.
        ITERATOR: Requests that we return an Iterator that yields one "page" of results at a time
    """

    NONE = "none"
    FULL = "full"
    ITERATOR = "iterator"


class Sort(str, Enum):
    ASC = "asc"
    DESC = "desc"


class SupportedCurrencies(str, Enum):
    """
    The various currencies that can be supported for LCT.

    see https://alpaca.markets/support/local-currency-trading-faq
    """

    USD = "USD"
    GBP = "GBP"
    CHF = "CHF"
    EUR = "EUR"
    CAD = "CAD"
    JPY = "JPY"
    TRY = "TRY"
    AUD = "AUD"
    CZK = "CZK"
    SEK = "SEK"
    DKK = "DKK"
    SGD = "SGD"
    HKD = "HKD"
    HUF = "HUF"
    NZD = "NZD"
    NOK = "NOK"
    PLN = "PLN"
