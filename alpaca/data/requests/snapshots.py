from typing import Union, List, Optional

from alpaca.common import NonEmptyRequest
from alpaca.data import DataFeed


class StockSnapshotRequest(NonEmptyRequest):
    """
    This request class is used to submit a request for snapshot data for stocks.

    Attributes:
        symbol_or_symbols (Union[str, List[str]]): The ticker identifier or list of ticker identifiers.
        feed (Optional[DataFeed]): The stock data feed to retrieve from.
    """

    symbol_or_symbols: Union[str, List[str]]
    feed: Optional[DataFeed]


class CryptoSnapshotRequest(NonEmptyRequest):
    """
    This request class is used to submit a request for snapshot data for crypto.

    Attributes:
        symbol_or_symbols (Union[str, List[str]]): The ticker identifier or list of ticker identifiers.
    """

    symbol_or_symbols: Union[str, List[str]]
