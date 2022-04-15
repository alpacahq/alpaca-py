from enum import Enum


class BaseURL(str, Enum):
    """Base urls for API endpoints"""

    BROKER_SANDBOX = "https://broker-api.sandbox.alpaca.markets"
    BROKER_PRODUCTION = "https://broker-api.alpaca.markets"
    TRADING_PAPER = "https://paper-api.alpaca.markets"
    TRADING_LIVE = "https://api.alpaca.markets"
    DATA = "https://data.alpaca.markets"
    MARKET_DATA_LIVE = "wss://stream.data.alpaca.markets"


class Sort(str, Enum):
    ASC = "asc"
    DESC = "desc"
