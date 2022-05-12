from datetime import datetime
from .models import ValidateBaseModel as BaseModel


class Clock(BaseModel):
    """
    The market clock for US equity markets. Timestamps are in eastern time.

    Attributes:
        timestamp (datetime): The current timestamp.
        is_open (bool): Whether the market is currently open.
        next_open (datetime): The timestamp when the market will next open.
        next_close (datetime): The timestamp when the market will next close.
    """

    timestamp: datetime
    is_open: bool
    next_open: datetime
    next_close: datetime
