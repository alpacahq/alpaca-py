from urllib.parse import parse_qs, urlparse

import alpaca.data.historical as historical
from alpaca.data._generated.models import (
    FixedIncomeLatestPricesResp,
    FixedIncomeLatestQuotesResp,
)
from alpaca.data.historical.fixed_income import FixedIncomeClient
from alpaca.data.requests import (
    FixedIncomeLatestPricesRequest,
    FixedIncomeLatestQuotesRequest,
)


def test_historical_package_exports_new_clients():
    assert "FixedIncomeClient" in historical.__all__
    assert "LogoClient" in historical.__all__


def test_get_fixed_income_latest_prices(
    reqmock, fixed_income_client: FixedIncomeClient
):
    reqmock.get(
        "https://data.alpaca.markets/v1beta1/fixed_income/latest/prices",
        json={
            "prices": {
                "US912797KJ59": {
                    "p": 99.6459,
                    "t": "2025-02-14T20:58:00.648Z",
                    "ytm": 4.249,
                    "ytw": 4.249,
                }
            }
        },
    )

    prices = fixed_income_client.get_fixed_income_latest_prices(
        FixedIncomeLatestPricesRequest(isins=["US912797KJ59", "US912797KS58"])
    )

    assert isinstance(prices, FixedIncomeLatestPricesResp)
    assert prices.prices["US912797KJ59"].p == 99.6459
    assert (
        urlparse(reqmock.request_history[0].url).path
        == "/v1beta1/fixed_income/latest/prices"
    )
    assert parse_qs(urlparse(reqmock.request_history[0].url).query)["isins"] == [
        "US912797KJ59,US912797KS58"
    ]


def test_get_fixed_income_latest_quotes(
    reqmock, fixed_income_client: FixedIncomeClient
):
    reqmock.get(
        "https://data.alpaca.markets/v1beta1/fixed_income/latest/quotes",
        json={
            "quotes": {
                "US912797SX61": {
                    "ams": 1000,
                    "ap": 99.91958333,
                    "as": 1000000,
                    "aytm": 2.226923,
                    "aytw": 2.226923,
                    "bms": 1000,
                    "bp": 99.81091667,
                    "bs": 1000000,
                    "bytm": 5.236154,
                    "bytw": 5.236154,
                    "t": "2026-05-21T06:56:01.882466Z",
                }
            }
        },
    )

    quotes = fixed_income_client.get_fixed_income_latest_quotes(
        FixedIncomeLatestQuotesRequest(isins="US912797SX61", trade_size=1000)
    )

    assert isinstance(quotes, FixedIncomeLatestQuotesResp)
    assert quotes.quotes["US912797SX61"].bp == 99.81091667
    assert quotes.quotes["US912797SX61"].var_as == 1000000
    assert (
        urlparse(reqmock.request_history[0].url).path
        == "/v1beta1/fixed_income/latest/quotes"
    )
    query = parse_qs(urlparse(reqmock.request_history[0].url).query)
    assert query["isins"] == ["US912797SX61"]
    assert query["trade_size"] == ["1000"]
