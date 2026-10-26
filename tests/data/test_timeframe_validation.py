import pytest

from alpaca.data.timeframe import TimeFrame, TimeFrameUnit


@pytest.mark.parametrize("amount", [True, 1.5])
def test_timeframe_rejects_non_integer_amounts(amount):
    with pytest.raises(ValueError, match="positive integer"):
        TimeFrame(amount, TimeFrameUnit.Minute)


def test_timeframe_rejects_non_unit_value():
    with pytest.raises(TypeError, match="TimeFrameUnit"):
        TimeFrame(1, "Min")


def test_timeframe_rejects_nested_timeframe_preset_as_unit():
    with pytest.raises(TypeError, match="not a TimeFrame"):
        TimeFrame(amount=1, unit=TimeFrame.Hour)
