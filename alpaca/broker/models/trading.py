from alpaca.trading.models import Order as BaseOrder


class Order(BaseOrder):
    """
    See base alpaca.trading.models.Order model for full list of base attributes.

    Attributes:
        commission (float): The dollar value commission you want to charge the end user.
    """

    commission: float
