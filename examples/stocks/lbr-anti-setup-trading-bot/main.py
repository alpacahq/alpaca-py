import logging
import os
import time
import traceback
from decimal import Decimal

import boto3
import pandas as pd

from alpaca_broker import (
    get_clock, get_price_history, get_orders, cancel_order,
    get_current_quotes, place_market_order, place_trailing_stop_order,
    get_account, get_all_positions,
)

logger = logging.getLogger()
logger.setLevel("INFO")

MAGNIFICENT_7 = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA"]

# LBR 3/10 oscillator parameters — authentic Raschke settings
# Source: Street Smarts (1996) Ch.9 + lindaraschke.net/faq-terminology-setups/
LBR_FAST   = 3    # SMA fast period
LBR_SLOW   = 10   # SMA slow period
LBR_SIGNAL = 16   # SMA signal period (SMA of the 3/10 difference)

# Indicator periods
ADX_PERIOD = 14
EMA_PERIOD = 20   # 20-bar EMA for trend context (Raschke's primary trend filter)
ATR_PERIOD = 14   # ATR for stop loss calculation

# Data
DAILY_BARS = 120  # ~6 months of daily bars
LBR_MIN_BARS = max(LBR_SLOW + LBR_SIGNAL, ADX_PERIOD + 1, EMA_PERIOD) + 5  # = 31

# Exit parameters (Option A — mechanical approximation of Raschke's discretionary exits)
# APPROXIMATION: Raschke sets stops at swing lows read from price structure.
# We substitute ATR-based stops as a computable proxy.
ATR_STOP_MULTIPLIER = Decimal("1.5")  # stop = entry - (ATR_14 * 1.5)
RISK_REWARD_RATIO = Decimal("1.0")    # target = entry + (risk * 1.0) — conservative 1:1

# Order polling
ORDER_SETTLEMENT_MAX_ATTEMPTS = 10
ORDER_SETTLEMENT_POLL_SECONDS = 2

def _get_table():
    return boto3.resource("dynamodb").Table(
        os.environ.get("PORTFOLIO_TABLE_NAME", "algotrading-portfolios")
    )


# --- DynamoDB helpers ---

def _store_portfolio(portfolio: dict) -> None:
    _get_table().put_item(Item=portfolio)


def _get_portfolio(account_hash: str) -> dict:
    response = _get_table().get_item(Key={"accountHash": account_hash})
    return response.get("Item", {"accountHash": account_hash, "cash": Decimal(0), "positions": {}})


# --- LBR 3/10 oscillator strategy ---

def calculate_adx(price_data: list[dict], period: int = ADX_PERIOD) -> tuple[float, bool]:
    """
    Returns (adx_value, is_rising) where is_rising = current ADX > previous ADX.
    Uses Wilder's smoothing (consistent with standard ADX definition).
    Returns (0.0, False) if insufficient data.
    """
    if len(price_data) < period * 2 + 1:
        return 0.0, False
    highs  = pd.Series([d["high"]  for d in price_data])
    lows   = pd.Series([d["low"]   for d in price_data])
    closes = pd.Series([d["close"] for d in price_data])

    # True Range
    prev_close = closes.shift(1)
    tr = pd.concat([
        highs - lows,
        (highs - prev_close).abs(),
        (lows  - prev_close).abs(),
    ], axis=1).max(axis=1)

    # Directional movement
    up_move   = highs.diff()
    down_move = -lows.diff()
    plus_dm  = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
    minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)

    # Wilder smoothing
    atr      = tr.ewm(alpha=1/period, adjust=False).mean()
    plus_di  = 100 * plus_dm.ewm(alpha=1/period, adjust=False).mean() / atr
    minus_di = 100 * minus_dm.ewm(alpha=1/period, adjust=False).mean() / atr

    dx  = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, float("nan"))
    adx = dx.ewm(alpha=1/period, adjust=False).mean()

    current_adx  = float(adx.iloc[-1])
    previous_adx = float(adx.iloc[-2])
    is_rising    = current_adx > previous_adx
    return current_adx, is_rising


def calculate_ema20(price_data: list[dict], period: int = EMA_PERIOD) -> float:
    """Returns the most recent 20-period EMA of closing prices."""
    closes = pd.Series([d["close"] for d in price_data])
    ema = closes.ewm(span=period, adjust=False).mean()
    return float(ema.iloc[-1])


