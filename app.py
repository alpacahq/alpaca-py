from advanced_orders import router as advanced_orders_router
import os
import re
from datetime import datetime
from typing import List, Optional
import aiohttp
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from alpaca.common.exceptions import APIError
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import (
    MarketOrderRequest,
    LimitOrderRequest,
    StopOrderRequest,
    CreateWatchlistRequest,
    UpdateWatchlistRequest
)
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import (
    StockBarsRequest, StockQuotesRequest, StockTradesRequest
)
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca_client import AlpacaClient

ALPACA_API_BASE_URL = os.getenv("ALPACA_API_BASE_URL", "https://api.alpaca.markets")
ALPACA_KEY_ID = os.getenv("ALPACA_KEY_ID") or os.getenv("APCA_API_KEY_ID")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY") or os.getenv("APCA_API_SECRET_KEY")
GATEWAY_API_KEY = os.getenv("GATEWAY_API_KEY") or os.getenv("X_API_KEY")

app = FastAPI(title="Alpaca Wrapper", version="1.0.3")


def _require_gateway_key(x_api_key: Optional[str]):
    if GATEWAY_API_KEY and x_api_key != GATEWAY_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")


def _alpaca_headers():
    key_id = ALPACA_KEY_ID or os.getenv("APCA_API_KEY_ID")
    secret_key = ALPACA_SECRET_KEY or os.getenv("APCA_API_SECRET_KEY")
    if not (key_id and secret_key):
        raise HTTPException(status_code=500, detail="Upstream credentials not configured")
    return {
        "APCA-API-KEY-ID": key_id,
        "APCA-API-SECRET-KEY": secret_key,
    }


app.include_router(advanced_orders_router)


def check_key(x_api_key: Optional[str]):
    _require_gateway_key(x_api_key)

def trading_client() -> TradingClient:
    return AlpacaClient.from_env().client

def md_client() -> StockHistoricalDataClient:
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


class CreateOrder(BaseModel):
    symbol: str
    side: str
    qty: float | None = None
    notional: float | None = None
    type: str
    time_in_force: str
    limit_price: float | None = None
    stop_price: float | None = None
    order_class: str | None = None
    take_profit: dict | None = None
    stop_loss: dict | None = None
    extended_hours: bool | None = None
    trail_price: float | None = None
    trail_percent: float | None = None
    client_order_id: str | None = None

def parse_timeframe(tf_str: str) -> TimeFrame:
    m = re.match(r'^(\d+)([A-Za-z]+)$', tf_str)
    if not m:
        raise HTTPException(status_code=400, detail="Invalid timeframe format")
    amount = int(m.group(1))
    unit = m.group(2).lower()
    units = {
        "min": TimeFrameUnit.Minute,
        "minute": TimeFrameUnit.Minute,
        "hour": TimeFrameUnit.Hour,
        "day": TimeFrameUnit.Day,
        "week": TimeFrameUnit.Week,
        "month": TimeFrameUnit.Month,
    }
    if unit not in units:
        raise HTTPException(status_code=400, detail="Unsupported timeframe unit")
    return TimeFrame(amount, units[unit])

@app.get("/healthz")
def healthz(): return {"ok": True}

# -- Orders
@app.post("/v1/order")
def submit_order(order: OrderIn, x_api_key: Optional[str] = Header(None)):
    check_key(x_api_key)
    tc = trading_client()
    side = OrderSide.BUY if order.side.lower() == "buy" else OrderSide.SELL
    tif = TimeInForce(order.time_in_force.lower())
    if order.type.lower() == "market":
        req = MarketOrderRequest(symbol=order.symbol, qty=order.qty, notional=order.notional,
                                 side=side, time_in_force=tif)
    elif order.type.lower() == "limit":
        if order.limit_price is None:
            raise HTTPException(400, "limit_price required for limit orders")
        req = LimitOrderRequest(symbol=order.symbol, qty=order.qty,
                                side=side, time_in_force=tif, limit_price=order.limit_price)
    else:
        raise HTTPException(400, "unsupported order type")
    o = tc.submit_order(order_data=req)
    return o.model_dump() if hasattr(o, "model_dump") else o.__dict__


