"""A watchlist on an account this scenario creates and deletes before closing it."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from alpaca.trading.models import Asset, Watchlist
from alpaca.trading.requests import CreateWatchlistRequest, UpdateWatchlistRequest

from . import Context, scenario
from ._broker import expect_client_error, opened_account

BROKER = "broker"


def _symbols(assets: Optional[List[Asset]]) -> List[str]:
    return sorted(asset.symbol for asset in assets or [])


@scenario(
    covers=[
        "BrokerClient.get_watchlists_for_account",
        "BrokerClient.get_watchlist_for_account_by_id",
        "BrokerClient.create_watchlist_for_account",
        "BrokerClient.update_watchlist_for_account_by_id",
        "BrokerClient.add_asset_to_watchlist_for_account_by_id",
        "BrokerClient.remove_asset_from_watchlist_for_account_by_id",
        "BrokerClient.delete_watchlist_from_account_by_id",
    ],
    credentials=BROKER,
)
def watchlist_lifecycle(ctx: Context) -> Dict[str, Any]:
    name = f"consumer-check-{ctx.unique_id('watchlist')[:12]}"
    with opened_account(ctx, "watchlist") as session:
        session.wait_until_ready()
        account_id = session.account.id
        created = ctx.broker.create_watchlist_for_account(
            account_id, CreateWatchlistRequest(name=name, symbols=["AAPL"])
        )
        assert isinstance(created, Watchlist)
        try:
            assert created.name == name
            assert _symbols(created.assets) == ["AAPL"]

            all_lists = ctx.broker.get_watchlists_for_account(account_id)
            assert isinstance(all_lists, list)
            listed = [
                watchlist for watchlist in all_lists if watchlist.id == created.id
            ]
            assert len(listed) == 1

            fetched = ctx.broker.get_watchlist_for_account_by_id(account_id, created.id)
            assert isinstance(fetched, Watchlist)
            assert _symbols(fetched.assets) == ["AAPL"]

            updated = ctx.broker.update_watchlist_for_account_by_id(
                account_id,
                created.id,
                UpdateWatchlistRequest(
                    name=f"{name}-renamed", symbols=["AAPL", "MSFT"]
                ),
            )
            assert isinstance(updated, Watchlist)
            assert updated.name == f"{name}-renamed"
            assert _symbols(updated.assets) == ["AAPL", "MSFT"]

            added = ctx.broker.add_asset_to_watchlist_for_account_by_id(
                account_id, created.id, "GOOGL"
            )
            assert isinstance(added, Watchlist)
            assert _symbols(added.assets) == ["AAPL", "GOOGL", "MSFT"]

            removed = ctx.broker.remove_asset_from_watchlist_for_account_by_id(
                account_id, created.id, "AAPL"
            )
            assert isinstance(removed, Watchlist)
            assert _symbols(removed.assets) == ["GOOGL", "MSFT"]
        finally:
            ctx.broker.delete_watchlist_from_account_by_id(account_id, created.id)

        gone = expect_client_error(
            lambda: ctx.broker.get_watchlist_for_account_by_id(account_id, created.id)
        )
        # The account exists, so 401/403 would mean the keys, not the watchlist.
        assert gone.status_code not in (401, 403)

    return {
        "created": created,
        "listed": listed[0],
        "updated": updated,
        "added": added,
        "removed": removed,
        "after_delete": gone,
    }
