from typing import Dict, Any

from alpaca.common.types import RawData
from alpaca.common.models import ValidateBaseModel as BaseModel
from alpaca.data.models import Trade, Quote, Bar
from alpaca.data.mappings import SNAPSHOT_MAPPING


class Snapshot(BaseModel):
    """A Snapshot contains the latest trade, latest quote, minute bar daily bar
    and previous daily bar data for a given ticker symbol.

    Attributes:
        symbol (str): The identifier for the snapshot security.
        latest_trade(Trade): The latest transaction on the price and sales tape
        latest_quote (Quote): Level 1 ask/bid pair quote data.
        minute_bar (Bar): The latest minute OHLC bar data
        daily_bar (Bar): The latest daily OHLC bar data
        previous_daily_bar (Bar): The 2nd to latest (2 trading days ago) daily OHLC bar data
    """

    symbol: str
    latest_trade: Trade
    latest_quote: Quote
    minute_bar: Bar
    daily_bar: Bar
    previous_daily_bar: Bar

    def __init__(self, symbol: str, raw_data: Dict[str, RawData]) -> None:
        """Instantiates a Snapshot.

        Args:
            symbol (str): The identifier for the snapshot security.
            raw_data (Dict[str, RawData]): The raw API snapshot data keyed by symbol
        """
        mapped_snapshot = {
            SNAPSHOT_MAPPING.get(key): val
            for key, val in raw_data.items()
            if key in SNAPSHOT_MAPPING
        }

        # Parse each data type
        mapped_snapshot["latest_trade"] = Trade(symbol, mapped_snapshot["latest_trade"])
        mapped_snapshot["latest_quote"] = Quote(symbol, mapped_snapshot["latest_quote"])
        mapped_snapshot["minute_bar"] = Bar(symbol, mapped_snapshot["minute_bar"])
        mapped_snapshot["daily_bar"] = Bar(symbol, mapped_snapshot["daily_bar"])
        mapped_snapshot["previous_daily_bar"] = Bar(
            symbol, mapped_snapshot["previous_daily_bar"]
        )

        super().__init__(symbol=symbol, **mapped_snapshot)


class SnapshotSet(BaseModel):
    """A collection of Snapshots keyed by symbol

    Attributes:
        data (Dict[str, Snapshot]): Snapshot data keyed by symbol
    """

    data: Dict[str, Snapshot]

    def __init__(self, raw_data: Dict[str, RawData]) -> None:
        """Instantiates a collection of Snapshot.

        Args:
            raw_data: The raw snapshot data from API.
        """
        parsed_snapshots = {}

        for symbol, snapshot in raw_data.items():
            parsed_snapshots[symbol] = Snapshot(symbol, snapshot)

        super().__init__(data=parsed_snapshots)

    def __getitem__(self, symbol: str) -> Any:
        """Gives dictionary-like access to multi-symbol data

        Args:
            symbol (str): The ticker identifier for the desired data

        Raises:
            KeyError: Symbol does not exist for data

        Returns:
            List[Bar]: The data for the given symbol
        """
        if symbol not in self.data:
            raise KeyError(f"No key {symbol} was found.")

        return self.data[symbol]
