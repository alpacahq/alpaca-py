from alpaca.broker.client import BrokerClient
from alpaca.common.enums import BaseURL
from alpaca.broker.enums import CommissionType
from alpaca.trading.enums import OrderSide, OrderStatus, TimeInForce
from alpaca.broker.requests import (
    MarketOrderRequest,
)
from alpaca.broker.models import Order


def test_order_commission_type(reqmock, client: BrokerClient):
    account_id = "0d969814-40d6-4b2b-99ac-2e37427f1ad2"

    # 1. commission_type notional per order
    def match_request_json(request):
        return request.json() == {
            "symbol": "SPY",
            "qty": 1.0,
            "side": "buy",
            "type": "market",
            "time_in_force": "day",
            "commission": 1.25,
            "commission_type": "notional",
        }

    reqmock.post(
        f"{BaseURL.BROKER_SANDBOX.value}/v1/trading/accounts/{account_id}/orders",
        additional_matcher=match_request_json,
        text="""
        {
          "id": "61e69015-8549-4bfd-b9c3-01e75843f47d",
          "client_order_id": "eb9e2aaa-f71a-4f51-b5b4-52a6c565dad4",
          "created_at": "2021-03-16T18:38:01.942282Z",
          "updated_at": "2021-03-16T18:38:01.942282Z",
          "submitted_at": "2021-03-16T18:38:01.937734Z",
          "filled_at": null,
          "expired_at": null,
          "canceled_at": null,
          "failed_at": null,
          "replaced_at": null,
          "replaced_by": null,
          "replaces": null,
          "asset_id": "b4695157-0d1d-4da0-8f9e-5c53149389e4",
          "symbol": "SPY`",
          "asset_class": "us_equity",
          "notional": null,
          "qty": 1,
          "filled_qty": "0",
          "filled_avg_price": null,
          "order_class": "simple",
          "order_type": "market",
          "type": "market",
          "side": "buy",
          "time_in_force": "day",
          "limit_price": null,
          "stop_price": null,
          "status": "accepted",
          "extended_hours": false,
          "legs": null,
          "trail_percent": null,
          "trail_price": null,
          "hwm": null,
          "commission": 1.25,
          "commission_type": "notional"
        }
        """,
    )

    mo = MarketOrderRequest(
        symbol="SPY",
        side=OrderSide.BUY,
        time_in_force=TimeInForce.DAY,
        qty=1,
        commission=1.25,
        commission_type=CommissionType.NOTIONAL,
    )

    assert mo.commission_type == CommissionType.NOTIONAL

    mo_response = client.submit_order_for_account(account_id, mo)

    assert reqmock.called_once
    assert isinstance(mo_response, Order)
    assert mo_response.status == OrderStatus.ACCEPTED
    assert mo_response.commission == 1.25
    assert mo_response.commission_type == CommissionType.NOTIONAL

    # 2. commission_type bps
    def match_request_json(request):
        return request.json() == {
            "symbol": "SPY",
            "qty": 1.0,
            "side": "buy",
            "type": "market",
            "time_in_force": "day",
            "commission": 1.25,
            "commission_type": "bps",
        }

    reqmock.post(
        f"{BaseURL.BROKER_SANDBOX.value}/v1/trading/accounts/{account_id}/orders",
        additional_matcher=match_request_json,
        text="""
        {
          "id": "61e69015-8549-4bfd-b9c3-01e75843f48d",
          "client_order_id": "eb9e2aaa-f71a-4f51-b5b4-52a6c565dad4",
          "created_at": "2021-03-16T18:38:01.942282Z",
          "updated_at": "2021-03-16T18:38:01.942282Z",
          "submitted_at": "2021-03-16T18:38:01.937734Z",
          "filled_at": null,
          "expired_at": null,
          "canceled_at": null,
          "failed_at": null,
          "replaced_at": null,
          "replaced_by": null,
          "replaces": null,
          "asset_id": "b4695157-0d1d-4da0-8f9e-5c53149389e4",
          "symbol": "SPY`",
          "asset_class": "us_equity",
          "notional": null,
          "qty": 1,
          "filled_qty": "0",
          "filled_avg_price": null,
          "order_class": "simple",
          "order_type": "market",
          "type": "market",
          "side": "buy",
          "time_in_force": "day",
          "limit_price": null,
          "stop_price": null,
          "status": "accepted",
          "extended_hours": false,
          "legs": null,
          "trail_percent": null,
          "trail_price": null,
          "hwm": null,
          "commission": 1.25,
          "commission_type": "bps"
        }
        """,
    )

    mo = MarketOrderRequest(
        symbol="SPY",
        side=OrderSide.BUY,
        time_in_force=TimeInForce.DAY,
        qty=1,
        commission=1.25,
        commission_type=CommissionType.BPS,
    )

    assert mo.commission_type == CommissionType.BPS

    mo_response = client.submit_order_for_account(account_id, mo)

    assert reqmock.call_count == 2
    assert isinstance(mo_response, Order)
    assert mo_response.status == OrderStatus.ACCEPTED
    assert mo_response.commission == 1.25
    assert mo_response.commission_type == CommissionType.BPS

    # 3. commission_type per qty
    def match_request_json(request):
        return request.json() == {
            "symbol": "SPY",
            "qty": 1.0,
            "side": "buy",
            "type": "market",
            "time_in_force": "day",
            "commission": 1.25,
            "commission_type": "qty",
        }

    reqmock.post(
        f"{BaseURL.BROKER_SANDBOX.value}/v1/trading/accounts/{account_id}/orders",
        text="""
        {
          "id": "61e69015-8549-4bfd-b9c3-01e75843f49d",
          "client_order_id": "eb9e2aaa-f71a-4f51-b5b4-52a6c565dad4",
          "created_at": "2021-03-16T18:38:01.942282Z",
          "updated_at": "2021-03-16T18:38:01.942282Z",
          "submitted_at": "2021-03-16T18:38:01.937734Z",
          "filled_at": null,
          "expired_at": null,
          "canceled_at": null,
          "failed_at": null,
          "replaced_at": null,
          "replaced_by": null,
          "replaces": null,
          "asset_id": "b4695157-0d1d-4da0-8f9e-5c53149389e4",
          "symbol": "SPY`",
          "asset_class": "us_equity",
          "notional": null,
          "qty": 3,
          "filled_qty": "0",
          "filled_avg_price": null,
          "order_class": "simple",
          "order_type": "market",
          "type": "market",
          "side": "buy",
          "time_in_force": "day",
          "limit_price": null,
          "stop_price": null,
          "status": "accepted",
          "extended_hours": false,
          "legs": null,
          "trail_percent": null,
          "trail_price": null,
          "hwm": null,
          "commission": 1.25,
          "commission_type": "qty"
        }
        """,
    )

    mo = MarketOrderRequest(
        symbol="SPY",
        side=OrderSide.BUY,
        time_in_force=TimeInForce.DAY,
        qty=1,
        commission=1.25,
        commission_type=CommissionType.QTY,
    )

    assert mo.commission_type == CommissionType.QTY

    mo_response = client.submit_order_for_account(account_id, mo)

    assert reqmock.call_count == 3
    assert isinstance(mo_response, Order)
    assert mo_response.status == OrderStatus.ACCEPTED
    assert mo_response.commission == 1.25
    assert mo_response.commission_type == CommissionType.QTY
