from typing import Iterator

import pytest
import requests_mock
from requests_mock import Mocker

from alpaca.broker.client import BrokerClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.historical.corporate_actions import CorporateActionsClient
from alpaca.data.historical.crypto import CryptoHistoricalDataClient
from alpaca.data.historical.news import NewsClient
from alpaca.data.historical.option import OptionHistoricalDataClient
from alpaca.data.historical.screener import ScreenerClient
from alpaca.trading.client import TradingClient

pytest_plugins = ("pytest_asyncio",)


@pytest.fixture
def reqmock() -> Iterator[Mocker]:
    with requests_mock.Mocker() as m:
        yield m


@pytest.fixture
def client():
    client = BrokerClient(
        "key-id",
        "secret-key",
        sandbox=True,  # Expressly call out sandbox as true for correct urls in reqmock
    )
    return client


@pytest.fixture
def raw_client():
    raw_client = BrokerClient("key-id", "secret-key", raw_data=True)
    return raw_client


@pytest.fixture
def trading_client():
    client = TradingClient("key-id", "secret-key")
    return client


@pytest.fixture
def stock_client():
    client = StockHistoricalDataClient("key-id", "secret-key")
    return client


@pytest.fixture
def news_client():
    client = NewsClient("key-id", "secret-key")
    return client


@pytest.fixture
def corporate_actions_client():
    client = CorporateActionsClient("key-id", "secret-key")
    return client


@pytest.fixture
def raw_stock_client():
    raw_client = StockHistoricalDataClient("key-id", "secret-key", raw_data=True)
    return raw_client


@pytest.fixture
def crypto_client():
    client = CryptoHistoricalDataClient("key-id", "secret-key")
    return client


@pytest.fixture
def option_client() -> OptionHistoricalDataClient:
    client = OptionHistoricalDataClient("key-id", "secret-key")
    return client


@pytest.fixture
def screener_client():
    return ScreenerClient("key-id", "secret-key")


@pytest.fixture
def raw_screener_client():
    return ScreenerClient("key-id", "secret-key", raw_data=True)


@pytest.fixture
def raw_crypto_client():
    raw_client = CryptoHistoricalDataClient("key-id", "secret-key", raw_data=True)
    return raw_client
