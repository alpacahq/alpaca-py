import os
import re
from datetime import datetime
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

app = FastAPI(title="Alpaca Wrapper")

def check_key(x_api_key: str | None):
    service_key = os.getenv("X_API_KEY")
    if not service_key or x_api_key != service_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

def trading_client():
    return TradingClient(
        api_key=os.environ["APCA_API_KEY_ID"],
        secret_key=os.environ["APCA_API_SECRET_KEY"],
        paper=("paper" in os.environ.get("APCA_API_BASE_URL", "")),
    )

def md_client():
    return StockHistoricalDataClient(
        api_key=os.environ["APCA_API_KEY_ID"],
        secret_key=os.environ["APCA_API_SECRET_KEY"]
    )

class OrderIn(BaseModel):
    symbol: str
    side: str
    qty: float | None = None
    notional: float | None = None
    type: str
    time_in_force: str
    limit_price: float | None = None

def parse_timeframe(tf_str: str) -> TimeFrame:
    m = re.match(r"^(\d+)([A-Za-z]+)$", tf_str)
    if not m:
        raise HTTPException(status_code=400, detail="Invalid timeframe format")
    amount = int(m.group(1))
    unit_str = m.group(2).lower()
    unit_map = {
        "min": TimeFrameUnit.Minute,
        "minute": TimeFrameUnit.Minute,
        "hour": TimeFrameUnit.Hour,
        "day": TimeFrameUnit.Day,
        "week": TimeFrameUnit.Week,
        "month": TimeFrameUnit.Month,
    }
    if unit_str not in unit_map:
        raise HTTPException(status_code=400, detail="Unsupported timeframe unit")
    return TimeFrame(amount, unit_map[unit_str])

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.post("/v1/order")
def place_order(inp: OrderIn, x_api_key: str | None = Header(None)):
    check_key(x_api_key)
    tc = trading_client()
    side = OrderSide.BUY if inp.side.lower() == "buy" else OrderSide.SELL
    tif = TimeInForce(inp.time_in_force.upper())
    if inp.type.lower() == "market":
        req = MarketOrderRequest(symbol=inp.symbol, qty=inp.qty, notional=inp.notional,
                                 side=side, time_in_force=tif)
    elif inp.type.lower() == "limit":
        if inp.limit_price is None:
            raise HTTPException(status_code=400, detail="limit_price required for limit orders")
        req = LimitOrderRequest(symbol=inp.symbol, qty=inp.qty, side=side,
                                time_in_force=tif, limit_price=inp.limit_price)
    else:
        raise HTTPException(status_code=400, detail="unsupported order type")
    order = tc.submit_order(order_data=req)
    return order.model_dump() if hasattr(order, "model_dump") else order.__dict__

@app.get("/v1/bars")
def get_bars(symbol: str = Query(...), timeframe: str = Query("1Day"),
             start: str = Query(...), end: str | None = None,
             x_api_key: str | None = Header(None)):
    check_key(x_api_key)
    tf = parse_timeframe(timeframe)
    req = StockBarsRequest(
        symbol_or_symbols=[symbol],
        timeframe=tf,
        start=datetime.fromisoformat(start),
        end=datetime.fromisoformat(end) if end else None
    )
    bars = md_client().get_stock_bars(req)
    return bars.df.reset_index().to_dict(orient="records")

@app.get("/openapi.yaml")
def spec():
    return FileResponse("openapi.yaml")
