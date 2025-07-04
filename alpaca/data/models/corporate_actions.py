from datetime import date
from typing import Dict, List, Optional, Union

from alpaca.common.models import ModelWithID as BaseModel
from alpaca.common.types import RawData
from alpaca.data.models.base import BaseDataSet, TimeSeriesMixin


class ForwardSplit(BaseModel):
    corporate_action_type: str
    symbol: str
    cusip: str
    new_rate: float
    old_rate: float
    process_date: date
    ex_date: date
    record_date: Optional[date] = None
    payable_date: Optional[date] = None
    due_bill_redemption_date: Optional[date] = None


class ReverseSplit(BaseModel):
    corporate_action_type: str
    symbol: str
    old_cusip: str
    new_cusip: str
    new_rate: float
    old_rate: float
    process_date: date
    ex_date: date
    record_date: Optional[date] = None
    payable_date: Optional[date] = None


class UnitSplit(BaseModel):
    corporate_action_type: str
    old_symbol: str
    old_cusip: str
    old_rate: float
    new_symbol: str
    new_cusip: str
    new_rate: float
    alternate_symbol: str
    alternate_cusip: str
    alternate_rate: float
    process_date: date
    effective_date: date
    payable_date: Optional[date] = None


class StockDividend(BaseModel):
    corporate_action_type: str
    symbol: str
    cusip: str
    rate: float
    process_date: date
    ex_date: date
    record_date: Optional[date] = None
    payable_date: Optional[date] = None


class CashDividend(BaseModel):
    corporate_action_type: str
    symbol: str
    cusip: str
    rate: float
    special: bool
    foreign: bool
    process_date: date
    ex_date: date
    record_date: Optional[date] = None
    payable_date: Optional[date] = None
    due_bill_on_date: Optional[date] = None
    due_bill_off_date: Optional[date] = None


class SpinOff(BaseModel):
    corporate_action_type: str
    source_symbol: str
    source_cusip: str
    source_rate: float
    new_symbol: str
    new_cusip: str
    new_rate: float
    process_date: date
    ex_date: date
    record_date: Optional[date] = None
    payable_date: Optional[date] = None
    due_bill_redemption_date: Optional[date] = None


class CashMerger(BaseModel):
    corporate_action_type: str
    acquirer_symbol: Optional[str] = None
    acquirer_cusip: Optional[str] = None
    acquiree_symbol: str
    acquiree_cusip: str
    rate: float
    process_date: date
    effective_date: date
    payable_date: Optional[date] = None


class StockMerger(BaseModel):
    corporate_action_type: str
    acquirer_symbol: str
    acquirer_cusip: str
    acquirer_rate: float
    acquiree_symbol: str
    acquiree_cusip: str
    acquiree_rate: float
    process_date: date
    effective_date: date
    payable_date: Optional[date] = None


class StockAndCashMerger(BaseModel):
    corporate_action_type: str
    acquirer_symbol: str
    acquirer_cusip: str
    acquirer_rate: float
    acquiree_symbol: str
    acquiree_cusip: str
    acquiree_rate: float
    cash_rate: float
    process_date: date
    effective_date: date
    payable_date: Optional[date] = None


class Redemption(BaseModel):
    corporate_action_type: str
    symbol: str
    cusip: str
    rate: float
    process_date: date
    payable_date: Optional[date] = None


class NameChange(BaseModel):
    corporate_action_type: str
    old_symbol: str
    old_cusip: str
    new_symbol: str
    new_cusip: str
    process_date: date


class WorthlessRemoval(BaseModel):
    corporate_action_type: str
    symbol: str
    cusip: str
    process_date: date


class RightsDistribution(BaseModel):
    corporate_action_type: str
    source_symbol: str
    source_cusip: str
    new_symbol: str
    new_cusip: str
    rate: float
    process_date: date
    ex_date: date
    payable_date: date = None
    record_date: Optional[date] = None
    expiration_date: Optional[date] = None


CorporateAction = Union[
    ForwardSplit,
    ReverseSplit,
    UnitSplit,
    StockDividend,
    CashDividend,
    SpinOff,
    CashMerger,
    StockMerger,
    StockAndCashMerger,
    Redemption,
    NameChange,
    WorthlessRemoval,
    RightsDistribution,
]


