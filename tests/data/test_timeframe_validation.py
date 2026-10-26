import pytest

from alpaca.data.timeframe import TimeFrame, TimeFrameUnit


@pytest.mark.parametrize("amount", [True, 1.5])
def test_timeframe_rejects_non_integer_amounts(amount):
    with pytest.raises(ValueError, match="positive integer"):
        TimeFrame(amount, TimeFrameUnit.Minute)


def test_timeframe_rejects_non_unit_value():
    with pytest.raises(TypeError, match="TimeFrameUnit"):
        TimeFrame(1, "Min")


PRESETS = [
    TimeFrame.Minute,
    TimeFrame.Hour,
    TimeFrame.Day,
    TimeFrame.Week,
    TimeFrame.Month,
]


@pytest.mark.parametrize("preset", PRESETS)
def test_timeframe_rejects_nested_timeframe_preset_as_unit(preset):
    unit_name = preset.unit.name
    with pytest.raises(TypeError) as exc_info:
        TimeFrame(amount=1, unit=preset)

    message = str(exc_info.value)
    assert f"TimeFrame.{unit_name}" in message
    assert f"TimeFrameUnit.{unit_name}" in message
    assert "amount=1" in message


@pytest.mark.parametrize("preset", PRESETS)
def test_timeframe_rejects_nested_preset_with_other_amount(preset):
    """Regression test: the message must echo the caller's amount instead
    of always suggesting amount=1, and must not imply the preset (always
    amount=1) is a direct substitute for a different amount.
    """
    unit_name = preset.unit.name
    with pytest.raises(TypeError) as exc_info:
        TimeFrame(amount=3, unit=preset)

    message = str(exc_info.value)
    assert f"TimeFrameUnit.{unit_name}" in message
    assert "amount=3" in message
    assert f"TimeFrame.{unit_name} directly" not in message


def test_timeframe_rejects_constructed_timeframe_as_unit():
    nested = TimeFrame(amount=5, unit=TimeFrameUnit.Minute)
    with pytest.raises(TypeError, match=r"TimeFrameUnit\.Minute"):
        TimeFrame(amount=1, unit=nested)


def test_timeframe_rejects_timeframe_passed_as_amount():
    with pytest.raises(ValueError, match="positive integer"):
        TimeFrame(amount=TimeFrame.Hour, unit=TimeFrameUnit.Hour)


@pytest.mark.parametrize(
    ("preset", "expected"),
    [
        (TimeFrame.Minute, "1Min"),
        (TimeFrame.Hour, "1Hour"),
        (TimeFrame.Day, "1Day"),
        (TimeFrame.Week, "1Week"),
        (TimeFrame.Month, "1Month"),
    ],
)
def test_timeframe_presets_serialize_for_the_api(preset, expected):
    assert preset.value == expected
    assert str(preset) == expected
