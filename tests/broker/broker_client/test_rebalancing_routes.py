from requests_mock import Mocker
from alpaca.broker.client import BrokerClient
from alpaca.broker.models.rebalancing import Portfolio
from alpaca.broker.requests import CreatePortfolioRequest
from alpaca.common.enums import BaseURL


def test_create_portfolio(reqmock: Mocker, client: BrokerClient) -> None:
    """Test to create a portfolio."""
    reqmock.post(
        f"{BaseURL.BROKER_SANDBOX.value}/v1/rebalancing/portfolios",
        text="""
        {
            "id": "6819ecd2-db92-4688-821d-8fac2a8f4744",
            "name": "Balanced",
            "description": "A balanced portfolio of stocks and bonds",
            "status": "active",
            "cooldown_days": 7,
            "created_at": "2022-08-06T19:12:13.555858187-04:00",
            "updated_at": "2022-08-06T19:12:13.628551899-04:00",
            "weights": [
                {
                    "type": "cash",
                    "symbol": null,
                    "percent": "5"
                },
                {
                    "type": "asset",
                    "symbol": "SPY",
                    "percent": "60"
                },
                {
                    "type": "asset",
                    "symbol": "TLT",
                    "percent": "35"
                }
            ],
            "rebalance_conditions": [
                {
                    "type": "drift_band",
                    "sub_type": "absolute",
                    "percent": "5",
                    "day": null
                },
                {
                    "type": "drift_band",
                    "sub_type": "relative",
                    "percent": "20",
                    "day": null
                }
            ]
        }
        """,
    )

    portfolio_request = CreatePortfolioRequest(
        **{
            "name": "Balanced",
            "description": "A balanced portfolio of stocks and bonds",
            "weights": [
                {"type": "cash", "percent": "5"},
                {"type": "asset", "symbol": "SPY", "percent": "60"},
                {"type": "asset", "symbol": "TLT", "percent": "35"},
            ],
            "cooldown_days": 7,
            "rebalance_conditions": [
                {"type": "drift_band", "sub_type": "absolute", "percent": "5"},
                {"type": "drift_band", "sub_type": "relative", "percent": "20"},
            ],
        }
    )
    ptf = client.create_portfolio(portfolio_request)

    assert reqmock.called_once
    assert isinstance(ptf, Portfolio)
