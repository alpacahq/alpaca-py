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


# (preset, amount) pairs where amount != 1 is actually a legal amount for
# that preset's unit, so the error hint can safely recommend
# TimeFrame(amount=<amount>, unit=TimeFrameUnit.<name>) as a working fix.
VALID_OTHER_AMOUNTS = [
    (TimeFrame.Minute, 30),
    (TimeFrame.Hour, 12),
    (TimeFrame.Month, 3),
]


@pytest.mark.parametrize(("preset", "amount"), VALID_OTHER_AMOUNTS)
def test_timeframe_rejects_nested_preset_with_valid_other_amount(preset, amount):
    """Regression test: the message must echo the caller's amount instead
    of always suggesting amount=1, and must not imply the preset (always
    amount=1) is a direct substitute for a different amount. The
    recommended TimeFrame(amount=<amount>, ...) call is itself valid here.
    """
    unit_name = preset.unit.name
    with pytest.raises(TypeError) as exc_info:
        TimeFrame(amount=amount, unit=preset)

    message = str(exc_info.value)
    assert f"TimeFrameUnit.{unit_name}" in message
    assert f"amount={amount}" in message
    assert f"TimeFrame.{unit_name} directly" not in message
    assert f"TimeFrame(amount={amount}, unit=TimeFrameUnit.{unit_name})" in message


# (preset, amount, expected_constraint) tuples where amount != 1 is NOT a
# legal amount for that preset's unit (Day/Week only allow amount=1;
# Minute/Hour/Month have their own ranges). The error hint must not
# recommend TimeFrame(amount=<amount>, unit=TimeFrameUnit.<name>) here,
# since that exact call would itself immediately raise a ValueError. It
# also must not silently suggest amount=1 as a "fix", since that would
# change the interval the caller actually asked for; it should instead
# state the unit's real constraint.
INVALID_OTHER_AMOUNTS = [
    (TimeFrame.Day, 3, "Day and Week units can only be used with amount 1"),
    (TimeFrame.Week, 2, "Day and Week units can only be used with amount 1"),
    (
        TimeFrame.Minute,
        60,
        "Second or Minute units can only be used with amounts between 1-59.",
    ),
    (TimeFrame.Hour, 24, "Hour units can only be used with amounts 1-23"),
    (
        TimeFrame.Month,
        4,
        "Month units can only be used with amount 1, 2, 3, 6 and 12",
    ),
]


@pytest.mark.parametrize(("preset", "amount", "constraint"), INVALID_OTHER_AMOUNTS)
def test_timeframe_rejects_nested_preset_with_invalid_other_amount(
    preset, amount, constraint
):
    """Regression test for the case where the caller's amount is not a
    legal amount for the nested unit at all (e.g. TimeFrame(3,
    TimeFrame.Day)). The hint must not present
    TimeFrame(amount=<amount>, unit=TimeFrameUnit.<name>) as the fix, since
    that replacement would itself raise ValueError, and it must not
    silently suggest amount=1 instead, since that changes the interval the
    caller asked for. It should instead state the unit's real constraint.
    """
    unit_name = preset.unit.name
    with pytest.raises(TypeError) as exc_info:
        TimeFrame(amount=amount, unit=preset)

    message = str(exc_info.value)
    assert f"TimeFrameUnit.{unit_name}" in message
    assert f"amount={amount}" in message
    assert f"TimeFrame(amount={amount}, unit=TimeFrameUnit.{unit_name})" not in message
    # Must not silently propose a different interval than the caller asked
    # for (e.g. "use TimeFrame(amount=1, ...)" for a 3-day request).
    assert "TimeFrame(amount=1" not in message
    assert constraint in message


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
