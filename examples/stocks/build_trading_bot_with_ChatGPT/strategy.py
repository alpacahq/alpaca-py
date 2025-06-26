# Import standard library modules
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

# Import third party modules
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from dotenv import load_dotenv

# Import Alpaca modules
from alpaca.data.historical.stock import (
    StockHistoricalDataClient,
    StockLatestTradeRequest,
)
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import (
    AssetClass,
    AssetStatus,
    OrderSide,
    OrderType,
    QueryOrderStatus,
    TimeInForce,
)
from alpaca.trading.requests import LimitOrderRequest, MarketOrderRequest


# Set the local timezone
NY_TZ = ZoneInfo('America/New_York')

# Select the stock (ProShares UltraPro QQQ)
underlying_symbol = 'TQQQ'

# Strategy Parameters
RSI_PERIOD       = 14                   # Standard medium‑term RSI
MACD_FAST        = 12                   # MACD fast EMA
MACD_SLOW        = 26                   # MACD slow EMA
MACD_SIGNAL      = 9                    # MACD signal line EMA
MA_FAST          = 50                   # Higher‑timeframe fast MA
MA_MID           = 100                  # Higher‑timeframe mid MA
MA_SLOW          = 200                  # Higher‑timeframe slow MA
BUY_POWER_LIMIT  = 0.02                 # Limit the amount of buying power to use for the trade
MAX_RISK_PCT     = 0.03                 # 1–3% position sizing
TIMEFRAME_MAIN   = TimeFrameUnit.Hour   # Suggested trading timeframe
TIMEFRAME_TREND  = TimeFrameUnit.Day    # Trend‑defining timeframe


# Set tracking signal lags over a predefined window
WINDOW_SIZE = 5
rsi_bounce_bar = None
macd_cross_bar = None
rsi_retreat_bar = None
macd_death_cross_bar = None
macd_centerline_bar = None
current_bar_index = 0

# Load environment variables
# Please safely store your API keys and never commit them to the repository (use .gitignore)
load_dotenv()
API_KEY = os.getenv("ALPACA_PAPER_API_KEY")
API_SECRET = os.getenv("ALPACA_PAPER_SECRET_KEY") 
ALPACA_PAPER_TRADE = os.getenv("ALPACA_PAPER_TRADE", "True")  # Default to paper trading (Returns "True" if ALPACA_PAPER_TRADE not set)
trade_api_url = os.getenv("TRADE_API_URL")

if not API_KEY or not API_SECRET:
    raise RuntimeError("Missing Alpaca API credentials in environment variables.")

# setup trading clients
trade_client = TradingClient(api_key=API_KEY, secret_key=API_SECRET, paper=ALPACA_PAPER_TRADE, url_override=trade_api_url)
stock_data_client = StockHistoricalDataClient(api_key=API_KEY, secret_key=API_SECRET)

# Helper: Pause execution until the specified UTC datetime.
def sleep_until(target_time, chunk_seconds=30):
    """Pause until target_time (UTC) in small chunks for responsiveness."""
    if target_time.tzinfo is None:
        target_time = target_time.replace(tzinfo=timezone.utc)
    while True:
        now = datetime.now(timezone.utc)
        remaining = (target_time - now).total_seconds()
        if remaining <= 0:
            break
        time.sleep(min(remaining, chunk_seconds))
        
# Helper: Fetch recent bar data  
def fetch_bars(client: StockHistoricalDataClient, underlying_symbol: str, timeframe_unit: TimeFrameUnit, days: int = 90) -> pd.DataFrame:
    today = datetime.now(NY_TZ).date()
    req = StockBarsRequest(
        symbol_or_symbols=[underlying_symbol],
        timeframe=TimeFrame(amount=1, unit=timeframe_unit),  # specify timeframe
        start=today - timedelta(days=days),             # specify start datetime, default=the beginning of the current day.
    )
    return client.get_stock_bars(req).df

