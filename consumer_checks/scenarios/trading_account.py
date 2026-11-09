"""Trading API: account, configuration and portfolio history (read only)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict

from alpaca.trading.enums import AccountStatus
from alpaca.trading.models import AccountConfiguration, PortfolioHistory, TradeAccount
from alpaca.trading.requests import GetPortfolioHistoryRequest

from . import Context, scenario


@scenario(
    covers=[
        "TradingClient.get_account",
        "TradingClient.get_account_configurations",
    ]
)
def account_and_configuration(ctx: Context) -> Dict[str, Any]:
    account = ctx.trading.get_account()

    assert isinstance(account, TradeAccount)
    assert isinstance(account.status, AccountStatus)
    assert account.currency == "USD"
    # Money fields are decimal strings. Users parse them, so they must stay parseable.
    assert account.cash is not None and account.buying_power is not None
    Decimal(account.cash)
    Decimal(account.buying_power)

    config = ctx.trading.get_account_configurations()
    assert isinstance(config, AccountConfiguration)
    assert isinstance(config.fractional_trading, bool)
    Decimal(config.max_margin_multiplier)
    return {"account": account, "configuration": config}


@scenario(covers=["TradingClient.get_portfolio_history"])
def portfolio_history_last_week(ctx: Context) -> Dict[str, Any]:
    history = ctx.trading.get_portfolio_history(
        GetPortfolioHistoryRequest(period="1W", timeframe="1D")
    )

    assert isinstance(history, PortfolioHistory)
    assert history.timeframe == "1D"
    # Parallel arrays: users zip them together.
    assert len(history.timestamp) == len(history.equity) == len(history.profit_loss)
    assert all(isinstance(stamp, int) for stamp in history.timestamp)
    return {"history": history}
