import pytest

from alpaca.broker.client import BrokerClient
from alpaca.common.enums import BaseURL
from alpaca.trading.enums import CorporateActionType
from alpaca.trading.requests import GetCorporateAnnouncementsRequest


def test_get_corporate_announcements_is_deprecated(reqmock, client: BrokerClient):
    reqmock.get(
        f"{BaseURL.BROKER_SANDBOX.value}/v1/corporate_actions/announcements",
        text="[]",
    )
    ca_filter = GetCorporateAnnouncementsRequest(
        ca_types=[CorporateActionType.DIVIDEND.value],
        since="2021-01-01",
        until="2021-02-01",
    )

    with pytest.deprecated_call(match="get_corporate_actions") as caught:
        assert client.get_corporate_announcements(ca_filter) == []

    assert caught[0].filename == __file__
    assert BrokerClient.get_corporate_announcements.__deprecated__.startswith(
        "get_corporate_announcements is deprecated"
    )


def test_get_corporate_announcement_by_id_is_deprecated(reqmock, client: BrokerClient):
    announcement_id = "be3c368a-4c7c-4384-808e-f02c9f5a8afe"
    reqmock.get(
        f"{BaseURL.BROKER_SANDBOX.value}/v1/corporate_actions/announcements/{announcement_id}",
        json={
            "id": announcement_id,
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
            "new_rate": "1",
        },
    )

    with pytest.deprecated_call(match="get_corporate_actions") as caught:
        client.get_corporate_announcement_by_id(announcement_id)

    assert caught[0].filename == __file__
    assert BrokerClient.get_corporate_announcement_by_id.__deprecated__.startswith(
        "get_corporate_announcement_by_id is deprecated"
    )
