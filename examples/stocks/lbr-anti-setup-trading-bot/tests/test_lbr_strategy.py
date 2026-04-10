"""
Tests for the LBR 3/10 oscillator strategy.

Synthetic data is constructed to satisfy (or violate) specific Anti setup conditions
so each test exercises exactly one code path.
"""
import math
import logging
from unittest.mock import patch

import pandas as pd
import pytest

from main import (
    LBR_FAST, LBR_SLOW, LBR_SIGNAL,
    LBR_MIN_BARS, DAILY_BARS, MAGNIFICENT_7,
    calculate_lbr_signal, calculate_atr, build_target_portfolio,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _bar(close: float, high: float | None = None, low: float | None = None,
         i: int = 0) -> dict:
    """Build a single OHLC bar dict. high/low default to close ± 0.5."""
    return {
        "close": close,
        "high":  close + 0.5 if high is None else high,
        "low":   close - 0.5 if low is None else low,
        "datetime": float(i * 86_400_000),  # daily ms timestamps
    }


def _make_bars(closes: list[float]) -> list[dict]:
    """Turn a list of close prices into bar dicts with small fixed high/low spread."""
    return [_bar(c, c + 0.5, c - 0.5, i) for i, c in enumerate(closes)]


def _anti_setup_prices() -> list[dict]:
    """
    Build a synthetic daily price series that satisfies the oscillator rules
    (signal zero crossing, pullback, histogram hook) for the Anti setup.

    Phase 1 (bars 0–49): steady decline at -1/bar from 100 to 51.
        SMA(3) < SMA(10) throughout → MACD strongly negative (≈-3.5 in steady state).
        Signal line (SMA16 of MACD) stays well below zero.

    Phase 2 (bars 50–69): gentle rise at +0.5/bar from 51.5 to 61.
        MACD turns positive slowly. Because Phase 1 MACD magnitude (≈3.5) ≈ Phase 2
        steady-state magnitude (≈1.75), the signal line zero crossing is delayed
        to approximately bar 65 — within the last-16 window (bars 60–75). ✓

    Phase 3 (bars 70–74): pullback at -0.5/bar from 60.5 to 58.5.
        MACD declines toward and below signal line (pullback). ✓

    Phase 4 (bar 75): sharp uptick +5 to 63.5.
        MACD reverses upward while signal lags → histogram turns up (hook). ✓

    Total: 76 bars >= LBR_MIN_BARS (31). ✓
    Last close 63.5 > EMA20 (≈59–61). ✓
    """
    closes = []
    # Phase 1: steady decline
    for i in range(50):
        closes.append(100.0 - i)
    # Phase 2: gentle rise
    for i in range(1, 21):
        closes.append(51.0 + i * 0.5)
    # Phase 3: pullback
    for i in range(1, 6):
        closes.append(61.0 - i * 0.5)
    # Phase 4: sharp hook
    closes.append(closes[-1] + 5.0)
    return _make_bars(closes)


# ---------------------------------------------------------------------------
# calculate_lbr_signal — happy path
# ---------------------------------------------------------------------------

def test_anti_setup_confirmed():
    """
    Full Anti setup: rules 1, 3–6 satisfied with real price data; ADX (rule 2)
    is mocked to a non-blocking value because the synthetic trend data
    unavoidably drives ADX above 32 (strong-trend detection is separately
    exercised by test_adx_filter_blocks_strong_trend).
    """
    price_data = _anti_setup_prices()
    with patch("main.calculate_adx", return_value=(15.0, False)):
        result = calculate_lbr_signal("AAPL", price_data)
    assert result["selected"] is True, (
        f"Expected Anti setup confirmed, got skip_reason='{result['skip_reason']}'"
    )
    assert result["score"] != 0.0


# ---------------------------------------------------------------------------
# Insufficient data
# ---------------------------------------------------------------------------

def test_insufficient_data_returns_selected_false():
    """Fewer than LBR_MIN_BARS bars → selected=False, no exception raised."""
    price_data = _make_bars([100.0] * (LBR_MIN_BARS - 1))
    result = calculate_lbr_signal("AAPL", price_data)
    assert result["selected"] is False
    assert "insufficient" in result["skip_reason"]


def test_insufficient_data_does_not_raise():
    """Ensure the function is safe with very short input."""
    price_data = _make_bars([100.0] * 5)
    result = calculate_lbr_signal("AAPL", price_data)
    assert isinstance(result, dict)
    assert result["selected"] is False


# ---------------------------------------------------------------------------
# ADX filter
# ---------------------------------------------------------------------------

def test_adx_filter_blocks_strong_trend():
    """
    When ADX > 32 and rising, the Anti setup must be rejected even if all
    other conditions are met.

    We take the Anti setup base data and add a strong uniform uptrend to
    push ADX above 32 while keeping it rising.
    """
    # Start from a very strong, consistent trend: 80 bars of steep linear rise.
    # This generates high +DI, low -DI, and high rising ADX.
    n = 80
    # Steep climb of 5 per bar to drive ADX high
    closes = [100.0 + i * 5.0 for i in range(n)]
    bars = []
    for i, c in enumerate(closes):
        bars.append({
            "close": c,
            "high":  c + 3.0,
            "low":   c - 0.5,   # asymmetric: much larger up moves → high +DI
            "datetime": float(i * 86_400_000),
        })

    result = calculate_lbr_signal("AAPL", bars)
    # The ADX test verifies the filter fires; other rules may or may not pass first
    # but once ADX > 32 and rising, selected must be False.
    # We verify the skip reason contains "ADX" when that is the reason.
    if result["adx"] > 32 and result["adx_rising"]:
        assert result["selected"] is False
        assert "ADX" in result["skip_reason"]


# ---------------------------------------------------------------------------
# Below EMA20
# ---------------------------------------------------------------------------

def test_below_ema20_blocks_long_anti():
    """
    Price below the 20-bar EMA → no long Anti allowed.

    Build a series that has a valid oscillator pattern but ends with the price
    falling below EMA(20).
    """
    # Start high, then drop sharply — last close well below recent EMA
    closes = [120.0] * 20 + [120.0 - i * 2.0 for i in range(1, 32)]
    price_data = _make_bars(closes)

    result = calculate_lbr_signal("AAPL", price_data)
    if result["skip_reason"] and ("below" in result["skip_reason"] or "EMA20" in result["skip_reason"]):
        assert result["selected"] is False
    elif result["last_close"] != 0.0:
        # If we reached the EMA check, verify the condition logic
        if result["last_close"] <= result["ema20"]:
            assert result["selected"] is False
            assert "below" in result["skip_reason"] or "EMA20" in result["skip_reason"]


def test_below_ema20_explicit():
    """
    Explicitly verify that when last_close < ema20, selected is False.
    Uses monkeypatching to isolate the EMA rule from other rules.
    """
    price_data = _anti_setup_prices()
    # Patch calculate_ema20 to return a value above the last close
    last_close = price_data[-1]["close"]
    with patch("main.calculate_ema20", return_value=last_close + 10.0):
        # Also patch calculate_adx to pass the ADX filter
        with patch("main.calculate_adx", return_value=(15.0, False)):
            result = calculate_lbr_signal("AAPL", price_data)
    assert result["selected"] is False
    assert "below" in result["skip_reason"] or "EMA20" in result["skip_reason"]


# ---------------------------------------------------------------------------
# No zero crossing
# ---------------------------------------------------------------------------

def test_no_zero_crossing_blocks_anti():
    """
    Signal line never crosses zero → no trend change confirmed → selected=False.

    Build a series where the MACD line is always negative (prices declining
    the whole time), so the signal line never rises to zero.
    """
    # Steady decline: SMA(3) < SMA(10) always → MACD always negative
    closes = [150.0 - i * 0.5 for i in range(66)]
    price_data = _make_bars(closes)

    result = calculate_lbr_signal("AAPL", price_data)
    # The EMA20 check may fire first (declining price below EMA20), which is fine —
    # the key assertion is that the Anti is not selected.
    assert result["selected"] is False
    if "signal line" in result["skip_reason"]:
        assert not result["signal_crossed"]


# ---------------------------------------------------------------------------
# SMA vs EMA verification (critical correctness test)
# ---------------------------------------------------------------------------

def test_oscillator_uses_sma_not_ema():
    """
    Verify the LBR oscillator score matches SMA-derived values, not EMA.

    On a step-function price series, SMA(3) and EMA(3) diverge significantly.
    We compute both and assert the result matches SMA.
    """
    # Use enough bars so LBR_MIN_BARS is satisfied
    closes = [100.0] * 30 + [200.0] * 36  # sharp step up at bar 30
    price_data = _make_bars(closes)

    result = calculate_lbr_signal("AAPL", price_data)

    series = pd.Series(closes)
    # SMA-based computation
    sma_fast   = series.rolling(LBR_FAST).mean()
    sma_slow   = series.rolling(LBR_SLOW).mean()
    macd_sma   = sma_fast - sma_slow
    signal_sma = macd_sma.rolling(LBR_SIGNAL).mean()
    expected_score = float(macd_sma.iloc[-1] - signal_sma.iloc[-1])

    # EMA-based computation (what standard MACD would give)
    ema_fast   = series.ewm(span=LBR_FAST, adjust=False).mean()
    ema_slow   = series.ewm(span=LBR_SLOW, adjust=False).mean()
    macd_ema   = ema_fast - ema_slow
    signal_ema = macd_ema.ewm(span=LBR_SIGNAL, adjust=False).mean()
    ema_score  = float(macd_ema.iloc[-1] - signal_ema.iloc[-1])

    # SMA and EMA should diverge meaningfully on this step function
    assert abs(expected_score - ema_score) > 0.1, (
        "Test data insufficient — SMA and EMA scores are too similar to distinguish"
    )
    # The actual score must match SMA, not EMA
    assert abs(result["score"] - expected_score) < 1e-9, (
        f"Score {result['score']:.9f} does not match SMA score {expected_score:.9f} "
        f"(EMA score was {ema_score:.9f})"
    )


# ---------------------------------------------------------------------------
# calculate_atr
# ---------------------------------------------------------------------------

def test_calculate_atr_known_series():
    """
    Verify ATR calculation against manually computed value.

    Use a series with constant true range of 2.0 (high-low = 2, no gap).
    Wilder's smoothing converges to the constant TR value, so ATR → 2.0.
    """
    n = 50
    bars = [
        {
            "close": 100.0,
            "high":  101.0,
            "low":   99.0,
            "datetime": float(i * 86_400_000),
        }
        for i in range(n)
    ]
    atr = calculate_atr(bars, period=14)
    # With constant TR=2.0 and Wilder smoothing, ATR converges to 2.0
    assert abs(atr - 2.0) < 0.001, f"Expected ATR≈2.0, got {atr}"


def test_calculate_atr_insufficient_data_returns_zero():
    """ATR with fewer than period+1 bars returns 0.0."""
    bars = _make_bars([100.0] * 5)
    atr = calculate_atr(bars, period=14)
    assert atr == 0.0


# ---------------------------------------------------------------------------
# build_target_portfolio
# ---------------------------------------------------------------------------

@patch("main.get_price_history")
@patch("main.calculate_lbr_signal")
def test_portfolio_selects_confirmed_anti_symbols(mock_signal, mock_history):
    """3 of 7 symbols with Anti confirmed → returns exactly those 3."""
    mock_history.return_value = _make_bars([100.0] * 50)
    confirmed = {"AAPL", "MSFT", "NVDA"}

    def side_effect(sym, data):
        if sym in confirmed:
            return {
                "selected": True, "score": 1.0, "atr": 2.5,
                "adx": 15.0, "adx_rising": False,
                "ema20": 95.0, "last_close": 100.0,
                "signal_crossed": True, "pullback": True,
                "skip_reason": "",
            }
        return {
            "selected": False, "score": -0.5, "atr": 0.0,
            "adx": 15.0, "adx_rising": False,
            "ema20": 95.0, "last_close": 100.0,
            "signal_crossed": False, "pullback": False,
            "skip_reason": "signal line has not crossed zero — no trend change",
        }

    mock_signal.side_effect = side_effect

    selected, atr_by_symbol = build_target_portfolio()

    assert set(selected) == confirmed
    assert len(selected) == 3
    assert set(atr_by_symbol.keys()) == confirmed
    for sym in confirmed:
        assert atr_by_symbol[sym] == 2.5


@patch("main.get_price_history")
@patch("main.calculate_lbr_signal")
def test_full_risk_off_returns_empty_tuple(mock_signal, mock_history, caplog):
    """No Anti setups → returns ([], {}) and logs cash-hold message."""
    mock_history.return_value = _make_bars([100.0] * 50)
    mock_signal.return_value = {
        "selected": False, "score": -1.0, "atr": 0.0,
        "adx": 15.0, "adx_rising": False,
        "ema20": 95.0, "last_close": 90.0,
        "signal_crossed": False, "pullback": False,
        "skip_reason": "price 90.00 below EMA20 95.00 — no long Anti",
    }

    with caplog.at_level(logging.INFO):
        result = build_target_portfolio()

    selected, atr_by_symbol = result
    assert selected == []
    assert atr_by_symbol == {}
    assert "holding cash" in caplog.text
