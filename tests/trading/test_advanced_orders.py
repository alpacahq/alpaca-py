from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from alpaca.trading.enums import (
    AdvancedInstructionsAlgorithm,
    AdvancedInstructionsDestination,
)
from alpaca.trading.models import AdvancedInstructions
from alpaca.trading.requests import PatchOrderRequest


def test_advanced_instruction_enum_values() -> None:
    assert [member.value for member in AdvancedInstructionsAlgorithm] == [
        "DMA",
        "TWAP",
        "VWAP",
    ]
    assert [member.value for member in AdvancedInstructionsDestination] == [
        "NYSE",
        "NASDAQ",
        "ARCA",
    ]


@pytest.mark.parametrize(
    ("algorithm", "destination"),
    [
        (
            AdvancedInstructionsAlgorithm.DMA,
            AdvancedInstructionsDestination.NYSE,
        ),
        ("TWAP", "NASDAQ"),
    ],
)
def test_advanced_instructions_accepts_enum_and_raw_values(
    algorithm: AdvancedInstructionsAlgorithm | str,
    destination: AdvancedInstructionsDestination | str,
) -> None:
    instructions = AdvancedInstructions(
        algorithm=algorithm,
        destination=destination,
    )

    assert instructions.algorithm == algorithm
    assert instructions.destination == destination


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("algorithm", "POV"),
        ("destination", "IEX"),
    ],
)
def test_advanced_instructions_rejects_unsupported_values(
    field: str, value: str
) -> None:
    with pytest.raises(ValidationError):
        AdvancedInstructions(**{field: value})


def test_patch_order_request_serializes_advanced_instructions() -> None:
    start_time = datetime(2026, 7, 14, 13, 30, tzinfo=timezone.utc)
    end_time = datetime(2026, 7, 14, 14, 30, tzinfo=timezone.utc)
    request = PatchOrderRequest(
        qty="100",
        time_in_force="day",
        limit_price="225.50",
        client_order_id="replacement-order",
        advanced_instructions=AdvancedInstructions(
            algorithm=AdvancedInstructionsAlgorithm.VWAP,
            destination=AdvancedInstructionsDestination.ARCA,
            display_qty="100",
            start_time=start_time,
            end_time=end_time,
            max_percentage="0.125",
        ),
    )

    assert request.to_request_fields() == {
        "qty": "100",
        "time_in_force": "day",
        "limit_price": "225.50",
        "client_order_id": "replacement-order",
        "advanced_instructions": {
            "algorithm": "VWAP",
            "destination": "ARCA",
            "display_qty": "100",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "max_percentage": "0.125",
        },
    }
