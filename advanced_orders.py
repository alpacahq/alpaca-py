import os
import requests
from typing import Optional, Literal

from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, root_validator

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass
from alpaca.trading.requests import (
    MarketOrderRequest,
    LimitOrderRequest,
    StopOrderRequest,
    TrailingStopOrderRequest,
    TakeProfitRequest,
    StopLossRequest,
)
from alpaca.common.exceptions import APIError

router = APIRouter()

def _client() -> TradingClient:
    key = os.getenv("APCA_API_KEY_ID")
    sec = os.getenv("APCA_API_SECRET_KEY")
    paper = "paper" in (os.getenv("APCA_API_BASE_URL", "") or "").lower()
    return TradingClient(key, sec, paper=paper)

def _side(s: str) -> OrderSide:
    s = (s or "").lower()
    if s == "buy":
        return OrderSide.BUY
    if s == "sell":
        return OrderSide.SELL
    raise HTTPException(status_code=400, detail="side must be 'buy' or 'sell'")

def _tif(t: str) -> TimeInForce:
    try:
        return TimeInForce[(t or "day").upper()]
    except Exception:
        raise HTTPException(status_code=400, detail="invalid time_in_force")

class TakeProfit(BaseModel):
    limit_price: float

class StopLoss(BaseModel):
    stop_price: float
    limit_price: Optional[float] = None

class BracketOrderBody(BaseModel):
    symbol: str
    side: str
    type: Literal["market", "limit"] = "market"
    qty: Optional[float] = None
    notional: Optional[float] = None
    limit_price: Optional[float] = None
    time_in_force: str = "day"
    order_class: Literal["bracket"] = "bracket"
    take_profit: TakeProfit
    stop_loss: StopLoss
    extended_hours: Optional[bool] = False
    client_order_id: Optional[str] = None

    @root_validator(skip_on_failure=True)
    def _qty_notional_and_limit(cls, v):
        if (v.get("qty") is None) == (v.get("notional") is None):
            raise ValueError("Provide exactly one of qty or notional")
        if v.get("type") == "limit" and v.get("limit_price") is None:
            raise ValueError("limit_price is required for limit entry")
        return v

def _submit(req):
    try:
        return _client().submit_order(req)
    except APIError as e:
        detail = getattr(e, "error", None) or str(e)
        raise HTTPException(status_code=403, detail=detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/v1/order/bracket", tags=["Orders"])
def place_bracket(body: BracketOrderBody):
    # Price safety check uses IEX feed (works on free plans)
    try:
        k = os.getenv("APCA_API_KEY_ID"); s = os.getenv("APCA_API_SECRET_KEY")
        if k and s:
            r = requests.get(
                f"https://data.alpaca.markets/v2/stocks/{body.symbol}/trades/latest?feed=iex",
                headers={"APCA-API-KEY-ID": k, "APCA-API-SECRET-KEY": s},
                timeout=3,
            )
            if r.ok:
                last = r.json()["trade"]["p"]
                if body.side.lower() == "buy" and body.stop_loss.stop_price >= last - 0.01:
                    raise HTTPException(422, "For buys, stop_loss.stop_price must be at least $0.01 below current price.")
                if body.side.lower() == "sell" and body.stop_loss.stop_price <= last + 0.01:
                    raise HTTPException(422, "For sells, stop_loss.stop_price must be at least $0.01 above current price.")
    except Exception:
        pass

    side = _side(body.side)
    tif = _tif(body.time_in_force)
    tp = TakeProfitRequest(limit_price=body.take_profit.limit_price)
    sl = StopLossRequest(stop_price=body.stop_loss.stop_price, limit_price=body.stop_loss.limit_price)

    if body.type == "market":
        req = MarketOrderRequest(
            symbol=body.symbol,
            side=side,
            time_in_force=tif,
            qty=body.qty,
            notional=body.notional,
            order_class=OrderClass.BRACKET,
            take_profit=tp,
            stop_loss=sl,
            extended_hours=body.extended_hours,
            client_order_id=body.client_order_id,
        )
    else:
        req = LimitOrderRequest(
            symbol=body.symbol,
            side=side,
            time_in_force=tif,
            limit_price=body.limit_price,
            qty=body.qty,
            notional=body.notional,
            order_class=OrderClass.BRACKET,
            take_profit=tp,
            stop_loss=sl,
            extended_hours=body.extended_hours,
            client_order_id=body.client_order_id,
        )
    return jsonable_encoder(_submit(req))

class StopOrderBody(BaseModel):
    symbol: str
    side: str
    qty: Optional[float] = None
    notional: Optional[float] = None
    time_in_force: str = "day"
    stop_price: float
    extended_hours: Optional[bool] = False
    client_order_id: Optional[str] = None

    @root_validator(skip_on_failure=True)
    def _qty_xor_notional(cls, v):
        if (v.get("qty") is None) == (v.get("notional") is None):
            raise ValueError("Provide exactly one of qty or notional")
        return v

@router.post("/v1/order/stop", tags=["Orders"])
def place_stop(body: StopOrderBody):
    req = StopOrderRequest(
        symbol=body.symbol,
        side=_side(body.side),
        time_in_force=_tif(body.time_in_force),
        qty=body.qty,
        notional=body.notional,
        stop_price=body.stop_price,
        extended_hours=body.extended_hours,
        client_order_id=body.client_order_id,
    )
    return jsonable_encoder(_submit(req))

class TrailingOrderBody(BaseModel):
    symbol: str
    side: str
    qty: Optional[float] = None
    notional: Optional[float] = None
    time_in_force: str = "day"
    trail_price: Optional[float] = None
    trail_percent: Optional[float] = None
    extended_hours: Optional[bool] = False
    client_order_id: Optional[str] = None

    @root_validator(skip_on_failure=True)
    def _validate_trail(cls, v):
        tp = v.get("trail_price"); pc = v.get("trail_percent")
        if (tp is None and pc is None) or (tp is not None and pc is not None):
            raise ValueError("Provide either trail_price or trail_percent, not both")
        if (v.get("qty") is None) == (v.get("notional") is None):
            raise ValueError("Provide exactly one of qty or notional")
        return v

@router.post("/v1/order/trailing", tags=["Orders"])
def place_trailing(body: TrailingOrderBody):
    req = TrailingStopOrderRequest(
        symbol=body.symbol,
        side=_side(body.side),
        time_in_force=_tif(body.time_in_force),
        qty=body.qty,
        notional=body.notional,
        trail_price=body.trail_price,
        trail_percent=body.trail_percent,
        extended_hours=body.extended_hours,
        client_order_id=body.client_order_id,
    )
    return jsonable_encoder(_submit(req))
