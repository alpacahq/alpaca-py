"""Option condition codes, available starting with the 0.50.0 SDK.

Recorded with this checkout until BASELINE reaches 0.50.0.
"""

from __future__ import annotations

from typing import Any, Dict

from . import Context, scenario


@scenario(
    covers=["OptionHistoricalDataClient.get_option_condition_codes"],
    since="0.50.0",
)
def trade_and_quote_condition_codes(ctx: Context) -> Dict[str, Any]:
    trade_codes = ctx.option_data.get_option_condition_codes("trade")
    quote_codes = ctx.option_data.get_option_condition_codes("quote")

    assert isinstance(trade_codes, dict) and trade_codes
    assert isinstance(quote_codes, dict) and quote_codes
    assert all(isinstance(name, str) for name in trade_codes.values())
    assert all(isinstance(name, str) for name in quote_codes.values())
    return {"trade_codes": trade_codes, "quote_codes": quote_codes}
