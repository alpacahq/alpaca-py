"""Trading API: the full watchlist lifecycle, on a watchlist the scenario owns."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from alpaca.common.exceptions import APIError
from alpaca.trading.models import Asset, Watchlist
from alpaca.trading.requests import CreateWatchlistRequest, UpdateWatchlistRequest

from . import Context, scenario


def _symbols(assets: Optional[List[Asset]]) -> List[str]:
    return sorted(asset.symbol for asset in assets or [])


@scenario(
    covers=[
        "TradingClient.create_watchlist",
        "TradingClient.get_watchlists",
        "TradingClient.get_watchlist_by_id",
        "TradingClient.update_watchlist_by_id",
        "TradingClient.add_asset_to_watchlist_by_id",
        "TradingClient.remove_asset_from_watchlist_by_id",
        "TradingClient.delete_watchlist_by_id",
    ]
)
def watchlist_lifecycle(ctx: Context) -> Dict[str, Any]:
    name = f"consumer-check-{ctx.unique_id('watchlist')[:12]}"
    created = ctx.trading.create_watchlist(
        CreateWatchlistRequest(name=name, symbols=["AAPL"])
    )
    assert isinstance(created, Watchlist)
    try:
        assert created.name == name
        assert _symbols(created.assets) == ["AAPL"]

        all_lists = ctx.trading.get_watchlists()
        assert isinstance(all_lists, list)
        # Other watchlists on the paper account are not part of the snapshot.
        listed = [watchlist for watchlist in all_lists if watchlist.id == created.id]
        assert len(listed) == 1

        fetched = ctx.trading.get_watchlist_by_id(created.id)
        assert isinstance(fetched, Watchlist)
        assert _symbols(fetched.assets) == ["AAPL"]

        updated = ctx.trading.update_watchlist_by_id(
            created.id,
            UpdateWatchlistRequest(name=f"{name}-renamed", symbols=["AAPL", "MSFT"]),
        )
        assert isinstance(updated, Watchlist)
        assert updated.name == f"{name}-renamed"
        assert _symbols(updated.assets) == ["AAPL", "MSFT"]

        added = ctx.trading.add_asset_to_watchlist_by_id(created.id, "GOOGL")
        assert isinstance(added, Watchlist)
        assert _symbols(added.assets) == ["AAPL", "GOOGL", "MSFT"]

        removed = ctx.trading.remove_asset_from_watchlist_by_id(created.id, "AAPL")
        assert isinstance(removed, Watchlist)
        assert _symbols(removed.assets) == ["GOOGL", "MSFT"]
    finally:
        ctx.trading.delete_watchlist_by_id(created.id)

    try:
        ctx.trading.get_watchlist_by_id(created.id)
    except APIError as error:
        gone = error
    else:
        raise AssertionError("a deleted watchlist should raise APIError")
    return {
        "created": created,
        "listed": listed[0],
        "updated": updated,
        "added": added,
        "removed": removed,
        "after_delete": gone,
    }
