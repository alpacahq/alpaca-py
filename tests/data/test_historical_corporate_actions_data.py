import urllib
from datetime import date, timezone

from alpaca.data.enums import CorporateActionsType
from alpaca.data.historical.corporate_actions import CorporateActionsClient
from alpaca.data.models.corporate_actions import CorporateActionsSet
from alpaca.data.requests import CorporateActionsRequest


def test_get_corporate_actions(
    reqmock, corporate_actions_client: CorporateActionsClient
):
    # requests and response may not match as to check requests parameter conversion
    symbols = ["AAPL", "TSLA"]
    _symbols_in_url = urllib.parse.quote_plus(",".join(symbols))
    types = [CorporateActionsType.CASH_DIVIDEND, CorporateActionsType.FORWARD_SPLIT]
    _types_in_url = urllib.parse.quote_plus(",".join(types))
    start = date(2022, 2, 1)
    _start_in_url = urllib.parse.quote_plus(
        start.isoformat(),
    )
    sort = "asc"
    limit = 1000

    limit2 = 987
    page_token = (
        "MDA3Q1ZSMDIwfDIwMjQtMDItMTV8NjBiZjkxYzItMDc0Ni00ZDliLThjOWUtYTgwYmIzMDhmZDkx"
    )
    _page_token_in_url = urllib.parse.quote_plus(page_token)

    reqmock.get(
        f"https://data.alpaca.markets/v1beta1/corporate-actions?symbols={_symbols_in_url}&types={_types_in_url}&start={_start_in_url}&sort={sort}&limit={limit}",
        text="""
{
  "corporate_actions": {
    "reverse_splits": [
      {
        "ex_date": "2023-08-24",
        "new_rate": 1,
        "old_rate": 50,
        "process_date": "2023-08-24",
        "record_date": "2023-08-24",
        "symbol": "MNTS"
      }
    ],
    "forward_splits": [
      {
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
        "alternate_rate": 0.3333,
        "alternate_symbol": "LVROW",
        "effective_date": "2023-03-01",
        "new_rate": 1,
        "new_symbol": "LVRO",
        "old_rate": 1,
        "old_symbol": "TPBAU",
        "process_date": "2023-03-01"
      }
    ],
    "stock_dividends": [
      {
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
        "ex_date": "2023-08-15",
        "new_rate": 1,
        "new_symbol": "SRM",
        "process_date": "2023-08-15",
        "record_date": "2023-08-15",
        "source_rate": 19.35,
        "source_symbol": "JUPW"
      }
    ],
    "cash_mergers": [
      {
        "acquiree_symbol": "GLOP",
        "effective_date": "2023-07-17",
        "payable_date": "2023-07-17",
        "process_date": "2023-07-17",
        "rate": 5.37
      }
    ],
    "stock_mergers": [
      {
        "acquiree_rate": 1,
        "acquiree_symbol": "LSI",
        "acquirer_rate": 0.895,
        "acquirer_symbol": "EXR",
        "effective_date": "2023-07-20",
        "payable_date": "2023-07-20",
        "process_date": "2023-07-20"
      }
    ],
    "stock_and_cash_mergers": [
      {
        "acquiree_rate": 1,
        "acquiree_symbol": "MLVF",
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
        "payable_date": "2023-06-13",
        "process_date": "2023-06-13",
        "rate": 0.141134,
        "symbol": "ORPHY"
      }
    ],
    "name_changes": [
      {
        "new_symbol": "VFS",
        "old_symbol": "BSAQ",
        "process_date": "2023-08-15"
      }
    ],
    "worthless_removals": [
      {
        "symbol": "ATNXQ",
        "process_date": "2023-10-11"
      }
    ],
    "rights_distributions": [
      {
        "source_symbol": "IFN",
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
    reqmock.get(
        f"https://data.alpaca.markets/v1beta1/corporate-actions?symbols={_symbols_in_url}&types={_types_in_url}&start={_start_in_url}&sort={sort}&limit={limit2}&page_token={_page_token_in_url}",
        text="""
{
  "corporate_actions": {
    "cash_dividends": [
      {
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
    )

    res = corporate_actions_client.get_corporate_actions(request_params=req)

    assert isinstance(res, CorporateActionsSet)

    assert res["reverse_splits"][0].symbol == "MNTS"
    assert res["forward_splits"][0].symbol == "SRE"
    assert res["unit_splits"][0].old_symbol == "TPBAU"
    assert res["stock_dividends"][0].symbol == "MSBC"
    assert res["cash_dividends"][0].symbol == "FCF"
    assert res["cash_dividends"][1].symbol == "ZMTBY"
    assert res["spin_offs"][0].source_symbol == "JUPW"
    assert res["cash_mergers"][0].acquiree_symbol == "GLOP"
    assert res["stock_mergers"][0].acquirer_symbol == "EXR"
    assert res["stock_and_cash_mergers"][0].acquirer_symbol == "FRBA"
    assert res["redemptions"][0].symbol == "ORPHY"
    assert res["name_changes"][0].old_symbol == "BSAQ"
    assert res["worthless_removals"][0].symbol == "ATNXQ"
    assert res["rights_distributions"][0].source_symbol == "IFN"
    assert res["rights_distributions"][0].new_symbol == "IFN.RTWI"

    assert res.df.index[0] == ("reverse_splits", date(2023, 8, 24))

    assert reqmock.call_count == 2
