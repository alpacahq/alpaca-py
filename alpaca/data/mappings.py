from typing import Dict

BAR_MAPPING: Dict[str, str] = {
    "t": "timestamp",
    "o": "open",
    "h": "high",
    "l": "low",
    "c": "close",
    "v": "volume",
    "n": "trade_count",
    "vw": "vwap",
}

QUOTE_MAPPING: Dict[str, str] = {
    "t": "timestamp",
    "ax": "ask_exchange",
    "ap": "ask_price",
    "as": "ask_size",
    "bx": "bid_exchange",
    "bp": "bid_price",
    "bs": "bid_size",
    "c": "conditions",
    "z": "tape",
}

TRADE_MAPPING: Dict[str, str] = {
    "t": "timestamp",
    "p": "price",
    "s": "size",
    "x": "exchange",
    "i": "id",
    "c": "conditions",
    "z": "tape",
}

SNAPSHOT_MAPPING: Dict[str, str] = {
    "latestTrade": "latest_trade",
    "latestQuote": "latest_quote",
    "minuteBar": "minute_bar",
    "dailyBar": "daily_bar",
    "prevDailyBar": "previous_daily_bar",
    "impliedVolatility": "implied_volatility",
    "greeks": "greeks",
}

ORDERBOOK_MAPPING: Dict[str, str] = {
    "t": "timestamp",
    "b": "bids",
    "a": "asks",
    "r": "reset",
}

TRADING_STATUS_MAPPING: Dict[str, str] = {
    "t": "timestamp",
    "sc": "status_code",
    "sm": "status_message",
    "rc": "reason_code",
    "rm": "reason_message",
    "z": "tape",
}

TRADE_CANCEL_MAPPING: Dict[str, str] = {
    "t": "timestamp",
    "p": "price",
    "s": "size",
    "x": "exchange",
    "i": "id",
    "a": "action",
    "z": "tape",
}

TRADE_CORRECTION_MAPPING: Dict[str, str] = {
    "t": "timestamp",
    "x": "exchange",
    "oi": "original_id",
    "op": "original_price",
    "os": "original_size",
    "oc": "original_conditions",
    "ci": "corrected_id",
    "cp": "corrected_price",
    "cs": "corrected_size",
    "cc": "corrected_conditions",
    "z": "tape",
}
