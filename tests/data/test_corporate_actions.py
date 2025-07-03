import urllib
from datetime import date
from uuid import UUID

from alpaca.data.enums import CorporateActionsType
from alpaca.data.historical.corporate_actions import CorporateActionsClient
from alpaca.data.models.corporate_actions import (
    CashDividend,
    CorporateActionsSet,
    ForwardSplit,
    ReverseSplit,
    StockDividend,
    UnitSplit,
)
from alpaca.data.requests import CorporateActionsRequest


def test_get_corporate_actions(
    reqmock, corporate_actions_client: CorporateActionsClient
):
    # requests and response may not match as to check requests parameter conversion
    symbols = ["AAPL", "TSLA"]
    _symbols_in_url = urllib.parse.quote_plus(",".join(symbols))
    cusips = ["CUSIP1", "CUSIP2"]
    _cusips_in_url = urllib.parse.quote_plus(",".join(cusips))
    types = [CorporateActionsType.CASH_DIVIDEND, CorporateActionsType.FORWARD_SPLIT]
    _types_in_url = urllib.parse.quote_plus(",".join(types))
    start = date(2022, 2, 1)
    _start_in_url = urllib.parse.quote_plus(
        start.isoformat(),
    )
    ids = [
        "a7932b15-f816-4f83-921e-998b524487b0",
        "a7932b15-f816-4f83-921e-998b524487b1",
    ]
    _ids_in_url = urllib.parse.quote_plus(",".join(ids))
    sort = "asc"
    limit = 1000
    reqmock.get(
        f"https://data.alpaca.markets/v1/corporate-actions?symbols={_symbols_in_url}&cusips={_cusips_in_url}&types={_types_in_url}&start={_start_in_url}&ids={_ids_in_url}&sort={sort}&limit={limit}",
        text="""
{
  "corporate_actions": {
    "reverse_splits": [
      {
        "id": "a7932b15-f816-4f83-921e-998b524487b0",
        "ex_date": "2023-08-24",
        "new_rate": 1,
        "old_rate": 50,
        "new_cusip": "NEWCUSIP1",
        "old_cusip": "OLDCUSIP1",
        "process_date": "2023-08-24",
        "record_date": "2023-08-24",
        "symbol": "MNTS"
      }
    ],
    "forward_splits": [
      {
        "cusip": "CUSIP1",
        "id": "a7932b15-f816-4f83-921e-998b524487b1",
        "due_bill_redemption_date": "2023-08-23",
        "ex_date": "2023-08-22",
        "new_rate": 2,
        "old_rate": 1,
        "payable_date": "2023-08-21",
        "process_date": "2023-08-22",
        "record_date": "2023-08-14",
        "symbol": "SRE"
      }
    ],
    "unit_splits": [
      {
        "id": "a7932b15-f816-4f83-921e-998b524487b2",
        "alternate_cusip": "ALTCUSIP1",
        "alternate_rate": 0.3333,
        "alternate_symbol": "LVROW",
        "effective_date": "2023-03-01",
        "new_cusip": "NEWCUSIP1",
        "new_rate": 1,
        "new_symbol": "LVRO",
        "old_cusip": "OLDCUSIP1",
        "old_rate": 1,
        "old_symbol": "TPBAU",
        "process_date": "2023-03-01"
      }
    ],
    "stock_dividends": [
      {
        "cusip": "CUSIP1",
        "id": "a7932b15-f816-4f83-921e-998b524487b3",
        "ex_date": "2023-05-19",
        "payable_date": "2023-05-05",
        "process_date": "2023-05-19",
        "rate": 0.05,
        "record_date": "2023-05-22",
        "symbol": "MSBC"
      }
    ],
    "cash_dividends": [
      {
        "cusip": "CUSIP1",
        "id": "a7932b15-f816-4f83-921e-998b524487b4",
        "ex_date": "2023-05-04",
        "foreign": false,
        "payable_date": "2023-05-19",
        "process_date": "2023-05-19",
        "rate": 0.125,
        "record_date": "2023-05-05",
        "special": false,
        "symbol": "FCF"
      }
    ],
    "spin_offs": [
      {
        "id": "a7932b15-f816-4f83-921e-998b524487b5",
        "ex_date": "2023-08-15",
        "new_cusip": "NEWCUSIP1",
        "new_rate": 1,
        "new_symbol": "SRM",
        "process_date": "2023-08-15",
        "record_date": "2023-08-15",
        "source_cusip": "SOURCECUSIP1",
        "source_rate": 19.35,
        "source_symbol": "JUPW"
      }
    ],
    "cash_mergers": [
      {
        "id": "a7932b15-f816-4f83-921e-998b524487b6",
        "acquiree_symbol": "GLOP",
        "acquiree_cusip": "ACQUIREECUSIP1",
        "effective_date": "2023-07-17",
        "payable_date": "2023-07-17",
        "process_date": "2023-07-17",
        "rate": 5.37
      }
    ],
    "stock_mergers": [
      {
        "id": "a7932b15-f816-4f83-921e-998b524487b7",
        "acquiree_cusip": "ACQUIREECUSIP1",
        "acquiree_rate": 1,
        "acquiree_symbol": "LSI",
        "acquirer_cusip": "ACQUIRERCUSIP1",
        "acquirer_rate": 0.895,
        "acquirer_symbol": "EXR",
        "effective_date": "2023-07-20",
        "payable_date": "2023-07-20",
        "process_date": "2023-07-20"
      }
    ],
    "stock_and_cash_mergers": [
      {
        "id": "a7932b15-f816-4f83-921e-998b524487b8",
        "acquiree_cusip": "ACQUIREECUSIP1",
        "acquiree_rate": 1,
        "acquiree_symbol": "MLVF",
        "acquirer_cusip": "ACQUIRERCUSIP1",
        "acquirer_rate": 0.7733,
        "acquirer_symbol": "FRBA",
        "cash_rate": 7.8,
        "effective_date": "2023-07-18",
        "payable_date": "2023-07-18",
        "process_date": "2023-07-18"
      }
    ],
    "redemptions": [
      {
        "id": "a7932b15-f816-4f83-921e-998b524487b9",
        "payable_date": "2023-06-13",
        "process_date": "2023-06-13",
        "cusip": "CUSIP1",
        "rate": 0.141134,
        "symbol": "ORPHY"
      }
    ],
    "name_changes": [
      {
        "id": "a7932b15-f816-4f83-921e-998b524487c0",
        "new_cusip": "NEWCUSIP1",
        "new_symbol": "VFS",
        "old_cusip": "OLDCUSIP1",
        "old_symbol": "BSAQ",
        "process_date": "2023-08-15"
      }
    ],
    "worthless_removals": [
      {
        "id": "a7932b15-f816-4f83-921e-998b524487c1",
        "cusip": "CUSIP1",
        "symbol": "ATNXQ",
        "process_date": "2023-10-11"
      }
    ],
    "rights_distributions": [
      {
        "id": "a7932b15-f816-4f83-921e-998b524487c2",
        "source_cusip": "SOURCECUSIP1",
        "source_symbol": "IFN",
        "new_cusip": "NEWCUSIP1",
        "new_symbol": "IFN.RTWI",
        "rate": 1,
        "ex_date": "2024-04-17",
        "record_date": "2024-04-18",
        "payable_date": "2024-04-19",
        "process_date": "2024-04-19",
        "expiration_date": "2024-05-14"
      }
    ]
  },
  "next_page_token": "MDA3Q1ZSMDIwfDIwMjQtMDItMTV8NjBiZjkxYzItMDc0Ni00ZDliLThjOWUtYTgwYmIzMDhmZDkx"
}
        """,
    )
    limit2 = 987
    page_token = (
        "MDA3Q1ZSMDIwfDIwMjQtMDItMTV8NjBiZjkxYzItMDc0Ni00ZDliLThjOWUtYTgwYmIzMDhmZDkx"
    )
    _page_token_in_url = urllib.parse.quote_plus(page_token)
    reqmock.get(
        f"https://data.alpaca.markets/v1/corporate-actions?symbols={_symbols_in_url}&cusips={_cusips_in_url}&types={_types_in_url}&start={_start_in_url}&ids={_ids_in_url}&sort={sort}&limit={limit2}&page_token={_page_token_in_url}",
        text="""
{
  "corporate_actions": {
    "cash_dividends": [
      {
        "cusip": "CUSIP1",
        "id": "a7932b15-f816-4f83-921e-998b524487c3",
        "ex_date": "2024-08-07",
        "foreign": true,
        "payable_date": "2024-08-26",
        "process_date": "2024-08-26",
        "rate": 0.086928,
        "record_date": "2024-08-07",
        "special": false,
        "symbol": "ZMTBY"
      }
    ]
  },
  "next_page_token": null
}
        """,
    )

    req = CorporateActionsRequest(
        symbols=symbols,
        types=types,
        start=start,
        cusips=cusips,
        ids=ids,
    )

    res = corporate_actions_client.get_corporate_actions(request_params=req)

    assert isinstance(res, CorporateActionsSet)

    reverse_split: ReverseSplit = res["reverse_splits"][0]
    assert reverse_split.id == UUID("a7932b15-f816-4f83-921e-998b524487b0")
    assert reverse_split.symbol == "MNTS"
    assert reverse_split.new_cusip == "NEWCUSIP1"
    assert reverse_split.old_cusip == "OLDCUSIP1"
    assert reverse_split.new_rate == 1
    assert reverse_split.old_rate == 50
    assert reverse_split.ex_date == date(2023, 8, 24)
    assert reverse_split.process_date == date(2023, 8, 24)
    assert reverse_split.record_date == date(2023, 8, 24)

    forward_split: ForwardSplit = res["forward_splits"][0]
    assert forward_split.id == UUID("a7932b15-f816-4f83-921e-998b524487b1")
    assert forward_split.symbol == "SRE"
    assert forward_split.cusip == "CUSIP1"
    assert forward_split.new_rate == 2
    assert forward_split.old_rate == 1
    assert forward_split.record_date == date(2023, 8, 14)
    assert forward_split.payable_date == date(2023, 8, 21)
    assert forward_split.ex_date == date(2023, 8, 22)
    assert forward_split.process_date == date(2023, 8, 22)
    assert forward_split.due_bill_redemption_date == date(2023, 8, 23)

    unit_split: UnitSplit = res["unit_splits"][0]
    assert unit_split.id == UUID("a7932b15-f816-4f83-921e-998b524487b2")
    assert unit_split.old_symbol == "TPBAU"
    assert unit_split.old_cusip == "OLDCUSIP1"
    assert unit_split.old_rate == 1
    assert unit_split.new_symbol == "LVRO"
    assert unit_split.new_cusip == "NEWCUSIP1"
    assert unit_split.new_rate == 1
    assert unit_split.alternate_symbol == "LVROW"
    assert unit_split.alternate_cusip == "ALTCUSIP1"
    assert unit_split.alternate_rate == 0.3333
    assert unit_split.effective_date == date(2023, 3, 1)
    assert unit_split.process_date == date(2023, 3, 1)

    stock_dividend: StockDividend = res["stock_dividends"][0]
    assert stock_dividend.id == UUID("a7932b15-f816-4f83-921e-998b524487b3")
    assert stock_dividend.symbol == "MSBC"
    assert stock_dividend.cusip == "CUSIP1"
    assert stock_dividend.rate == 0.05
    assert stock_dividend.payable_date == date(2023, 5, 5)
    assert stock_dividend.ex_date == date(2023, 5, 19)
    assert stock_dividend.process_date == date(2023, 5, 19)
    assert stock_dividend.record_date == date(2023, 5, 22)

    cash_dividend: CashDividend = res["cash_dividends"][0]
    assert cash_dividend.id == UUID("a7932b15-f816-4f83-921e-998b524487b4")
    assert cash_dividend.cusip == "CUSIP1"
    assert cash_dividend.symbol == "FCF"
    assert cash_dividend.rate == 0.125
    assert not cash_dividend.foreign
    assert not cash_dividend.special
    assert cash_dividend.ex_date == date(2023, 5, 4)
    assert cash_dividend.record_date == date(2023, 5, 5)
    assert cash_dividend.payable_date == date(2023, 5, 19)
    assert cash_dividend.process_date == date(2023, 5, 19)

    cash_dividend = res["cash_dividends"][1]
    cash_dividend.symbol == "ZMTBY"

    assert res["cash_mergers"][0].acquiree_symbol == "GLOP"
    assert res["stock_mergers"][0].acquirer_symbol == "EXR"
    assert res["stock_and_cash_mergers"][0].acquirer_symbol == "FRBA"
    assert res["redemptions"][0].symbol == "ORPHY"
    assert res["name_changes"][0].old_symbol == "BSAQ"
    assert res["worthless_removals"][0].symbol == "ATNXQ"
    assert res["rights_distributions"][0].source_symbol == "IFN"
    assert res["rights_distributions"][0].new_symbol == "IFN.RTWI"

    assert res.df.index[0] == "reverse_splits"

    assert reqmock.call_count == 2
