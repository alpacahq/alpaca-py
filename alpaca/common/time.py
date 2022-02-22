
from enum import Enum

from pydantic import BaseModel


class TimeFrameUnit(Enum):
    Minute : str = "Min"
    Hour : str = "Hour"
    Day : str = "Day"

class TimeFrame(BaseModel):

    amount : int 
    unit : TimeFrameUnit

    # def __init__(self, amount: int, unit: TimeFrameUnit):
    #     super().__init__(amount, unit)
# TimeFrame.Minute = TimeFrame(1, TimeFrameUnit.Minute)
# TimeFrame.Hour = TimeFrame(1, TimeFrameUnit.Hour)
# TimeFrame.Day = TimeFrame(1, TimeFrameUnit.Day)
