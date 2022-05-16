from datetime import datetime, date
from typing import Any
from .models import ValidateBaseModel as BaseModel


class Calendar(BaseModel):
    """
    The market calendar for equity markets. Describes the market open and close time on a given day.
    """

    date: date
    open: datetime
    close: datetime

    def __init__(self, **data: Any) -> None:
        """
            Converts open and close time strings from %H:%M to a datetime
        Args:
            **data: The raw calendar data from API
        """
        if "date" in data and "open" in data:
            start_datetime_str = data["date"] + " " + data["open"]
            data["open"] = datetime.strptime(start_datetime_str, "%Y-%m-%d %H:%M")

        if "date" in data and "close" in data:
            start_datetime_str = data["date"] + " " + data["close"]
            data["close"] = datetime.strptime(start_datetime_str, "%Y-%m-%d %H:%M")

        super().__init__(**data)