def calculate_atr(price_data: list[dict], period: int = ATR_PERIOD) -> float:
    """
    Returns ATR(14) using Wilder's smoothing on daily bars.
    Used for Option A stop loss: stop = entry_price - (ATR * ATR_STOP_MULTIPLIER).
    # APPROXIMATION: Raschke places stops at swing lows from price structure.
    # ATR * 1.5 is a computable proxy for volatility-adjusted risk.
    """
    if len(price_data) < period + 1:
        return 0.0
    highs  = pd.Series([d["high"]  for d in price_data])
    lows   = pd.Series([d["low"]   for d in price_data])
    closes = pd.Series([d["close"] for d in price_data])
    prev_close = closes.shift(1)
    tr = pd.concat([
        highs - lows,
        (highs - prev_close).abs(),
        (lows  - prev_close).abs(),
    ], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    return float(atr.iloc[-1])


def calculate_lbr_signal(symbol: str, price_data: list[dict]) -> dict:
    """
    Computes the LBR 3/10 oscillator and detects the Anti setup.

    Returns a dict:
    {
        "score":          float,   # MACD_line[-1] - signal_line[-1]; >0 = bullish
        "selected":       bool,    # True if Anti setup confirmed (see rules below)
        "adx":            float,
        "adx_rising":     bool,
        "ema20":          float,
        "last_close":     float,
        "atr":            float,
        "signal_crossed": bool,    # signal line crossed zero (trend change)
        "pullback":       bool,    # MACD line pulled back to signal line
        "skip_reason":    str,     # non-empty string explains why selected=False
    }

    Anti setup rules (long side only — bot is long-only):
    1. Sufficient data: len(price_data) >= LBR_MIN_BARS
    2. ADX filter: ADX(14) <= 32 OR ADX is not rising
       (Raschke: "I will not try to trade against a market where the ADX is
       above 32 and rising." — lindaraschke.net ebook)
    3. Trend context: last close > EMA(20)
       (price must be above the 20-bar EMA for a long Anti)
    4. Signal line crossed zero from below (uptrend change confirmed):
       signal_line crossed above zero at some point in the last LBR_SIGNAL bars
    5. Pullback: MACD line has pulled back toward signal line after making a
       new high — specifically: MACD line is now <= signal_line (or within
       0.1 * ATR of it), having previously been above it
    6. Hook: MACD line is now turning back up (current histogram > previous histogram)
       # APPROXIMATION: Raschke uses price action to time Anti entry.
       # The histogram hook is a computable proxy for the price action hook.
    """
    result = {
        "score": 0.0, "selected": False,
        "adx": 0.0, "adx_rising": False,
        "ema20": 0.0, "last_close": 0.0, "atr": 0.0,
        "signal_crossed": False, "pullback": False,
        "skip_reason": "",
    }

    # Rule 1 — sufficient data
    if len(price_data) < LBR_MIN_BARS:
        result["skip_reason"] = f"insufficient bars ({len(price_data)} < {LBR_MIN_BARS})"
        logger.warning(f"{symbol}: {result['skip_reason']}")
        return result

    closes = pd.Series([d["close"] for d in price_data])

    # LBR 3/10 oscillator — SMA-based (NOT EMA)
    # Source: "the proper 3/10 uses simple averages" — lindaraschke.net
    sma_fast   = closes.rolling(LBR_FAST).mean()
    sma_slow   = closes.rolling(LBR_SLOW).mean()
    macd_line  = sma_fast - sma_slow
    signal_line = macd_line.rolling(LBR_SIGNAL).mean()
    histogram  = macd_line - signal_line

    score = float(macd_line.iloc[-1] - signal_line.iloc[-1])
    result["score"] = score

    # ADX filter (Rule 2)
    adx, adx_rising = calculate_adx(price_data)
    result["adx"] = adx
    result["adx_rising"] = adx_rising
    if adx > 32 and adx_rising:
        result["skip_reason"] = f"ADX {adx:.1f} > 32 and rising — strong trend filter"
        logger.info(f"{symbol}: {result['skip_reason']}")
        return result

    # Trend context (Rule 3)
    ema20 = calculate_ema20(price_data)
    last_close = float(closes.iloc[-1])
    result["ema20"] = ema20
    result["last_close"] = last_close
    if last_close <= ema20:
        result["skip_reason"] = f"price {last_close:.2f} below EMA20 {ema20:.2f} — no long Anti"
        logger.info(f"{symbol}: {result['skip_reason']}")
        return result

    # ATR (needed for hook proximity check)
    atr = calculate_atr(price_data)
    result["atr"] = atr

    # Signal line crossed zero from below (Rule 4)
    # Requires: signal line crossed above zero somewhere in the last LBR_SIGNAL bars
    # AND is currently above zero (trend change confirmed and still valid).
    recent_signal = signal_line.iloc[-LBR_SIGNAL:]
    currently_above_zero = float(signal_line.iloc[-1]) >= 0
    was_below_zero_recently = bool((recent_signal < 0).any())
    crossed_zero = currently_above_zero and was_below_zero_recently
    result["signal_crossed"] = crossed_zero
    if not crossed_zero:
        if not currently_above_zero:
            result["skip_reason"] = "signal line currently below zero — no active uptrend"
        else:
            result["skip_reason"] = "signal line has not crossed zero from below — no trend change"
        logger.info(f"{symbol}: {result['skip_reason']}")
        return result

    # Pullback — MACD line pulled back after making a new high (Rule 5)
    # The Anti requires: MACD made a new high, THEN pulled back to the signal line.
    # Both conditions must hold simultaneously.
    # APPROXIMATION: "near signal line" = within 0.5 * ATR of signal line.
    macd_now    = float(macd_line.iloc[-1])
    signal_now  = float(signal_line.iloc[-1])
    proximity   = 0.5 * atr if atr > 0 else abs(signal_now) * 0.1

    # Condition A: MACD line previously made a new high in the lookback window
    recent_macd = macd_line.iloc[-LBR_SIGNAL:]
    macd_made_new_high = float(recent_macd.max()) > macd_now  # current is below the recent peak

    # Condition B: MACD line is now near or below signal line
    near_signal = macd_now <= signal_now + proximity

    pulled_back = macd_made_new_high and near_signal
    result["pullback"] = pulled_back
    if not pulled_back:
        if not macd_made_new_high:
            result["skip_reason"] = "MACD line has not made a new high — no impulse to pull back from"
        else:
            result["skip_reason"] = "MACD line has not pulled back to signal line yet"
        logger.info(f"{symbol}: {result['skip_reason']}")
        return result

    # Hook — histogram turning back up (Rule 6)
    # APPROXIMATION: price action hook proxied by histogram direction change
    hist_now  = float(histogram.iloc[-1])
    hist_prev = float(histogram.iloc[-2])
    hooking_up = hist_now > hist_prev
    if not hooking_up:
        result["skip_reason"] = "MACD histogram not yet hooking up — waiting for entry"
        logger.info(f"{symbol}: {result['skip_reason']}")
        return result

    # All rules passed
    result["selected"] = True
    logger.info(
        f"{symbol}: Anti setup confirmed | score={score:.6f} | "
        f"ADX={adx:.1f}(rising={adx_rising}) | "
        f"close={last_close:.2f} EMA20={ema20:.2f} | ATR={atr:.2f}"
    )
    return result


def build_target_portfolio() -> tuple[list[str], dict[str, float]]:
    """
    Returns (selected_symbols, atr_by_symbol).
    selected_symbols: symbols where the Anti setup is confirmed.
    atr_by_symbol: ATR value per symbol, used by exit logic to compute stop prices.
    """
    signals = {}
    atrs    = {}
    for symbol in MAGNIFICENT_7:
        price_data = get_price_history(symbol, bars=DAILY_BARS)
        result = calculate_lbr_signal(symbol, price_data)
        signals[symbol] = result
        atrs[symbol]    = result["atr"]

    selected = [s for s, r in signals.items() if r["selected"]]

    if not selected:
        logger.info("No Anti setups confirmed across Magnificent 7 — holding cash.")
        # Log why each was skipped for debuggability
        for symbol, r in signals.items():
            if r["skip_reason"]:
                logger.info(f"  {symbol}: skipped — {r['skip_reason']}")
        return [], {}

    logger.info(f"Anti setup confirmed for: {selected}")
    return selected, {s: atrs[s] for s in selected}


# --- Portfolio execution helpers ---

def _get_ask_price(current_quotes: dict, symbol: str) -> Decimal | None:
    if symbol not in current_quotes:
        logger.warning(f"{symbol} NOT IN FETCHED QUOTES")
        return None
    
    quote = current_quotes[symbol]
    ask_price = quote.get("askPrice")
    
    if ask_price is None:
        logger.warning(f"{symbol} askPrice missing or None in quote data")
        return None
    
    try:
        return Decimal(str(ask_price))
    except (ValueError, TypeError) as e:
        logger.warning(f"{symbol} askPrice invalid: {ask_price} — {e}")
        return None


def _portfolio_value(positions: dict, cash: Decimal) -> Decimal:
    if not positions:
        return cash
    quotes = get_current_quotes(list(positions.keys()))
    total = cash
    for symbol, qty in positions.items():
        price = _get_ask_price(quotes, symbol)
        if price:
            total += price * Decimal(str(qty))
    return total


def _desired_positions(stocks: list[str], amount: Decimal) -> dict:
    if not stocks:
        return {}
    quotes = get_current_quotes(stocks)
    per_stock = amount / Decimal(len(stocks))
    result = {}
    for symbol in stocks:
        price = _get_ask_price(quotes, symbol)
        if price and price > 0:
            qty = int(per_stock // price)
            if qty > 0:
                result[symbol] = qty
    logger.info(f"Desired positions: {result}")
    return result


def _position_changes(current: dict, desired: dict) -> tuple[dict, dict]:
    sell, buy = {}, {}
    for symbol in set(current) | set(desired):
        cur_qty = Decimal(str(current.get(symbol, 0)))
        des_qty = Decimal(str(desired.get(symbol, 0)))
        diff = des_qty - cur_qty
        if diff > 0:
            buy[symbol] = int(diff)
        elif diff < 0:
            sell[symbol] = int(-diff)
    return sell, buy


def _positions_by_symbol() -> dict[str, int]:
    return {p.symbol: int(float(p.qty)) for p in get_all_positions()}


def _submit_market_orders(orders: dict[str, int], side: str) -> dict[str, int]:
    submitted = {}
    for symbol, qty in orders.items():
        try:
            order = place_market_order(None, symbol, qty, side)
        except Exception as exc:
            logger.warning(
                f"{symbol}: failed to submit {side} market order for qty={qty}: {exc}",
                exc_info=True,
            )
            continue

        order_id = getattr(order, "id", None)
        status = getattr(order, "status", None)
        logger.info(f"{symbol}: submitted {side} market order qty={qty} id={order_id} status={status}")
        submitted[symbol] = qty
    return submitted


def _expected_positions_after(current: dict[str, int], changes: dict[str, int], side: str) -> dict[str, int]:
    expected = current.copy()
    for symbol, qty in changes.items():
        current_qty = expected.get(symbol, 0)
        next_qty = current_qty + qty if side == "BUY" else current_qty - qty
        if next_qty > 0:
            expected[symbol] = next_qty
        else:
            expected.pop(symbol, None)
    return expected


def _positions_match(observed: dict[str, int], expected: dict[str, int], symbols: set[str]) -> bool:
    return all(observed.get(symbol, 0) == expected.get(symbol, 0) for symbol in symbols)


def _positions_for_log(positions: dict[str, int], symbols: set[str]) -> dict[str, int]:
    return {symbol: positions.get(symbol, 0) for symbol in sorted(symbols)}


def _wait_for_positions(expected: dict[str, int], symbols: set[str], phase: str) -> dict[str, int]:
    last_observed = {}
    for attempt in range(1, ORDER_SETTLEMENT_MAX_ATTEMPTS + 1):
        last_observed = _positions_by_symbol()
        if _positions_match(last_observed, expected, symbols):
            logger.info(f"{phase}: positions settled after {attempt} poll(s)")
            return last_observed

        if attempt < ORDER_SETTLEMENT_MAX_ATTEMPTS:
            logger.info(
                f"{phase}: waiting for positions to settle; "
                f"expected={_positions_for_log(expected, symbols)} "
                f"observed={_positions_for_log(last_observed, symbols)}"
            )
            time.sleep(ORDER_SETTLEMENT_POLL_SECONDS)

    logger.warning(
        f"{phase}: positions did not settle; "
        f"expected={_positions_for_log(expected, symbols)} "
        f"observed={_positions_for_log(last_observed, symbols)}"
    )
    raise TimeoutError(f"{phase}: positions did not settle after market order submission")


def _place_exit_orders(
    buy_pos: dict[str, int],
    atr_by_symbol: dict[str, float],
    entry_quotes: dict,
) -> None:
    for symbol, qty in buy_pos.items():
        # Defensively check for symbol in entry_quotes to avoid KeyError
        if symbol not in entry_quotes:
            logger.warning(f"{symbol}: quote unavailable, skipping stop-loss setup")
            continue
        quote_data = entry_quotes[symbol]
        if "askPrice" not in quote_data:
            logger.warning(f"{symbol}: askPrice missing from quote, skipping stop-loss setup")
            continue

        ask = Decimal(str(quote_data["askPrice"]))
        atr = Decimal(str(atr_by_symbol.get(symbol, 0)))
        # atr_by_symbol only contains selected symbols. If a submitted buy has no
        # ATR, the strategy invariant is broken and an operator should inspect it.
        if atr <= 0:
            logger.warning(f"{symbol}: ATR unavailable for submitted buy, skipping stop-loss setup")
            continue
        stop_price = ask - (atr * ATR_STOP_MULTIPLIER)
        stop_price = max(stop_price, Decimal("0.01"))   # floor at $0.01
        trail_pct = float((atr * ATR_STOP_MULTIPLIER) / ask * 100)
        logger.info(
            f"{symbol}: entry≈{ask:.2f} | ATR={atr:.2f} | "
            f"stop={stop_price:.2f} | trail_pct={trail_pct:.2f}% | "
            f"target≈{ask + atr * ATR_STOP_MULTIPLIER * RISK_REWARD_RATIO:.2f}"
        )
        # APPROXIMATION: converting ATR distance to trail_percent for TrailingStopOrderRequest.
        # True Option A would place a hard stop-limit at stop_price directly.
        place_trailing_stop_order(None, symbol, qty, trail_pct, "SELL")


# --- Main run logic ---

def run() -> None:
    logger.info("Starting bot")
    desired_stocks, atr_by_symbol = build_target_portfolio()
    logger.info(f"Desired stocks: {desired_stocks}")

    account = get_account()
    account_hash = str(account.id)
    buying_power = Decimal(str(account.buying_power))

    current_positions = _positions_by_symbol()

    portfolio = _get_portfolio(account_hash)
    portfolio["cash"] = buying_power
    portfolio["positions"] = current_positions

    portfolio_value = _portfolio_value(current_positions, buying_power)
    logger.info(f"Account {account_hash}: portfolio_value={portfolio_value}")

    # Cancel open orders before rebalancing
    for order in get_orders():
        cancel_order(None, str(order.id))
        logger.info(f"Cancelled order {order.id}")

    allocation = portfolio_value * Decimal("0.02")
    desired = _desired_positions(desired_stocks, allocation)
    sell_pos, buy_pos = _position_changes(current_positions, desired)

    logger.info(f"Selling: {sell_pos}")
    logger.info(f"Buying: {buy_pos}")

    submitted_sells = _submit_market_orders(sell_pos, "SELL")
    if submitted_sells:
        expected_after_sells = _expected_positions_after(current_positions, submitted_sells, "SELL")
        current_positions = _wait_for_positions(expected_after_sells, set(submitted_sells), "WAIT_SELL")

    # Fetch quotes BEFORE placing orders — used for stop price calculation
    entry_quotes = get_current_quotes(list(buy_pos.keys())) if buy_pos else {}

    submitted_buys = _submit_market_orders(buy_pos, "BUY")
    if submitted_buys:
        expected_after_buys = _expected_positions_after(current_positions, submitted_buys, "BUY")
        current_positions = _wait_for_positions(expected_after_buys, set(submitted_buys), "WAIT_BUY")

    # Refresh positions and store to DynamoDB
    portfolio["positions"] = current_positions
    _store_portfolio(portfolio)

    # --- Option A exits: ATR-based stop + measured move target ---
    # APPROXIMATION: Raschke sets stops at swing lows from price structure.
    # Trailing stops are replaced by fixed ATR stops placed at order time.
    # Profit target = entry + (ATR * ATR_STOP_MULTIPLIER * RISK_REWARD_RATIO) — 1:1 R:R.
    if submitted_buys:
        _place_exit_orders(submitted_buys, atr_by_symbol, entry_quotes)


def handler(event, context):
    clock = get_clock()
    if not clock.is_open:
        logger.info("Market is closed — skipping run.")
        return {"statusCode": 200, "body": {"status": "skipped", "reason": "market_closed"}}
    try:
        run()
        return {"statusCode": 200, "body": {"status": "success"}}
    except Exception as e:
        logger.error(traceback.format_exc())
        return {"statusCode": 500, "body": {"error": "Internal server error"}}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    response = handler({}, None)
    raise SystemExit(0 if response.get("statusCode", 500) < 400 else 1)
