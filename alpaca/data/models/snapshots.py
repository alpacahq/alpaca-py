from typing import Dict, Optional

from pydantic import ConfigDict

from alpaca.common.types import RawData
from alpaca.common.models import ValidateBaseModel as BaseModel
from alpaca.data.models import Trade, Quote, Bar
from alpaca.data.mappings import SNAPSHOT_MAPPING


class Snapshot(BaseModel):
    """A Snapshot contains the latest trade, latest quote, minute bar daily bar
    and previous daily bar data for a given ticker symbol.

    Attributes:
        symbol (str): The identifier for the snapshot security.
        latest_trade (Optional[Trade]): The latest transaction on the price and sales tape
        latest_quote (Optional[Quote]): Level 1 ask/bid pair quote data.
        minute_bar (Optional[Bar]): The latest minute OHLC bar data
        daily_bar (Optional[Bar]): The latest daily OHLC bar data
        previous_daily_bar (Optional[Bar]): The 2nd to latest (2 trading days ago) daily OHLC bar data
    """

    symbol: str
    latest_trade: Optional[Trade] = None
    latest_quote: Optional[Quote] = None
    minute_bar: Optional[Bar] = None
    daily_bar: Optional[Bar] = None
    previous_daily_bar: Optional[Bar] = None

    model_config = ConfigDict(protected_namespaces=tuple())

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
        if mapped_snapshot.get("latest_trade", None) is not None:
            mapped_snapshot["latest_trade"] = Trade(
                symbol, mapped_snapshot["latest_trade"]
            )
        if mapped_snapshot.get("latest_quote", None) is not None:
            mapped_snapshot["latest_quote"] = Quote(
                symbol, mapped_snapshot["latest_quote"]
            )
        if mapped_snapshot.get("minute_bar", None) is not None:
            mapped_snapshot["minute_bar"] = Bar(symbol, mapped_snapshot["minute_bar"])
        if mapped_snapshot.get("daily_bar", None) is not None:
            mapped_snapshot["daily_bar"] = Bar(symbol, mapped_snapshot["daily_bar"])
        if mapped_snapshot.get("previous_daily_bar", None) is not None:
            mapped_snapshot["previous_daily_bar"] = Bar(
                symbol, mapped_snapshot["previous_daily_bar"]
            )

        super().__init__(symbol=symbol, **mapped_snapshot)