# Helper: Compute RSI with Wilder's smoothing
def compute_rsi(prices, period):
    deltas = prices.diff().dropna()
    gains = deltas.where(deltas > 0, 0)
    losses = (-deltas).where(deltas < 0, 0)
    # Calculate initial average gain and loss
    avg_gain = gains.rolling(period).mean()
    avg_loss = losses.rolling(period).mean()
    # Calculate RS and RSI for all periods
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Helper: Compute MACD and its signal line
def compute_macd(prices, fast, slow, signal):
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return macd_line, signal_line

# Helper: Calculate buying power limit based on account value and risk percentage
def calculate_buying_power_limit(buy_power_limit):
    # Check account buying power
    buying_power = float(trade_client.get_account().buying_power)
    # Calculate the limit amount of buying power to use for the trade
    buying_power_limit = buying_power * buy_power_limit
    return buying_power_limit

# Helper: Get the latest price of the underlying stock
def get_underlying_price(symbol):
    # Get the latest trade for the underlying stock
    underlying_trade_request = StockLatestTradeRequest(symbol_or_symbols=symbol)
    underlying_trade_response = stock_data_client.get_stock_latest_trade(underlying_trade_request)
    return underlying_trade_response[symbol].price

def get_next_bar_time(current_bar_time, timeframe):
    """Calculate the next bar time based on the current timeframe"""
    if timeframe == TimeFrameUnit.Hour:
        return current_bar_time + timedelta(hours=1)
    elif timeframe == TimeFrameUnit.Day:
        return current_bar_time + timedelta(days=1)

