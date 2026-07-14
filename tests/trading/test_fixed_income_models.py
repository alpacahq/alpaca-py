from datetime import date

from alpaca.trading.enums import (
    BondStatus,
    CallType,
    CouponFrequency,
    CouponType,
    DayCount,
    SpOutlook,
    TreasurySubtype,
)
from alpaca.trading.models import (
    USCorporate,
    USCorporatesResp,
    USTreasuriesResp,
    USTreasury,
)
from alpaca.trading.requests import GetUSCorporatesRequest, GetUSTreasuriesRequest


def test_fixed_income_enum_values():
    assert BondStatus.PRE_ISSUANCE == "pre_issuance"
    assert CallType.MAKE_WHOLE == "make_whole"
    assert CouponFrequency.SEMI_ANNUAL == "semi_annual"
    assert CouponType.FLOATING == "floating"
    assert DayCount.THIRTY_E_360 == "30E/360"
    assert SpOutlook.NOT_MEANINGFUL == "not_meaningful"
    assert TreasurySubtype.TIPS == "tips"


def test_us_treasury_response_parses_security():
    response = USTreasuriesResp(
        us_treasuries=[
            {
                "cusip": "91282CJL6",
                "isin": "US91282CJL63",
                "bond_status": "outstanding",
                "tradable": True,
                "subtype": "note",
                "issue_date": "2024-05-15",
                "maturity_date": "2034-05-15",
                "description": "US TREASURY N/B",
                "description_short": "UST 4.375 05/15/34",
                "coupon": 4.375,
                "coupon_type": "fixed",
                "coupon_frequency": "semi_annual",
                "close_price": 101.25,
            }
        ]
    )

    treasury = response.us_treasuries[0]
    assert isinstance(treasury, USTreasury)
    assert treasury.issue_date == date(2024, 5, 15)
    assert treasury.subtype is TreasurySubtype.NOTE
    assert treasury.close_price == 101.25
    assert treasury.next_coupon_date is None


def test_us_corporate_response_parses_security():
    response = USCorporatesResp(
        us_corporates=[
            {
                "cusip": "594918CV0",
                "isin": "US594918CV00",
                "bond_status": "outstanding",
                "tradable": True,
                "marginable": False,
                "issue_date": "2023-11-03",
                "country_domicile": "US",
                "ticker": "MSFT",
                "seniority": "senior",
                "issuer": "Microsoft Corporation",
                "sector": "technology",
                "description": "MICROSOFT CORP",
                "description_short": "MSFT 4.2 11/03/35",
                "coupon": 4.2,
                "coupon_type": "fixed",
                "coupon_frequency": "semi_annual",
                "perpetual": False,
                "day_count": "30/360",
                "dated_date": "2023-11-03",
                "issue_size": 3_000_000_000,
                "issue_price": 99.8,
                "issue_minimum_denomination": 1_000,
                "par_value": 1_000,
                "callable": True,
                "puttable": False,
                "convertible": False,
                "reg_s": False,
                "call_type": "make_whole",
                "sp_outlook": "stable",
            }
        ]
    )

    corporate = response.us_corporates[0]
    assert isinstance(corporate, USCorporate)
    assert corporate.day_count is DayCount.THIRTY_360
    assert corporate.call_type is CallType.MAKE_WHOLE
    assert corporate.sp_outlook is SpOutlook.STABLE
    assert corporate.maturity_date is None


def test_fixed_income_requests_parse_filters():
    treasury_request = GetUSTreasuriesRequest(
        subtype="bill", bond_status="outstanding", cusips="912797PM3"
    )
    corporate_request = GetUSCorporatesRequest(
        bond_status=BondStatus.OUTSTANDING, tickers="MSFT"
    )

    assert treasury_request.subtype is TreasurySubtype.BILL
    assert treasury_request.bond_status is BondStatus.OUTSTANDING
    assert corporate_request.tickers == "MSFT"


def test_fixed_income_requests_omit_unset_filters():
    assert GetUSTreasuriesRequest().to_request_fields() == {}
    assert GetUSCorporatesRequest().to_request_fields() == {}