@app.post("/v2/orders")
async def order_create(
    order: CreateOrder, x_api_key: Optional[str] = Header(None, alias="x-api-key")
):
    _require_gateway_key(x_api_key)
    payload = (
        order.model_dump(exclude_none=True)
        if hasattr(order, "model_dump")
        else order.dict(exclude_none=True)
    )
    async with aiohttp.ClientSession(headers=_alpaca_headers()) as session:
        async with session.post(f"{ALPACA_API_BASE_URL}/v2/orders", json=payload) as r:
            body = await r.text()
            if r.status >= 400:
                raise HTTPException(status_code=r.status, detail=body)
            return await r.json()


@app.get("/v2/account")
async def account_get(x_api_key: Optional[str] = Header(None, alias="x-api-key")):
    _require_gateway_key(x_api_key)
    async with aiohttp.ClientSession(headers=_alpaca_headers()) as session:
        async with session.get(f"{ALPACA_API_BASE_URL}/v2/account") as r:
            body = await r.text()
            if r.status >= 400:
                raise HTTPException(status_code=r.status, detail=body)
            return await r.json()


@app.get("/v2/orders")
async def orders_list(
    status: Optional[str] = Query(None),
    x_api_key: Optional[str] = Header(None, alias="x-api-key"),
):
    _require_gateway_key(x_api_key)
    params = {"status": status} if status else None
    async with aiohttp.ClientSession(headers=_alpaca_headers()) as session:
        async with session.get(
            f"{ALPACA_API_BASE_URL}/v2/orders", params=params
        ) as r:
            body = await r.text()
            if r.status >= 400:
                raise HTTPException(status_code=r.status, detail=body)
            return await r.json()


@app.get("/v2/orders/{order_id}")
async def orders_get_by_id(
    order_id: str, x_api_key: Optional[str] = Header(None, alias="x-api-key")
):
    _require_gateway_key(x_api_key)
    async with aiohttp.ClientSession(headers=_alpaca_headers()) as session:
        async with session.get(
            f"{ALPACA_API_BASE_URL}/v2/orders/{order_id}"
        ) as r:
            body = await r.text()
            if r.status >= 400:
                raise HTTPException(status_code=r.status, detail=body)
            return await r.json()


@app.get("/v2/positions")
async def positions_list_v2(
    x_api_key: Optional[str] = Header(None, alias="x-api-key")
):
    _require_gateway_key(x_api_key)
    async with aiohttp.ClientSession(headers=_alpaca_headers()) as session:
        async with session.get(f"{ALPACA_API_BASE_URL}/v2/positions") as r:
            body = await r.text()
            if r.status >= 400:
                raise HTTPException(status_code=r.status, detail=body)
            return await r.json()


@app.get("/v2/positions/{symbol}")
async def positions_get(
    symbol: str, x_api_key: Optional[str] = Header(None, alias="x-api-key")
):
    _require_gateway_key(x_api_key)
    async with aiohttp.ClientSession(headers=_alpaca_headers()) as session:
        async with session.get(
            f"{ALPACA_API_BASE_URL}/v2/positions/{symbol}"
        ) as r:
            body = await r.text()
            if r.status >= 400:
                raise HTTPException(status_code=r.status, detail=body)
            return await r.json()


@app.delete("/v2/positions")
async def positions_close_all(
    cancel_orders: bool = Query(False),
    x_api_key: Optional[str] = Header(None, alias="x-api-key"),
):
    _require_gateway_key(x_api_key)
    params = {"cancel_orders": str(cancel_orders).lower()}
    async with aiohttp.ClientSession(headers=_alpaca_headers()) as session:
        async with session.delete(
            f"{ALPACA_API_BASE_URL}/v2/positions", params=params
        ) as r:
            body = await r.text()
            if r.status >= 400:
                raise HTTPException(status_code=r.status, detail=body)
            return await r.json()


@app.delete("/v2/positions/{symbol}")
async def positions_close(
    symbol: str,
    cancel_orders: bool = Query(False),
    x_api_key: Optional[str] = Header(None, alias="x-api-key"),
):
    _require_gateway_key(x_api_key)
    params = {"cancel_orders": str(cancel_orders).lower()}
    async with aiohttp.ClientSession(headers=_alpaca_headers()) as session:
        async with session.delete(
            f"{ALPACA_API_BASE_URL}/v2/positions/{symbol}", params=params
        ) as r:
            body = await r.text()
            if r.status >= 400:
                raise HTTPException(status_code=r.status, detail=body)
            return await r.json()

@app.get("/v1/orders")
def list_orders(status: str = Query("open"), x_api_key: Optional[str] = Header(None)):
    check_key(x_api_key)
    tc = trading_client()
    orders = tc.get_orders()
    return [o.model_dump() for o in orders]

