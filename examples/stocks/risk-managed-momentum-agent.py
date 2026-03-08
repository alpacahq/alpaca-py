"""
Risk-Managed Momentum Trading Agent
====================================

A momentum trading agent that validates every trade through System R's
pre-trade risk gate before execution. This ensures compliance with
configurable risk limits (concentration, drawdown, exposure) before
any order reaches the market.

Architecture:
    1. Scan for momentum signals (20-day price breakout)
    2. Submit proposed trade to System R pre_trade_gate for approval
    3. Execute on Alpaca only if the risk gate returns "approve"

Requirements:
    pip install alpaca-py httpx python-dotenv

Environment variables:
    ALPACA_API_KEY      - Alpaca paper/live API key
    ALPACA_SECRET_KEY   - Alpaca paper/live secret key
    SYSTEMR_API_KEY     - System R API key (get one at https://systemr.ai)
    ALPACA_PAPER_TRADE  - Set to "True" for paper trading (default: True)

System R reference:
    https://github.com/System-R-AI/systemr-agent-demo
    https://agents.systemr.ai/docs
"""

import logging
import os
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import httpx
from dotenv import load_dotenv

# Alpaca SDK imports
from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import MarketOrderRequest

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

load_dotenv()

ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
SYSTEMR_API_KEY = os.getenv("SYSTEMR_API_KEY")
PAPER = os.getenv("ALPACA_PAPER_TRADE", "True").lower() in ("true", "1", "yes")

if not all([ALPACA_API_KEY, ALPACA_SECRET_KEY, SYSTEMR_API_KEY]):
    sys.exit("Error: set ALPACA_API_KEY, ALPACA_SECRET_KEY, and SYSTEMR_API_KEY.")

SYSTEMR_GATE_URL = "https://agents.systemr.ai/v1/compound/pre-trade-gate"

# Universe of symbols to scan for momentum
UNIVERSE = ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "META", "GOOG"]
BREAKOUT_WINDOW = 20  # days for high-watermark breakout
ORDER_QTY = 1  # shares per trade (keep small for the example)

NY_TZ = ZoneInfo("America/New_York")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Clients
# ---------------------------------------------------------------------------

trade_client = TradingClient(
    api_key=ALPACA_API_KEY, secret_key=ALPACA_SECRET_KEY, paper=PAPER
)
data_client = StockHistoricalDataClient(
    api_key=ALPACA_API_KEY, secret_key=ALPACA_SECRET_KEY
)
http_client = httpx.Client(
    headers={"Authorization": f"Bearer {SYSTEMR_API_KEY}"},
    timeout=10.0,
)

# ---------------------------------------------------------------------------
# Momentum signal: 20-day high breakout
# ---------------------------------------------------------------------------


def detect_breakout(symbol: str) -> float | None:
    """Return the latest close if it breaks the 20-day high, else None."""
    today = datetime.now(NY_TZ).date()
    bars = data_client.get_stock_bars(
        StockBarsRequest(
            symbol_or_symbols=[symbol],
            timeframe=TimeFrame(amount=1, unit=TimeFrameUnit.Day),
            start=today - timedelta(days=BREAKOUT_WINDOW + 5),
        )
    ).df

    if len(bars) < BREAKOUT_WINDOW:
        return None

    closes = bars["close"]
    latest_close = closes.iloc[-1]
    rolling_high = closes.iloc[-(BREAKOUT_WINDOW + 1) : -1].max()

    if latest_close > rolling_high:
        return float(latest_close)
    return None


# ---------------------------------------------------------------------------
# System R pre-trade risk gate
# ---------------------------------------------------------------------------


def check_risk_gate(
    symbol: str, side: str, qty: int, price: float
) -> tuple[bool, dict]:
    """Call System R pre_trade_gate. Returns (approved, response_body)."""
    payload = {
        "agent_id": "alpaca-momentum-agent",
        "symbol": symbol,
        "side": side,
        "quantity": qty,
        "price": price,
        "order_type": "market",
        "strategy": "momentum_breakout",
    }

    try:
        resp = http_client.post(SYSTEMR_GATE_URL, json=payload)
        resp.raise_for_status()
        body = resp.json()
        approved = body.get("decision") == "approve"
        return approved, body
    except httpx.HTTPError as exc:
        log.error("System R gate request failed: %s", exc)
        # Fail closed: if the risk service is unreachable, do not trade.
        return False, {"error": str(exc)}


# ---------------------------------------------------------------------------
# Order execution
# ---------------------------------------------------------------------------


def place_order(symbol: str, qty: int, side: OrderSide) -> None:
    """Submit a market order via the Alpaca SDK."""
    order = trade_client.submit_order(
        MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=side,
            time_in_force=TimeInForce.DAY,
        )
    )
    log.info("Order submitted: %s %s x%d  (id=%s)", side.name, symbol, qty, order.id)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------


def main() -> None:
    log.info("Starting risk-managed momentum scan (paper=%s)", PAPER)

    account = trade_client.get_account()
    log.info(
        "Account equity: $%s  buying power: $%s",
        account.equity,
        account.buying_power,
    )

    for symbol in UNIVERSE:
        # Step 1 -- detect momentum signal
        breakout_price = detect_breakout(symbol)
        if breakout_price is None:
            continue
        log.info("Breakout detected: %s at $%.2f", symbol, breakout_price)

        # Step 2 -- validate through System R risk gate
        approved, gate_resp = check_risk_gate(
            symbol=symbol,
            side="buy",
            qty=ORDER_QTY,
            price=breakout_price,
        )

        if not approved:
            log.warning(
                "Risk gate REJECTED %s: %s",
                symbol,
                gate_resp.get("reason", gate_resp),
            )
            continue

        log.info(
            "Risk gate APPROVED %s (risk_score=%.2f)",
            symbol,
            gate_resp.get("risk_score", 0),
        )

        # Step 3 -- execute the trade
        place_order(symbol, ORDER_QTY, OrderSide.BUY)

    log.info("Scan complete.")


if __name__ == "__main__":
    main()
