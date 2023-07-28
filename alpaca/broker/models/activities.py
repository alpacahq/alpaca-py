from uuid import UUID
from alpaca.trading.models import BaseActivity as TradingBaseActivity
from alpaca.trading.models import NonTradeActivity as BaseNonTradeActivity
from alpaca.trading.models import TradeActivity as BaseTradeActivity


class BaseActivity(TradingBaseActivity):
    """
    Base model for activities that are retrieved through the Broker API.

    Attributes:
        id (str): Unique ID of this Activity. Note that IDs for Activity instances are formatted like
          `20220203000000000::045b3b8d-c566-4bef-b741-2bf598dd6ae7` the first part before the `::` is a date string
          while the part after is a UUID
        account_id (UUID): id of the Account this activity relates too
        activity_type (ActivityType): What specific kind of Activity this was
    """

    account_id: UUID

    def __init__(self, *args, **data):
        if "account_id" in data and type(data["account_id"]) == str:
            data["account_id"] = UUID(data["account_id"])

        super().__init__(*args, **data)


class NonTradeActivity(BaseNonTradeActivity, BaseActivity):
    """NonTradeActivity for the Broker API."""


class TradeActivity(BaseTradeActivity, BaseActivity):
    """TradeActivity for the Broker API."""