def main():
    """Main trading loop and setup."""
    # Configure logging
    logging.basicConfig(
        filename="trade_log.txt",          # file to write
        level=logging.INFO,                # log INFO and above
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    logging.info("=== Strategy started ===")

    # remembers whether the market was open in the previous iteration
    clock = trade_client.get_clock()
    market_open = clock.is_open

    # Set tracking signal flags over a predefined window
    global rsi_bounce_bar, macd_cross_bar, rsi_retreat_bar, macd_death_cross_bar, macd_centerline_bar, current_bar_index
    rsi_bounce_bar = None
    macd_cross_bar = None
    rsi_retreat_bar = None
    macd_death_cross_bar = None
    macd_centerline_bar = None
    current_bar_index = 0

    while True:
        clock = trade_client.get_clock()

        # Detect if the market has just transitioned from open to closed.
        if market_open and not clock.is_open:
            logging.info("Market closed. Sleeping until next open at %s", clock.next_open)
            market_open = False
            sleep_until(clock.next_open)
            continue        # skip the rest of the loop while the market is shut

        # Detect if the market has just transitioned from closed to open.
        if (not market_open) and clock.is_open:
            logging.info("Market opened. Resuming trading")
            market_open = True           # fall through and run the trading logic

        # Detect if the market is closed (e.g., at script start or unexpected state), exit to prevent trading.
        if not clock.is_open:
            logging.info("Market is closed. Exiting.")
            exit(0)
        
        # Fetch data
        df_main = fetch_bars(stock_data_client, underlying_symbol, TIMEFRAME_MAIN, days=MA_SLOW + 100)
        df_trend = fetch_bars(stock_data_client, underlying_symbol, TIMEFRAME_TREND, days=MA_SLOW + 10)
        logging.info("Fetched %d main bars and %d trend bars", len(df_main), len(df_trend))
        
        # Update current bar index
        current_bar_index = len(df_main) - 1

        # Check if we currently hold the underlying_symbol
        try:
            position = trade_client.get_open_position(underlying_symbol)
            position_open = True
            current_qty = int(position.qty)
        except Exception as e:
            position_open = False
            current_qty = 0

        # Compute indicators using helper functions
        prices = df_main.close
        rsi_series = compute_rsi(prices, RSI_PERIOD)
        macd_line, signal_line = compute_macd(prices, MACD_FAST, MACD_SLOW, MACD_SIGNAL)

        # Get latest values
        rsi_now = rsi_series.iloc[-1]
        rsi_prev = rsi_series.iloc[-2]
        macd_now = macd_line.iloc[-1]
        macd_prev = macd_line.iloc[-2]
        sig_now = signal_line.iloc[-1]
        sig_prev = signal_line.iloc[-2]

        # Trend filter on higher timeframe with NaN check
        ma_fast = df_trend.close.rolling(MA_FAST).mean()
        ma_mid = df_trend.close.rolling(MA_MID).mean()
        ma_slow = df_trend.close.rolling(MA_SLOW).mean()
        
        # Check if we have enough data for all MAs
        if not (ma_fast.isna().any() or ma_mid.isna().any() or ma_slow.isna().any()):
            in_uptrend = (ma_fast.iloc[-1] > ma_mid.iloc[-1]) and (ma_mid.iloc[-1] > ma_slow.iloc[-1])
        else:
            in_uptrend = False

        # Calculate position size based on buying power
        buying_power_limit = calculate_buying_power_limit(BUY_POWER_LIMIT)
        current_price = get_underlying_price(underlying_symbol)
        position_size = int(buying_power_limit / current_price)

        # Detect RSI oversold bounce
        if (rsi_prev < 30) and (rsi_now > 30):
            rsi_bounce_bar = current_bar_index

        # Detect MACD golden cross
        if (macd_prev < sig_prev) and (macd_now > sig_now):
            macd_cross_bar = current_bar_index

        # Entry logic
        if not position_open and in_uptrend and position_size > 0:
            if (rsi_bounce_bar is not None and 
                macd_cross_bar is not None and 
                abs(rsi_bounce_bar - macd_cross_bar) <= WINDOW_SIZE):
                
                req = MarketOrderRequest(
                    symbol=underlying_symbol,
                    qty=position_size,  # Use calculated position size
                    side=OrderSide.BUY,
                    type=OrderType.MARKET,
                    time_in_force=TimeInForce.DAY,
                )
                res = trade_client.submit_order(req)
                logging.info(
                    "BUY ORDER SUBMITTED - Symbol: %s | Qty: %d | Est.Price: $%.2f | OrderID: %s | ClientOrderID: %s | SubmittedAt: %s",
                    underlying_symbol,
                    position_size,
                    current_price,
                    res.id,
                    res.client_order_id,
                    res.submitted_at
                )
                # Reset entry signals
                rsi_bounce_bar = None
                macd_cross_bar = None

        # Detect RSI overbought retreat
        if (rsi_prev > 70) and (rsi_now < 65):
            rsi_retreat_bar = current_bar_index

        # Detect MACD bearish signals
        if (macd_prev > sig_prev) and (macd_now < sig_now):  # death cross
            macd_death_cross_bar = current_bar_index
        elif macd_prev > 0 and macd_now < 0:  # centerline drop
            macd_centerline_bar = current_bar_index

        # Exit logic
        if position_open:
            if (rsi_retreat_bar is not None and 
                ((macd_death_cross_bar is not None and 
                  abs(rsi_retreat_bar - macd_death_cross_bar) <= WINDOW_SIZE) or
                 (macd_centerline_bar is not None and 
                  abs(rsi_retreat_bar - macd_centerline_bar) <= WINDOW_SIZE))):
                
                req = MarketOrderRequest(
                    symbol=underlying_symbol,
                    qty=current_qty,
                    side=OrderSide.SELL,
                    type=OrderType.MARKET,
                    time_in_force=TimeInForce.DAY,
                )
                res = trade_client.submit_order(req)
                logging.info(
                    "SELL ORDER SUBMITTED - Symbol: %s | Qty: %d | Est.Price: $%.2f | OrderID: %s | ClientOrderID: %s | SubmittedAt: %s",
                    underlying_symbol,
                    current_qty,
                    current_price,
                    res.id,
                    res.client_order_id,
                    res.submitted_at
                )
                # Reset exit signals
                rsi_retreat_bar = None
                macd_death_cross_bar = None
                macd_centerline_bar = None
        # Hourly scheduling
        # Compute the timestamp for the next top of hour
        next_run = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        # Pause until that exact moment
        sleep_until(next_run, chunk_seconds=30)

# The code below ensures that the main() function is called only when this script is executed directly.
# It prevents main() from running if the script is imported as a module in another script.
if __name__ == "__main__":
    main()
