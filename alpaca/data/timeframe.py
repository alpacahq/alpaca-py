from enum import Enum


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

    Attributes:
        amount_value (int): The number of multiples of the TimeFrameUnit interval
        unit_value (TimeFrameUnit): The base unit of time interval that is used to measure the TimeFrame

    Raises:
        ValueError: Raised if the amount_value and unit_value are not consistent with each other
    """

    amount_value: int
    unit_value: TimeFrameUnit

    def __init__(self, amount, unit) -> None:
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
    def validate_timeframe(amount: int, unit: TimeFrameUnit):
        """Validates the amount value against the TimeFrameUnit value for consistency

        Args:
            amount (int): The number of multiples of unit
            unit (TimeFrameUnit): The base unit of time interval the TimeFrame is measured by

        Raises:
            ValueError: Raised if the values of amount and unit are not consistent with each other
        """
        if amount <= 0:
            raise ValueError("Amount must be a positive integer value.")

        if unit == TimeFrameUnit.Minute and amount > 59:
            raise ValueError(
                "Second or Minute units can only be "
                + "used with amounts between 1-59."
            )

        if unit == TimeFrameUnit.Hour and amount > 23:
            raise ValueError("Hour units can only be used with amounts 1-23")

        if unit in (TimeFrameUnit.Day, TimeFrameUnit.Week) and amount != 1:
            raise ValueError("Day and Week units can only be used with amount 1")

        if unit == TimeFrameUnit.Month and amount not in (1, 2, 3, 6, 12):
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
