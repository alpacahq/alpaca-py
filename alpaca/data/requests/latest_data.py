from typing import Union, List, Optional

from alpaca.common import NonEmptyRequest
from alpaca.data import DataFeed

# ############################## Stocks ################################# #


class BaseLatestStockDataRequest(NonEmptyRequest):
    """
    A base request object for retrieving the latest data for stocks. You most likely should not use this directly and
    instead use the asset class specific request objects.

    Attributes:
        symbol_or_symbols (Union[str, List[str]]): The ticker identifier or list of ticker identifiers.
        feed (Optional[DataFeed]): The stock data feed to retrieve from.
    """

    symbol_or_symbols: Union[str, List[str]]
    feed: Optional[DataFeed]


class LatestStockTradeRequest(BaseLatestStockDataRequest):
    """
    This request class is used to submit a request for the latest stock trade data.

    See BaseLatestStockDataRequest for more information on available parameters.
    """

    pass


class LatestStockQuoteRequest(BaseLatestStockDataRequest):
    """
    This request class is used to submit a request for the latest stock quote data.

    See BaseLatestStockDataRequest for more information on available parameters.
    """

    pass


class LatestStockBarRequest(BaseLatestStockDataRequest):
    """
    This request class is used to submit a request for the latest stock bar data.

    See BaseLatestStockDataRequest for more information on available parameters.
    """

    pass


# ############################## Crypto ################################# #


class BaseLatestCryptoDataRequest(NonEmptyRequest):
    """
    A base request object for retrieving the latest data for crypto. You most likely should not use this directly and
    instead use the asset class specific request objects.

    Attributes:
        symbol_or_symbols (Union[str, List[str]]): The ticker identifier or list of ticker identifiers.
    """

    symbol_or_symbols: Union[str, List[str]]


class LatestCryptoTradeRequest(BaseLatestCryptoDataRequest):
    """
    This request class is used to submit a request for the latest crypto trade data.

    See BaseLatestCryptoDataRequest for more information on available parameters.
    """

    pass


class LatestCryptoQuoteRequest(BaseLatestCryptoDataRequest):
    """
    This request class is used to submit a request for the latest crypto quote data.

    See BaseLatestCryptoDataRequest for more information on available parameters.
    """

    pass


class LatestCryptoBarRequest(BaseLatestCryptoDataRequest):
    """
    This request class is used to submit a request for the latest crypto bar data.

    See BaseLatestCryptoDataRequest for more information on available parameters.
    """

    pass
