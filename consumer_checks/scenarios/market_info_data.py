"""News, screener and corporate actions data."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Dict

from alpaca.data.enums import CorporateActionsType, MarketType, MostActivesBy
from alpaca.data.models import News, NewsSet
from alpaca.data.models.corporate_actions import CashDividend, CorporateActionsSet
from alpaca.data.models.screener import ActiveStock, MostActives, Mover, Movers
from alpaca.data.requests import (
    CorporateActionsRequest,
    MarketMoversRequest,
    MostActivesRequest,
    NewsRequest,
)

from . import Context, scenario


@scenario(covers=["NewsClient.get_news"])
def news_for_symbol_in_a_day(ctx: Context) -> Dict[str, Any]:
    news = ctx.news.get_news(
        NewsRequest(
            symbols="AAPL",
            start=datetime(2024, 3, 4, tzinfo=timezone.utc),
            end=datetime(2024, 3, 5, tzinfo=timezone.utc),
            limit=3,
        )
    )

    assert isinstance(news, NewsSet)
    articles = news.data["news"]
    assert 1 <= len(articles) <= 3
    article = articles[0]
    assert isinstance(article, News)
    assert "AAPL" in article.symbols
    assert isinstance(article.id, int)
    return {"news": news, "df": news.df}


@scenario(covers=["ScreenerClient.get_most_actives"])
def most_active_stocks(ctx: Context) -> Dict[str, Any]:
    actives = ctx.screener.get_most_actives(
        MostActivesRequest(top=5, by=MostActivesBy.VOLUME)
    )

    assert isinstance(actives, MostActives)
    assert 1 <= len(actives.most_actives) <= 5
    assert all(isinstance(stock, ActiveStock) for stock in actives.most_actives)
    volumes = [stock.volume for stock in actives.most_actives]
    assert volumes == sorted(volumes, reverse=True)
    return {"actives": actives}


@scenario(covers=["ScreenerClient.get_market_movers"])
def stock_market_movers(ctx: Context) -> Dict[str, Any]:
    movers = ctx.screener.get_market_movers(
        MarketMoversRequest(top=5, market_type=MarketType.STOCKS)
    )

    assert isinstance(movers, Movers)
    assert movers.market_type == MarketType.STOCKS
    assert len(movers.gainers) <= 5 and len(movers.losers) <= 5
    assert all(isinstance(mover, Mover) for mover in movers.gainers + movers.losers)
    return {"movers": movers}


@scenario(covers=["CorporateActionsClient.get_corporate_actions"])
def cash_dividends_for_a_quarter(ctx: Context) -> Dict[str, Any]:
    actions = ctx.corporate_actions.get_corporate_actions(
        CorporateActionsRequest(
            symbols=["AAPL"],
            types=[CorporateActionsType.CASH_DIVIDEND],
            start=date(2024, 1, 1),
            end=date(2024, 3, 31),
        )
    )

    assert isinstance(actions, CorporateActionsSet)
    dividends = actions.data["cash_dividends"]
    assert dividends
    dividend = dividends[0]
    assert isinstance(dividend, CashDividend)
    assert dividend.symbol == "AAPL"
    return {"actions": actions}
