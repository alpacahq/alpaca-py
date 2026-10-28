from enum import Enum
from numbers import Integral


class classproperty(property):
    """Allows us to create decorator of stacked classmethod and property decorators

    Args:
        property (property): the property decorator class
    """

    def __get__(self, cls, owner):
        return classmethod(self.fget).__get__(None, owner)()


class TimeFrameUnit(str, Enum):
    """Quantity of time used as unit"""

    Minute: str = "Min"
    Hour: str = "Hour"
    Day: str = "Day"
    Week: str = "Week"
    Month: str = "Month"


class TimeFrame:
    """A time interval specified in multiples of defined units (minute, day, etc)

    Pass a ``TimeFrameUnit`` and a positive integer amount, or use a preset
    directly::

        TimeFrame(amount=5, unit=TimeFrameUnit.Minute)
        TimeFrame.Hour

    Presets such as ``TimeFrame.Hour`` are already ``TimeFrame`` instances.
    Pass the preset as the timeframe. Do not wrap one as ``unit``.

    Attributes:
        amount_value (int): The number of multiples of the TimeFrameUnit interval
        unit_value (TimeFrameUnit): The base unit of time interval that is used to measure the TimeFrame

    Raises:
        ValueError: Raised if the amount_value and unit_value are not consistent with each other
        TypeError: Raised if unit is not a TimeFrameUnit
    """

    amount_value: int
    unit_value: TimeFrameUnit

    def __init__(self, amount: int, unit: TimeFrameUnit) -> None:
        self.validate_timeframe(amount, unit)
        self.amount_value = amount
        self.unit_value = unit

    @property
    def amount(self) -> int:
        """Returns the amount_value field

        Returns:
            int: amount_value field
        """
        return self.amount_value

    @property
    def unit(self) -> TimeFrameUnit:
        """Returns the TimeFrameUnit field value of this TimeFrame object

        Returns:
            TimeFrameUnit: unit_value field
        """
        return self.unit_value

    @property
    def value(self) -> str:
        """Returns a string representation of this TimeFrame object for API consumption

        Returns:
            str: string representation of this timeframe
        """
        return f"{self.amount}{self.unit.value}"

    @staticmethod
    def _is_amount_valid_for_unit(amount: int, unit: TimeFrameUnit) -> bool:
        """Returns whether ``amount`` is a legal value for ``unit``.

        This is the single source of truth for the amount/unit constraints
        enforced below, so error-message hints (e.g. for a nested TimeFrame)
        can check whether a constructor call they are about to recommend
        would itself be legal, instead of duplicating these rules and
        risking drift.

        Args:
            amount (int): The number of multiples of unit
            unit (TimeFrameUnit): The base unit of time interval

        Returns:
            bool: True if amount is valid for unit
        """
        if unit == TimeFrameUnit.Minute:
            return amount <= 59
        if unit == TimeFrameUnit.Hour:
            return amount <= 23
        if unit in (TimeFrameUnit.Day, TimeFrameUnit.Week):
            return amount == 1
        if unit == TimeFrameUnit.Month:
            return amount in (1, 2, 3, 6, 12)
        return True

    @staticmethod
    def validate_timeframe(amount: int, unit: TimeFrameUnit):
        """Validates the amount value against the TimeFrameUnit value for consistency

        Args:
            amount (int): The number of multiples of unit
            unit (TimeFrameUnit): The base unit of time interval the TimeFrame is measured by

        Raises:
            ValueError: Raised if the values of amount and unit are not consistent with each other
            TypeError: Raised if unit is not a TimeFrameUnit. A nested TimeFrame
                names the TimeFrameUnit to use instead.
        """
        if isinstance(amount, bool) or not isinstance(amount, Integral) or amount <= 0:
            raise ValueError("Amount must be a positive integer value.")

        if isinstance(unit, TimeFrame):
            nested_unit = unit.unit
            nested_unit_name = nested_unit.name
            if amount == 1:
                hint = (
                    f"Pass a preset such as TimeFrame.{nested_unit_name} directly, "
                    f"or use TimeFrame(amount=1, unit=TimeFrameUnit.{nested_unit_name})."
                )
            elif TimeFrame._is_amount_valid_for_unit(amount, nested_unit):
                # Presets are always amount=1, so they can't stand in for the
                # caller's amount. Echo it in the constructor form instead;
                # amount is confirmed valid for this unit, so the suggested
                # call will not itself raise.
                hint = (
                    f"Presets like TimeFrame.{nested_unit_name} are always "
                    f"amount=1. Use TimeFrame(amount={amount}, "
                    f"unit=TimeFrameUnit.{nested_unit_name}) instead."
                )
            else:
                # amount is not valid for this unit at all (e.g. amount=3
                # with TimeFrameUnit.Day), so recommending
                # TimeFrame(amount={amount}, unit=TimeFrameUnit.{name})
                # would itself immediately raise. Don't present that as
                # the fix; point to the amount=1 preset instead.
                hint = (
                    f"Presets like TimeFrame.{nested_unit_name} are always "
                    f"amount=1, and amount={amount} is not valid for "
                    f"TimeFrameUnit.{nested_unit_name}. Pass a preset such "
                    f"as TimeFrame.{nested_unit_name} directly, or use "
                    f"TimeFrame(amount=1, unit=TimeFrameUnit.{nested_unit_name})."
                )

            raise TypeError(
                f"Unit must be a TimeFrameUnit value, not a TimeFrame. {hint}"
            )

        if not isinstance(unit, TimeFrameUnit):
            raise TypeError("Unit must be a TimeFrameUnit value.")

        if unit == TimeFrameUnit.Minute and not TimeFrame._is_amount_valid_for_unit(
            amount, unit
        ):
            raise ValueError(
                "Second or Minute units can only be "
                + "used with amounts between 1-59."
            )

        if unit == TimeFrameUnit.Hour and not TimeFrame._is_amount_valid_for_unit(
            amount, unit
        ):
            raise ValueError("Hour units can only be used with amounts 1-23")

        if unit in (
            TimeFrameUnit.Day,
            TimeFrameUnit.Week,
        ) and not TimeFrame._is_amount_valid_for_unit(amount, unit):
            raise ValueError("Day and Week units can only be used with amount 1")

        if unit == TimeFrameUnit.Month and not TimeFrame._is_amount_valid_for_unit(
            amount, unit
        ):
            raise ValueError(
                "Month units can only be used with amount 1, 2, 3, 6 and 12"
            )

    def __str__(self):
        return self.value

    @classproperty
    def Minute(cls):
        """Helper method to quickly access a 1 minute timeframe

        Returns:
            TimeFrame: A 1-minute TimeFrame
        """
        return TimeFrame(amount=1, unit=TimeFrameUnit.Minute)

    @classproperty
    def Hour(cls):
        """Helper method to quickly access a 1 hour timeframe

        Returns:
            TimeFrame: A 1-hour TimeFrame
        """
        return TimeFrame(amount=1, unit=TimeFrameUnit.Hour)

    @classproperty
    def Day(cls):
        """Helper method to quickly access a  1 day timeframe

        Returns:
            TimeFrame: A 1-day TimeFrame
        """
        return TimeFrame(amount=1, unit=TimeFrameUnit.Day)

    @classproperty
    def Week(cls):
        """Helper method to quickly access a 1 week timeframe

        Returns:
            TimeFrame: A 1-week TimeFrame
        """
        return TimeFrame(amount=1, unit=TimeFrameUnit.Week)

    @classproperty
    def Month(cls):
        """Helper method to quickly access a 1 month timeframe

        Returns:
            TimeFrame: A 1-month TimeFrame
        """
        return TimeFrame(amount=1, unit=TimeFrameUnit.Month)
