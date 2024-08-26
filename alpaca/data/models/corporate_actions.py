from datetime import date
from typing import Dict, List, Optional

from alpaca.common.models import ValidateBaseModel as BaseModel
from alpaca.common.types import RawData
from alpaca.data.models.base import BaseDataSet, TimeSeriesMixin


class CorporateAction(BaseModel):
    """
    A reverse split corporate action.

    Attributes:
        corporate_action_type (Optional[str]): The type of corporate action.
        symbol (Optional[str]): The ticker identifier for the security whose data forms the corporate action.
        old_symbol (Optional[str]): The old symbol of the security before the corporate action.
        new_symbol (Optional[str]): The new symbol of the security after the corporate action.
        alternate_symbol (Optional[str]): The alternate symbol
        new_rate (Optional[float]): The new rate of the security after the corporate action.
        old_rate (Optional[float]): The old rate of the security before the corporate action.
        alternate_rate (Optional[float]): The alternate rate
        process_date (Optional[date]): The date when the corporate action is processed by Alpaca.
        ex_date (Optional[date]): The ex-date marks the cutoff point for shareholders to be credited.
        effective_date (Optional[date]): The ex-date marks the cutoff point for shareholders to be credited.
        record_date (Optional[date]): The record date
        payable_date (Optional[date]): The payable date
        due_bill_redemption_date (Optional[date]): The due bill redemption date
        special (Optional[bool]): A flag indicating special.
        foreign (Optional[bool]): A flag indicating foreign.
        due_bill_on_date (Optional[date]): The due bill on date
        due_bill_off_date (Optional[date]): The due bill off date
        source_symbol (Optional[str]): The source symbol
        source_rate (Optional[str]): The source rate
        acquirer_symbol (Optional[str]): The acquirer symbol
        acquiree_symbol (Optional[str]): The acquiree symbol
        acquirer_rate (Optional[float]): The acquirer rate
        acquiree_rate (Optional[float]): The acquiree rate
        cash_rate (Optional[float]): The cash rate
    """

    corporate_action_type: Optional[str] = None
    symbol: Optional[str] = None
    old_symbol: Optional[str] = None
    new_symbol: Optional[str] = None
    alternate_symbol: Optional[str] = None
    rate: Optional[float] = None
    new_rate: Optional[float] = None
    old_rate: Optional[float] = None
    alternate_rate: Optional[float] = None
    process_date: Optional[date] = None
    ex_date: Optional[date] = None
    effective_date: Optional[date] = None
    record_date: Optional[date] = None
    payable_date: Optional[date] = None
    due_bill_redemption_date: Optional[date] = None
    special: Optional[bool] = None
    foreign: Optional[bool] = None
    due_bill_on_date: Optional[date] = None
    due_bill_off_date: Optional[date] = None
    source_symbol: Optional[str] = None
    source_rate: Optional[float] = None
    acquirer_symbol: Optional[str] = None
    acquiree_symbol: Optional[str] = None
    acquirer_rate: Optional[float] = None
    acquiree_rate: Optional[float] = None
    cash_rate: Optional[float] = None


class CorporateActionsSet(BaseDataSet, TimeSeriesMixin):
    """
    A collection of Corporate actions.
    ref. https://docs.alpaca.markets/reference/corporateactions-1

    Attributes:
        data (Dict[str, List[CorporateAction]]): The collection of corporate actions.
    """

    data: Dict[str, List[CorporateAction]] = {}

    def __init__(self, raw_data: RawData) -> None:
        """
        Instantiates a CorporateActionsSet - a collection of CorporateAction.

        Args:
            raw_data (RawData): The raw corporate_actions data received from API
        """
        parsed_corporate_actions: Dict[str, List[CorporateAction]] = {}

        if raw_data is not None:
            for corporate_action_type, corporate_actions in raw_data.items():
                parsed_corporate_actions[corporate_action_type] = [
                    CorporateAction(
                        corporate_action_type=corporate_action_type, **corporate_action
                    )
                    for corporate_action in corporate_actions
                    if corporate_action is not None
                ]

        super().__init__(data=parsed_corporate_actions)
