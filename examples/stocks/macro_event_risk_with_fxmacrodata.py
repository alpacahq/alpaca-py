"""Join Alpaca stock bars with FXMacroData macro event context.

This example is read-only. It fetches recent Alpaca daily bars for a symbol and
adds public USD release-calendar and inflation-history context from FXMacroData.

Environment variables:
    ALPACA_API_KEY: Alpaca API key for market data.
    ALPACA_SECRET_KEY: Alpaca secret key for market data.
    SYMBOL: Optional stock symbol, default SPY.
    FXMACRODATA_API_KEY or FXMD_API_KEY: Optional key for protected FXMacroData
        coverage. The public USD examples below do not require it.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame


FXMACRODATA_BASE_URL = "https://fxmacrodata.com/api"


def _fxmacrodata_headers() -> dict[str, str]:
    api_key = os.environ.get("FXMACRODATA_API_KEY") or os.environ.get("FXMD_API_KEY")
    if not api_key:
        return {}
    return {"X-API-Key": api_key}


def fetch_fxmacrodata(
    path: str, params: dict[str, Any] | None = None
) -> dict[str, Any]:
    response = requests.get(
        f"{FXMACRODATA_BASE_URL}{path}",
        params=params,
        headers=_fxmacrodata_headers(),
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def upcoming_us_releases(days: int = 14) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=days)
    calendar = fetch_fxmacrodata("/v1/calendar/USD")
    rows = []
    for row in calendar.get("data", []):
        release_at = parse_iso_datetime(row.get("announcement_datetime_utc"))
        if release_at and now <= release_at <= end:
            rows.append(
                {
                    "release_at": release_at,
                    "name": row.get("name") or row.get("release"),
                    "source": row.get("source"),
                    "confirmed": row.get("release_date_confirmed"),
                }
            )
    return sorted(rows, key=lambda item: item["release_at"])


def latest_us_inflation_rows(limit: int = 3) -> list[dict[str, Any]]:
    history = fetch_fxmacrodata("/v1/announcements/USD/inflation")
    rows = history.get("data", [])
    return rows[-limit:]


def recent_stock_bars(symbol: str) -> Any:
    api_key = os.environ.get("ALPACA_API_KEY")
    secret_key = os.environ.get("ALPACA_SECRET_KEY")
    if not api_key or not secret_key:
        raise RuntimeError(
            "Set ALPACA_API_KEY and ALPACA_SECRET_KEY to fetch Alpaca bars."
        )

    client = StockHistoricalDataClient(api_key=api_key, secret_key=secret_key)
    request = StockBarsRequest(
        symbol_or_symbols=[symbol],
        timeframe=TimeFrame.Day,
        start=datetime.now(timezone.utc) - timedelta(days=30),
    )
    return client.get_stock_bars(request).df


def main() -> None:
    symbol = os.environ.get("SYMBOL", "SPY")

    print(f"Macro event-risk context for {symbol}")
    print()

    try:
        bars = recent_stock_bars(symbol)
    except RuntimeError as exc:
        print(f"Alpaca bars skipped: {exc}")
    else:
        print("Recent Alpaca bars:")
        print(bars.tail(5))
        print()

    releases = upcoming_us_releases(days=14)
    print("Upcoming USD macro releases:")
    if not releases:
        print("No confirmed releases found in the next 14 days.")
    for event in releases[:10]:
        confirmed = "confirmed" if event["confirmed"] else "unconfirmed"
        print(f"- {event['release_at'].isoformat()} {event['name']} ({confirmed})")
    print()

    print("Latest USD inflation rows:")
    for row in latest_us_inflation_rows():
        value = row.get("val")
        date = row.get("date")
        released = row.get("announcement_datetime")
        print(f"- {date}: {value} released at {released}")


if __name__ == "__main__":
    main()
