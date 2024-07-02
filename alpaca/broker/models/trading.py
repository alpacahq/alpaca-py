from typing import Optional
from alpaca.trading.models import Order as BaseOrder
from alpaca.broker.enums import CommissionType


class Order(BaseOrder):
    """
    See base alpaca.trading.models.Order model for full list of base attributes.

    Attributes:
        commission (float): The dollar value commission you want to charge the end user.
        commission_type (Optional[CommissionType]): An enum to select how to interpret the value provided in the commission field: notional, bps, qty.
    """

    commission: Optional[float] = None
    commission_type: Optional[CommissionType] = None
