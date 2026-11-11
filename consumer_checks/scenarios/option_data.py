"""Historical and latest option market data.

Uses the free ``indicative`` feed, which every paper account has. Option
contracts expire, so:

* latest data uses a contract picked from the option chain, filtered by a fixed
  strike range, which keeps the request the same on every replay and keeps
  live runs working as contracts roll over;
* historical data uses a contract that expired on 8 March 2024.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from alpaca.data.enums import OptionsFeed
from alpaca.data.models import BarSet, OptionsSnapshot, Quote, Trade, TradeSet
from alpaca.data.requests import (
    OptionBarsRequest,
    OptionChainRequest,
    OptionLatestQuoteRequest,
    OptionLatestTradeRequest,
    OptionSnapshotRequest,
    OptionTradesRequest,
)
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.enums import ContractType

from . import Context, scenario

EXPIRED_CONTRACT = "AAPL240308C00175000"  # AAPL 175 call, expired 8 March 2024
WEEK_START = datetime(2024, 3, 4, tzinfo=timezone.utc)
WEEK_END = datetime(2024, 3, 9, tzinfo=timezone.utc)


@scenario(
    covers=[
        "OptionHistoricalDataClient.get_option_chain",
        "OptionHistoricalDataClient.get_option_latest_quote",
        "OptionHistoricalDataClient.get_option_latest_trade",
        "OptionHistoricalDataClient.get_option_snapshot",
    ]
)
def chain_then_latest_contract_data(ctx: Context) -> Dict[str, Any]:
    chain = ctx.option_data.get_option_chain(
        OptionChainRequest(
            underlying_symbol="AAPL",
            feed=OptionsFeed.INDICATIVE,
            type=ContractType.CALL,
            strike_price_gte=200,
            strike_price_lte=205,
        )
    )

    assert isinstance(chain, dict)
    assert chain
    assert all(isinstance(snap, OptionsSnapshot) for snap in chain.values())
    assert all(symbol.startswith("AAPL") for symbol in chain)
    traded = sorted(symbol for symbol, snap in chain.items() if snap.latest_trade)
    assert traded, "no contract in the strike range has traded"
    symbol = traded[0]

    quotes = ctx.option_data.get_option_latest_quote(
        OptionLatestQuoteRequest(
            symbol_or_symbols=[symbol], feed=OptionsFeed.INDICATIVE
        )
    )
    trades = ctx.option_data.get_option_latest_trade(
        OptionLatestTradeRequest(
            symbol_or_symbols=[symbol], feed=OptionsFeed.INDICATIVE
        )
    )
    snapshots = ctx.option_data.get_option_snapshot(
        OptionSnapshotRequest(symbol_or_symbols=[symbol], feed=OptionsFeed.INDICATIVE)
    )

    assert isinstance(quotes, dict) and isinstance(quotes[symbol], Quote)
    assert isinstance(trades, dict) and isinstance(trades[symbol], Trade)
    assert isinstance(snapshots, dict) and isinstance(
        snapshots[symbol], OptionsSnapshot
    )
    return {
        "chain_entry": chain[symbol],
        "quote": quotes[symbol],
        "trade": trades[symbol],
        "snapshot": snapshots[symbol],
    }


@scenario(
    covers=[
        "OptionHistoricalDataClient.get_option_bars",
        "OptionHistoricalDataClient.get_option_trades",
    ]
)
def expired_contract_bars_and_trades(ctx: Context) -> Dict[str, Any]:
    bars = ctx.option_data.get_option_bars(
        OptionBarsRequest(
            symbol_or_symbols=EXPIRED_CONTRACT,
            timeframe=TimeFrame.Day,
            start=WEEK_START,
            end=WEEK_END,
        )
    )
    trades = ctx.option_data.get_option_trades(
        OptionTradesRequest(
            symbol_or_symbols=EXPIRED_CONTRACT,
            start=WEEK_START,
            end=WEEK_END,
            limit=5,
        )
    )

    assert isinstance(bars, BarSet) and isinstance(trades, TradeSet)
    assert bars[EXPIRED_CONTRACT] and len(bars[EXPIRED_CONTRACT]) <= 5
    assert len(trades[EXPIRED_CONTRACT]) == 5
    assert all(bar.symbol == EXPIRED_CONTRACT for bar in bars[EXPIRED_CONTRACT])
    return {"bars": bars, "trades": trades, "bars_df": bars.df}


@scenario(covers=["OptionHistoricalDataClient.get_option_exchange_codes"])
def exchange_codes(ctx: Context) -> Dict[str, Any]:
    codes = ctx.option_data.get_option_exchange_codes()

    # A plain dict of exchange code to exchange name.
    assert isinstance(codes, dict)
    assert codes
    assert all(
        isinstance(code, str) and isinstance(name, str) for code, name in codes.items()
    )
    return {"codes": codes}
