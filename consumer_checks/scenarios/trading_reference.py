"""Trading API reference data: asset lists, option contracts, corporate announcements."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict

from alpaca.trading.enums import (
    AssetClass,
    AssetStatus,
    ContractType,
    CorporateActionType,
)
from alpaca.trading.models import (
    Asset,
    CorporateActionAnnouncement,
    OptionContract,
    OptionContractsResponse,
)
from alpaca.trading.requests import (
    GetAssetsRequest,
    GetCorporateAnnouncementsRequest,
    GetOptionContractsRequest,
)

from . import Context, scenario


@scenario(covers=["TradingClient.get_all_assets"])
def active_crypto_assets(ctx: Context) -> Dict[str, Any]:
    # Filtered to crypto: the unfiltered list is about 10,000 assets.
    assets = ctx.trading.get_all_assets(
        GetAssetsRequest(asset_class=AssetClass.CRYPTO, status=AssetStatus.ACTIVE)
    )

    assert isinstance(assets, list)
    assert all(isinstance(asset, Asset) for asset in assets)
    assert all(asset.asset_class == AssetClass.CRYPTO for asset in assets)
    btc = [asset for asset in assets if asset.symbol == "BTC/USD"]
    assert len(btc) == 1
    # The full list changes as assets are listed; the snapshot keeps one entry.
    return {"btc": btc[0], "is_list": isinstance(assets, list)}


@scenario(
    covers=[
        "TradingClient.get_option_contracts",
        "TradingClient.get_option_contract",
    ]
)
def option_contracts_for_underlying(ctx: Context) -> Dict[str, Any]:
    # No expiration filter: the API defaults to contracts expiring soon, so live
    # runs keep working as time passes. Replay uses whatever was recorded.
    response = ctx.trading.get_option_contracts(
        GetOptionContractsRequest(
            underlying_symbols=["AAPL"],
            type=ContractType.CALL,
            limit=3,
        )
    )

    assert isinstance(response, OptionContractsResponse)
    contracts = response.option_contracts
    assert contracts
    assert len(contracts) <= 3
    first = contracts[0]
    assert isinstance(first, OptionContract)
    assert first.underlying_symbol == "AAPL"
    assert first.type == ContractType.CALL
    assert isinstance(first.expiration_date, date)

    by_symbol = ctx.trading.get_option_contract(first.symbol)
    by_id = ctx.trading.get_option_contract(first.id)
    assert isinstance(by_symbol, OptionContract) and isinstance(by_id, OptionContract)
    assert by_symbol.id == by_id.id == first.id
    return {"response": response, "by_symbol": by_symbol}


@scenario(
    covers=[
        "TradingClient.get_corporate_announcements",
        "TradingClient.get_corporate_announcement_by_id",
    ]
)
def dividend_announcements(ctx: Context) -> Dict[str, Any]:
    # Both methods are deprecated in favor of CorporateActionsClient, and users
    # see that warning too. Removing them is a break: this scenario will flag it.
    # AAPL declared a dividend on 1 February 2024. The range must be at most 90 days.
    announcements = ctx.trading.get_corporate_announcements(
        GetCorporateAnnouncementsRequest(
            ca_types=[CorporateActionType.DIVIDEND],
            since=date(2024, 1, 1),
            until=date(2024, 3, 1),
            symbol="AAPL",
        )
    )

    assert isinstance(announcements, list)
    assert announcements
    first = announcements[0]
    assert isinstance(first, CorporateActionAnnouncement)
    assert first.initiating_symbol == "AAPL"

    by_id = ctx.trading.get_corporate_announcement_by_id(first.id)
    assert isinstance(by_id, CorporateActionAnnouncement)
    assert by_id.id == first.id
    return {"announcements": announcements, "by_id": by_id}
