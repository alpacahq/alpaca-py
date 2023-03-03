from typing import List

from alpaca.common.enums import BaseURL
from alpaca.trading.enums import CorporateActionType
from alpaca.trading.models import (
    CorporateActionAnnouncement,
)
from alpaca.trading.requests import GetCorporateAnnouncementsRequest
from alpaca.trading.client import TradingClient


def test_get_announcements(reqmock, trading_client: TradingClient):
    reqmock.get(
        f"{BaseURL.TRADING_PAPER}/v2/corporate_actions/announcements",
        text="""
        [
          {
            "id": "be3c368a-4c7c-4384-808e-f02c9f5a8afe",
            "corporate_action_id": "F58684224_XY37",
            "ca_type": "dividend",
            "ca_sub_type": "cash",
            "initiating_symbol": "MLLAX",
            "initiating_original_cusip": "55275E101",
            "target_symbol": "MLLAX",
            "target_original_cusip": "55275E101",
            "declaration_date": "2021-01-05",
            "ex_date": "2022-07-18",
            "expiration_date": "2021-01-12",
            "record_date": "2021-01-13",
            "payable_date": "2021-01-14",
            "cash": "0.018",
            "old_rate": "1",
            "new_rate": "1"
          },
          {
            "id": "be3c368a-4c7c-4384-808e-f02c9f5a8afe",
            "corporate_action_id": "48251W104_AD21",
            "ca_type": "dividend",
            "ca_sub_type": "cash",
            "initiating_symbol": "KKR",
            "initiating_original_cusip": "G52830109",
            "target_symbol": "KKR",
            "target_original_cusip": "G52830109",
            "declaration_date": "2021-11-01",
            "ex_date": "2021-11-12",
            "record_date": "2021-11-15",
            "payable_date": "2021-11-30",
            "cash": "0.145",
            "old_rate": "1",
            "new_rate": "1"
          }
        ]
      """,
    )

    ca_filter = GetCorporateAnnouncementsRequest(
        ca_types=[CorporateActionType.DIVIDEND], since="2021-01-01", until="2021-02-01"
    )

    response = trading_client.get_corporate_announcements(ca_filter)

    assert reqmock.called_once
    assert isinstance(response, List)
    assert len(response) > 0
    assert isinstance(response[0], CorporateActionAnnouncement)