class CorporateActionsSet(BaseDataSet, TimeSeriesMixin):
    """
    A collection of Corporate actions.
    ref. https://docs.alpaca.markets/reference/corporateactions-1

    Attributes:
        data (Dict[str, List[CorporateAction]]): The collection of corporate actions.
    """

    data: Dict[
        str,
        List[CorporateAction],
    ] = {}

    def __init__(self, raw_data: RawData) -> None:
        """
        Instantiates a CorporateActionsSet - a collection of CorporateAction.

        Args:
            raw_data (RawData): The raw corporate_actions data received from API
        """
        parsed_corporate_actions: Dict[
            str,
            List[CorporateAction],
        ] = {}

        if raw_data is None:
            return super().__init__()

        for corporate_action_type, corporate_actions in raw_data.items():
            if corporate_action_type == "forward_splits":
                parsed_corporate_actions[corporate_action_type] = [
                    ForwardSplit(
                        corporate_action_type=corporate_action_type, **corporate_action
                    )
                    for corporate_action in corporate_actions
                ]
            elif corporate_action_type == "reverse_splits":
                parsed_corporate_actions[corporate_action_type] = [
                    ReverseSplit(
                        corporate_action_type=corporate_action_type, **corporate_action
                    )
                    for corporate_action in corporate_actions
                ]
            elif corporate_action_type == "unit_splits":
                parsed_corporate_actions[corporate_action_type] = [
                    UnitSplit(
                        corporate_action_type=corporate_action_type, **corporate_action
                    )
                    for corporate_action in corporate_actions
                ]
            elif corporate_action_type == "stock_dividends":
                parsed_corporate_actions[corporate_action_type] = [
                    StockDividend(
                        corporate_action_type=corporate_action_type, **corporate_action
                    )
                    for corporate_action in corporate_actions
                ]
            elif corporate_action_type == "cash_dividends":
                parsed_corporate_actions[corporate_action_type] = [
                    CashDividend(
                        corporate_action_type=corporate_action_type, **corporate_action
                    )
                    for corporate_action in corporate_actions
                ]
            elif corporate_action_type == "spin_offs":
                parsed_corporate_actions[corporate_action_type] = [
                    SpinOff(
                        corporate_action_type=corporate_action_type, **corporate_action
                    )
                    for corporate_action in corporate_actions
                ]
            elif corporate_action_type == "cash_mergers":
                parsed_corporate_actions[corporate_action_type] = [
                    CashMerger(
                        corporate_action_type=corporate_action_type, **corporate_action
                    )
                    for corporate_action in corporate_actions
                ]
            elif corporate_action_type == "stock_mergers":
                parsed_corporate_actions[corporate_action_type] = [
                    StockMerger(
                        corporate_action_type=corporate_action_type, **corporate_action
                    )
                    for corporate_action in corporate_actions
                ]
            elif corporate_action_type == "stock_and_cash_mergers":
                parsed_corporate_actions[corporate_action_type] = [
                    StockAndCashMerger(
                        corporate_action_type=corporate_action_type, **corporate_action
                    )
                    for corporate_action in corporate_actions
                ]
            elif corporate_action_type == "redemptions":
                parsed_corporate_actions[corporate_action_type] = [
                    Redemption(
                        corporate_action_type=corporate_action_type, **corporate_action
                    )
                    for corporate_action in corporate_actions
                ]
            elif corporate_action_type == "name_changes":
                parsed_corporate_actions[corporate_action_type] = [
                    NameChange(
                        corporate_action_type=corporate_action_type, **corporate_action
                    )
                    for corporate_action in corporate_actions
                ]
            elif corporate_action_type == "worthless_removals":
                parsed_corporate_actions[corporate_action_type] = [
                    WorthlessRemoval(
                        corporate_action_type=corporate_action_type, **corporate_action
                    )
                    for corporate_action in corporate_actions
                ]
            elif corporate_action_type == "rights_distributions":
                parsed_corporate_actions[corporate_action_type] = [
                    RightsDistribution(
                        corporate_action_type=corporate_action_type, **corporate_action
                    )
                    for corporate_action in corporate_actions
                ]

        super().__init__(data=parsed_corporate_actions)