@app.get("/v1/orders/{order_id}")
def get_order(order_id: str, x_api_key: Optional[str] = Header(None)):
    check_key(x_api_key)
    tc = trading_client()
    o = tc.get_order_by_id(order_id)
    return o.model_dump() if hasattr(o, "model_dump") else o.__dict__

@app.delete(
    "/v1/orders/{order_id}",
    status_code=204,
    summary="Cancel order",
    response_description="Order cancelled",
)
def cancel_order(order_id: str, x_api_key: Optional[str] = Header(None)):
    check_key(x_api_key)
    tc = trading_client()
    tc.cancel_order(order_id)

    # The decorator defines a 204 status code, so simply return an empty response.
    return Response(status_code=204)


# v2 alias for cancelling orders to match OpenAPI spec
@app.delete(
    "/v2/orders/{order_id}",
    status_code=204,
    summary="Cancel order by ID",
    response_description="Order cancelled",
    # FastAPI uses snake_case for the OpenAPI operation_id parameter
    operation_id="cancelOrderById_v2",
)
async def cancelOrderById_v2(
    order_id: str, x_api_key: Optional[str] = Header(None, alias="x-api-key")
):
    """Cancel an order by ID for the v2 API. Mirrors /v1/orders/{order_id}."""

    _require_gateway_key(x_api_key)
    async with aiohttp.ClientSession(headers=_alpaca_headers()) as session:
        async with session.delete(
            f"{ALPACA_API_BASE_URL}/v2/orders/{order_id}"
        ) as r:
            if r.status >= 400:
                body = await r.text()
                raise HTTPException(status_code=r.status, detail=body)
    return Response(status_code=204)

# -- Account
@app.get("/v1/account")
def get_account(x_api_key: Optional[str] = Header(None)):
    check_key(x_api_key)
    client = AlpacaClient.from_env()
    try:
        return client.get_account()
    except APIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

# -- Positions
@app.get("/v1/positions")
def list_positions(x_api_key: Optional[str] = Header(None)):
    check_key(x_api_key)
    positions = trading_client().get_all_positions()
    return [p.model_dump() for p in positions]

@app.get("/v1/positions/{symbol}")
def get_position(symbol: str, x_api_key: Optional[str] = Header(None)):
    check_key(x_api_key)
    pos = trading_client().get_open_position(symbol)
    return pos.model_dump() if hasattr(pos, "model_dump") else pos.__dict__

@app.delete("/v1/positions/{symbol}")
def close_position(symbol: str, cancel_orders: bool = Query(False), x_api_key: Optional[str] = Header(None)):
    check_key(x_api_key)
    return trading_client().close_position(symbol, cancel_orders=cancel_orders)

@app.delete("/v1/positions")
def close_all_positions(cancel_orders: bool = Query(False), x_api_key: Optional[str] = Header(None)):
    check_key(x_api_key)
    return trading_client().close_all_positions(cancel_orders=cancel_orders)

# -- Watchlists
@app.get("/v1/watchlists")
def list_watchlists(x_api_key: Optional[str] = Header(None)):
    check_key(x_api_key)
    wls = trading_client().get_watchlists()
    return [wl.model_dump() for wl in wls]

class WatchlistIn(BaseModel):
    name: str
    symbols: List[str]

@app.post("/v1/watchlists")
def create_watchlist(w: WatchlistIn, x_api_key: Optional[str] = Header(None)):
    check_key(x_api_key)
    req = CreateWatchlistRequest(name=w.name, symbols=w.symbols)
    wl = trading_client().create_watchlist(req)
    return wl.model_dump()

@app.get("/v1/watchlists/{watchlist_id}")
def get_watchlist(watchlist_id: str, x_api_key: Optional[str] = Header(None)):
    check_key(x_api_key)
    wl = trading_client().get_watchlist(watchlist_id)
    return wl.model_dump()

@app.put("/v1/watchlists/{watchlist_id}")
def update_watchlist(watchlist_id: str, w: WatchlistIn, x_api_key: Optional[str] = Header(None)):
    check_key(x_api_key)
    req = UpdateWatchlistRequest(name=w.name, symbols=w.symbols)
    wl = trading_client().update_watchlist(watchlist_id, req)
    return wl.model_dump()

