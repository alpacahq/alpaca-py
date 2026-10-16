from typing import Optional

from alpaca.common.models import ValidateBaseModel as BaseModel
from alpaca.trading.models import Order as BaseOrder


class Order(BaseOrder):
    """
    See base alpaca.trading.models.Order model for full list of base attributes.

    Attributes:
        commission (float): The dollar value commission you want to charge the end user.
    """

    commission: Optional[float] = None


class OptionExerciseResponse(BaseModel):
    """
    Result of exercising an options position.

    ``POST /v1/trading/accounts/{account_id}/positions/{symbol_or_contract_id}/exercise``
    returns this body. Both quantities are decimal strings. Either may be omitted.

    Attributes:
        qty_exercised (Optional[str]): Total number of contracts exercised.
        qty_remaining (Optional[str]): Number of contracts left after the exercise.
    """

    qty_exercised: Optional[str] = None
    qty_remaining: Optional[str] = None
