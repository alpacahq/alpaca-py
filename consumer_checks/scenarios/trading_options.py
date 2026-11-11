"""Trading API: option exercise, checked without exercising anything.

A real exercise cannot be undone, needs market hours, and settles
asynchronously, so a scenario could not clean up after it. This scenario
checks the part the SDK owns: the request it sends and the error users get
when the account holds no such position.
"""

from __future__ import annotations

from typing import Any, Dict

from alpaca.common.exceptions import APIError
from alpaca.trading.enums import ContractType
from alpaca.trading.models import OptionContractsResponse
from alpaca.trading.requests import GetOptionContractsRequest

from . import Context, scenario


@scenario(covers=["TradingClient.exercise_options_position"])
def exercise_without_position_raises(ctx: Context) -> Dict[str, Any]:
    response = ctx.trading.get_option_contracts(
        GetOptionContractsRequest(
            underlying_symbols=["AAPL"], type=ContractType.CALL, limit=1
        )
    )
    assert isinstance(response, OptionContractsResponse)
    assert response.option_contracts
    contract = response.option_contracts[0]

    positions = ctx.trading.get_all_positions()
    assert isinstance(positions, list)
    if any(position.symbol == contract.symbol for position in positions):
        # Never exercise for real: the account holds this contract.
        raise AssertionError(f"refusing to exercise held contract {contract.symbol}")

    try:
        ctx.trading.exercise_options_position(contract.symbol)
    except APIError as error:
        assert isinstance(error.status_code, int)
        assert 400 <= error.status_code < 500
        return {"contract": contract, "error": error}
    raise AssertionError("exercising an option the account does not hold should fail")
