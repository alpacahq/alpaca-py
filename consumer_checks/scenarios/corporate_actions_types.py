"""Every corporate action type ``get_corporate_actions`` parses: ``since="0.46.0"``.

``partial_calls``, ``reorganizations`` and ``capital_gains_distributions`` are
parsed into models only from 0.46.0; the BASELINE release drops them. So this
scenario is recorded with this checkout's SDK until BASELINE reaches 0.46.0.

The response is stubbed: the API rarely has one of each type in a date range,
and a stub sets every field of every type, so a rename or a retyped field shows
up in the snapshot. The request the SDK sends is frozen like any other.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List

from alpaca.data.enums import CorporateActionsType
from alpaca.data.models.corporate_actions import CorporateActionsSet
from alpaca.data.requests import CorporateActionsRequest

from . import Context, scenario

SINCE = "0.46.0"


def _action(number: int, **fields: Any) -> Dict[str, Any]:
    """One action: the id every action has, and the dates they share."""
    return {
        "id": f"00000000-0000-4000-8000-{number:012d}",
        "process_date": "2024-03-04",
        **fields,
    }


_ACTIONS: Dict[str, List[Dict[str, Any]]] = {
    "forward_splits": [
        _action(
            1,
            symbol="AAA",
            cusip="000000001",
            new_rate=2,
            old_rate=1,
            ex_date="2024-03-05",
            record_date="2024-03-04",
            payable_date="2024-03-06",
            due_bill_redemption_date="2024-03-07",
        )
    ],
    "reverse_splits": [
        _action(
            2,
            symbol="BBB",
            old_cusip="000000002",
            new_cusip="000000102",
            new_rate=1,
            old_rate=10,
            ex_date="2024-03-05",
            record_date="2024-03-04",
            payable_date="2024-03-06",
        )
    ],
    "unit_splits": [
        _action(
            3,
            old_symbol="CCC",
            old_cusip="000000003",
            old_rate=1,
            new_symbol="CCD",
            new_cusip="000000103",
            new_rate=2,
            alternate_symbol="CCE",
            alternate_cusip="000000203",
            alternate_rate=3,
            effective_date="2024-03-05",
            payable_date="2024-03-06",
        )
    ],
    "stock_dividends": [
        _action(
            4,
            symbol="DDD",
            cusip="000000004",
            rate=0.05,
            ex_date="2024-03-05",
            record_date="2024-03-04",
            payable_date="2024-03-06",
        )
    ],
    "cash_dividends": [
        _action(
            5,
            symbol="EEE",
            cusip="000000005",
            rate=0.25,
            special=False,
            foreign=True,
            ex_date="2024-03-05",
            record_date="2024-03-04",
            payable_date="2024-03-06",
            due_bill_on_date="2024-03-05",
            due_bill_off_date="2024-03-06",
        )
    ],
    "spin_offs": [
        _action(
            6,
            source_symbol="FFF",
            source_cusip="000000006",
            source_rate=1,
            new_symbol="FFG",
            new_cusip="000000106",
            new_rate=0.5,
            ex_date="2024-03-05",
            record_date="2024-03-04",
            payable_date="2024-03-06",
            due_bill_redemption_date="2024-03-07",
        )
    ],
    "cash_mergers": [
        _action(
            7,
            acquirer_symbol="GGG",
            acquirer_cusip="000000007",
            acquiree_symbol="GGH",
            acquiree_cusip="000000107",
            rate=12.5,
            effective_date="2024-03-05",
            payable_date="2024-03-06",
        )
    ],
    "stock_mergers": [
        _action(
            8,
            acquirer_symbol="HHH",
            acquirer_cusip="000000008",
            acquirer_rate=1,
            acquiree_symbol="HHI",
            acquiree_cusip="000000108",
            acquiree_rate=2,
            effective_date="2024-03-05",
            payable_date="2024-03-06",
        )
    ],
    "stock_and_cash_mergers": [
        _action(
            9,
            acquirer_symbol="III",
            acquirer_cusip="000000009",
            acquirer_rate=1,
            acquiree_symbol="IIJ",
            acquiree_cusip="000000109",
            acquiree_rate=2,
            cash_rate=3.5,
            effective_date="2024-03-05",
            payable_date="2024-03-06",
        )
    ],
    "redemptions": [
        _action(
            10,
            symbol="JJJ",
            cusip="000000010",
            rate=25,
            payable_date="2024-03-06",
        )
    ],
    "name_changes": [
        _action(
            11,
            old_symbol="KKK",
            old_cusip="000000011",
            new_symbol="KKL",
            new_cusip="000000111",
        )
    ],
    "worthless_removals": [_action(12, symbol="LLL", cusip="000000012")],
    "rights_distributions": [
        _action(
            13,
            source_symbol="MMM",
            source_cusip="000000013",
            new_symbol="MMR",
            new_cusip="000000113",
            rate=0.1,
            ex_date="2024-03-05",
            record_date="2024-03-04",
            payable_date="2024-03-06",
            expiration_date="2024-04-05",
        )
    ],
    # The types below have no hand-written model: they parse into generated ones.
    "partial_calls": [
        _action(
            14,
            symbol="NNN",
            cusip="000000014",
            isin="US0000000149",
            currency="USD",
            dividend_rate=0.02,
            price=100,
            lottery_date="2024-03-05",
            lottery_type="original",
            record_date="2024-03-04",
            payable_date="2024-03-06",
            results_publication_date="2024-03-07",
        )
    ],
    "reorganizations": [
        _action(
            15,
            symbol="OOO",
            cusip="000000015",
            isin="US0000000156",
            currency="USD",
            cash_rate=1.5,
            effective_date="2024-03-05",
            payable_date="2024-03-06",
            stock_movements=[
                {
                    "symbol": "OOP",
                    "cusip": "000000115",
                    "isin": "US0000001150",
                    "source_rate": 1,
                    "new_rate": 2,
                }
            ],
        )
    ],
    "capital_gains_distributions": [
        _action(
            16,
            symbol="PPP",
            cusip="000000016",
            isin="US0000000164",
            currency="USD",
            long_term_rate=0.4,
            short_term_rate=0.1,
            ex_date="2024-03-05",
            record_date="2024-03-04",
            payable_date="2024-03-06",
        )
    ],
}


# Recordings store JSON with sorted keys, so the types are sorted here too: the
# order the SDK sees is then the same when recording and when replaying.
STUBBED_ACTIONS = dict(sorted(_ACTIONS.items()))


@scenario(
    covers=["CorporateActionsClient.get_corporate_actions"],
    since=SINCE,
    stub_responses=[
        {
            "status": 200,
            "json": {"corporate_actions": STUBBED_ACTIONS, "next_page_token": None},
        }
    ],
)
def every_corporate_action_type(ctx: Context) -> Dict[str, Any]:
    actions = ctx.corporate_actions.get_corporate_actions(
        CorporateActionsRequest(
            symbols=["AAA"],
            types=[
                CorporateActionsType.PARTIAL_CALL,
                CorporateActionsType.REORGANIZATION,
                CorporateActionsType.CAPITAL_GAINS_DISTRIBUTION,
            ],
            start=date(2024, 3, 1),
            end=date(2024, 3, 31),
        )
    )

    assert isinstance(actions, CorporateActionsSet)
    assert set(actions.data) == set(STUBBED_ACTIONS)
    for action_type, stubbed in STUBBED_ACTIONS.items():
        assert len(actions.data[action_type]) == len(stubbed)
    return {"actions": actions, "df": actions.df}