@app.delete("/v1/watchlists/{watchlist_id}")
def delete_watchlist(watchlist_id: str, x_api_key: Optional[str] = Header(None)):
    check_key(x_api_key)
    return trading_client().delete_watchlist(watchlist_id)

# -- Quotes & Trades (basic market data)
@app.get("/v1/quotes")
def get_quotes(symbol: str, start: str, end: str, x_api_key: Optional[str] = Header(None)):
    check_key(x_api_key)
    req = StockQuotesRequest(symbol_or_symbols=[symbol],
                             start=datetime.fromisoformat(start),
                             end=datetime.fromisoformat(end))
    quotes = md_client().get_stock_quotes(req)
    return quotes.df.reset_index().to_dict(orient="records")

@app.get("/v1/trades")
def get_trades(symbol: str, start: str, end: str, x_api_key: Optional[str] = Header(None)):
    check_key(x_api_key)
    req = StockTradesRequest(symbol_or_symbols=[symbol],
                             start=datetime.fromisoformat(start),
                             end=datetime.fromisoformat(end))
    trades = md_client().get_stock_trades(req)
    return trades.df.reset_index().to_dict(orient="records")

@app.get("/v1/bars")
def get_bars(symbol: str, timeframe: str = Query("1Day"), start: str = Query(...),
             end: Optional[str] = None, x_api_key: Optional[str] = Header(None)):
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


# --- ChatGPT plugin support ---
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

try:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://chat.openai.com"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
except Exception:
    pass

try:
    app.mount("/.well-known", StaticFiles(directory=".well-known"), name="wellknown")
except Exception:
    pass

@app.get("/openapi.yaml", include_in_schema=False)
def _openapi_yaml():
    return FileResponse("openapi.yaml", media_type="text/yaml")
# --- end plugin support ---
from fastapi.responses import JSONResponse
import yaml
@app.get("/openapi.json", include_in_schema=False)
def _openapi_json():
    with open("openapi.yaml", "r", encoding="utf-8") as f:
        spec = yaml.safe_load(f)
    return JSONResponse(spec)
# --- GPT Actions OpenAPI patch ---
from fastapi.responses import PlainTextResponse
from fastapi.openapi.utils import get_openapi
import yaml

SERVER_URL = 'https://alpaca-py-production.up.railway.app'

def _custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title="Alpaca Wrapper",
        version="1.0.0",
        routes=app.routes,
    )
    # Force OpenAPI 3.1 and a proper base URL for GPT Actions
    schema["openapi"] = "3.1.0"
    schema["servers"] = [{"url": SERVER_URL}]
    # Ensure security scheme exists (so importer sees the header)
    schema.setdefault("components", {}).setdefault("securitySchemes", {
        "ApiKeyAuth": {"type": "apiKey", "in": "header", "name": "x-api-key"}
    })
    app.openapi_schema = schema
    return app.openapi_schema

app.openapi = _custom_openapi

# YAML variant of the same runtime schema (for manual checks)
@app.get("/openapi.yaml", include_in_schema=False)
def _openapi_yaml():
    return PlainTextResponse(
        yaml.safe_dump(app.openapi(), sort_keys=False, allow_unicode=True),
        media_type="application/yaml"
    )
# --- end patch ---
# --- Actions/OpenAPI serving (do not use FastAPI auto /openapi.json) ---
import os, yaml
from fastapi import Header, HTTPException
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse

# Optional gate separate from Alpaca creds
PLUGIN_API_KEY = os.getenv("PLUGIN_API_KEY")

def _require_plugin_key(x_api_key: str | None):
    if PLUGIN_API_KEY and x_api_key != PLUGIN_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.get("/healthz", include_in_schema=False)
def _healthz(): return {"ok": True}

# Serve your file-based spec (YAML + JSON)
@app.get("/openapi.yaml", include_in_schema=False)
def _spec_yaml(): return FileResponse("openapi.yaml", media_type="text/yaml")

@app.get("/openapi.json", include_in_schema=False)
def _spec_json():
    with open("openapi.yaml","r",encoding="utf-8") as f:
        return JSONResponse(yaml.safe_load(f))

# Remove FastAPI's auto /openapi.json to avoid conflicts
try:
    app.openapi_url = None
    app.docs_url = None
    app.redoc_url = None
except Exception:
    pass
# --- end patch ---



@app.get('/openapi.json', include_in_schema=False)
def openapi_json():
    return FileResponse('openapi.json', media_type='application/json')
