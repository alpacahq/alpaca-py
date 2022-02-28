
from enum import Enum

from pydantic import BaseModel


class TimeFrameUnit(Enum):
    """Quantity of time used as unit
    """
    Minute : str = "Min"
    Hour : str = "Hour"
    Day : str = "Day"

class TimeFrame(BaseModel):

    amount_value: int
    unit_value : TimeFrameUnit

    @property
    def amount(self):
        return self.amount_value

    @amount.setter
    def amount(self, value: int):
        self.amount_value = value

    @property
    def unit(self) -> TimeFrameUnit:
        return self.unit_value

    @unit.setter
    def unit(self, value: TimeFrameUnit):
        self.unit_value = value

    @property
    def value(self):
        return f"{self.amount}{self.unit.value}"

    def __str__(self):
        return self.value

    

