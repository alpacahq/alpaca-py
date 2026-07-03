"""
Tests for the Trading API's fixed income routes:
  GET /v2/assets/fixed_income/us_treasuries
  GET /v2/assets/fixed_income/us_corporates
"""

from typing import List

import pytest

from alpaca.common.enums import BaseURL
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import BondStatus, TreasurySubtype
from alpaca.trading.models import (
    USCorporate,
    USCorporatesResp,
    USTreasuriesResp,
    USTreasury,
)
from alpaca.trading.requests import GetUSCorporatesRequest, GetUSTreasuriesRequest

# ---------------------------------------------------------------------------
# Shared fixture data
# ---------------------------------------------------------------------------

_TREASURY_JSON = """{
    "cusip": "912810UG1",
    "isin": "US912810UG12",
    "bond_status": "outstanding",
    "tradable": true,
    "subtype": "bond",
    "issue_date": "2020-02-15",
    "maturity_date": "2050-02-15",
    "description": "United States Treasury Bond",
    "description_short": "US T-Bond 2050",
    "coupon": 2.0,
    "coupon_type": "fixed",
    "coupon_frequency": "semi_annual"
}"""

_CORPORATE_JSON = """{
    "cusip": "38141GXZ2",
    "isin": "US38141GXZ20",
    "bond_status": "outstanding",
    "tradable": true,
    "marginable": false,
    "issue_date": "2021-03-01",
    "country_domicile": "US",
    "ticker": "GS",
    "seniority": "Senior",
    "issuer": "Goldman Sachs Group Inc",
    "sector": "Financials",
    "description": "Goldman Sachs Group Inc 1.542% Notes due 2027",
    "description_short": "GS 1.542 09/10/27",
    "coupon": 1.542,
    "coupon_type": "fixed",
    "coupon_frequency": "semi_annual",
    "perpetual": false,
    "day_count": "30/360",
    "dated_date": "2021-03-10",
    "issue_size": 2500000000,
    "issue_price": 99.872,
    "issue_minimum_denomination": 2000,
    "par_value": 1000,
    "callable": false,
    "puttable": false,
    "convertible": false,
    "reg_s": false
}"""


# ---------------------------------------------------------------------------
# US Treasuries
# ---------------------------------------------------------------------------


def test_get_us_treasuries_no_filter(reqmock, trading_client: TradingClient):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/assets/fixed_income/us_treasuries",
        text=f'{{"us_treasuries": [{_TREASURY_JSON}]}}',
    )

    result = trading_client.get_us_treasuries()

    assert reqmock.called_once
    assert isinstance(result, USTreasuriesResp)
    assert len(result.us_treasuries) == 1
    assert isinstance(result.us_treasuries[0], USTreasury)
    assert result.us_treasuries[0].cusip == "912810UG1"
    assert result.us_treasuries[0].bond_status == BondStatus.OUTSTANDING
    assert result.us_treasuries[0].subtype == TreasurySubtype.BOND


def test_get_us_treasuries_with_subtype(reqmock, trading_client: TradingClient):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/assets/fixed_income/us_treasuries?subtype=bond",
        text=f'{{"us_treasuries": [{_TREASURY_JSON}]}}',
    )

    result = trading_client.get_us_treasuries(
        GetUSTreasuriesRequest(subtype=TreasurySubtype.BOND)
    )

    assert reqmock.called_once
    assert isinstance(result, USTreasuriesResp)
    assert result.us_treasuries[0].subtype == TreasurySubtype.BOND


def test_get_us_treasuries_with_bond_status(reqmock, trading_client: TradingClient):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/assets/fixed_income/us_treasuries?bond_status=outstanding",
        text=f'{{"us_treasuries": [{_TREASURY_JSON}]}}',
    )

    result = trading_client.get_us_treasuries(
        GetUSTreasuriesRequest(bond_status=BondStatus.OUTSTANDING)
    )

    assert reqmock.called_once
    assert isinstance(result, USTreasuriesResp)


def test_get_us_treasuries_with_cusips(reqmock, trading_client: TradingClient):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/assets/fixed_income/us_treasuries?cusips=912810UG1%2C912797PM3",
        text=f'{{"us_treasuries": [{_TREASURY_JSON}]}}',
    )

    result = trading_client.get_us_treasuries(
        GetUSTreasuriesRequest(cusips="912810UG1,912797PM3")
    )

    assert reqmock.called_once
    assert isinstance(result, USTreasuriesResp)


def test_get_us_treasuries_empty(reqmock, trading_client: TradingClient):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/assets/fixed_income/us_treasuries",
        text='{"us_treasuries": []}',
    )

    result = trading_client.get_us_treasuries()

    assert isinstance(result, USTreasuriesResp)
    assert result.us_treasuries == []


def test_get_us_treasuries_raw(reqmock, trading_client_raw: TradingClient):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/assets/fixed_income/us_treasuries",
        text=f'{{"us_treasuries": [{_TREASURY_JSON}]}}',
    )

    result = trading_client_raw.get_us_treasuries()

    assert isinstance(result, dict)
    assert "us_treasuries" in result


# ---------------------------------------------------------------------------
# US Corporates
# ---------------------------------------------------------------------------


def test_get_us_corporates_no_filter(reqmock, trading_client: TradingClient):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/assets/fixed_income/us_corporates",
        text=f'{{"us_corporates": [{_CORPORATE_JSON}]}}',
    )

    result = trading_client.get_us_corporates()

    assert reqmock.called_once
    assert isinstance(result, USCorporatesResp)
    assert len(result.us_corporates) == 1
    assert isinstance(result.us_corporates[0], USCorporate)
    assert result.us_corporates[0].cusip == "38141GXZ2"
    assert result.us_corporates[0].ticker == "GS"
    assert result.us_corporates[0].bond_status == BondStatus.OUTSTANDING


def test_get_us_corporates_with_tickers(reqmock, trading_client: TradingClient):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/assets/fixed_income/us_corporates?tickers=GS%2CJPM",
        text=f'{{"us_corporates": [{_CORPORATE_JSON}]}}',
    )

    result = trading_client.get_us_corporates(GetUSCorporatesRequest(tickers="GS,JPM"))

    assert reqmock.called_once
    assert isinstance(result, USCorporatesResp)


def test_get_us_corporates_with_bond_status(reqmock, trading_client: TradingClient):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/assets/fixed_income/us_corporates?bond_status=outstanding",
        text=f'{{"us_corporates": [{_CORPORATE_JSON}]}}',
    )

    result = trading_client.get_us_corporates(
        GetUSCorporatesRequest(bond_status=BondStatus.OUTSTANDING)
    )

    assert reqmock.called_once
    assert isinstance(result, USCorporatesResp)


def test_get_us_corporates_empty(reqmock, trading_client: TradingClient):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/assets/fixed_income/us_corporates",
        text='{"us_corporates": []}',
    )

    result = trading_client.get_us_corporates()

    assert isinstance(result, USCorporatesResp)
    assert result.us_corporates == []


def test_get_us_corporates_raw(reqmock, trading_client_raw: TradingClient):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER.value}/v2/assets/fixed_income/us_corporates",
        text=f'{{"us_corporates": [{_CORPORATE_JSON}]}}',
    )

    result = trading_client_raw.get_us_corporates()

    assert isinstance(result, dict)
    assert "us_corporates" in result
