from datetime import date
from typing import Dict, List, Optional, Union

import pandas as pd
from pandas import DataFrame

from alpaca.common._deprecation import (
    deprecate_compatibility_shape as _deprecate_compatibility_shape,
)
from alpaca.common.models import ModelWithID as BaseModel
from alpaca.common.types import RawData
from alpaca.data._generated.models import (
    CapitalGainsDistribution,
    PartialCall,
    Reorganization,
)
from alpaca.data.models.base import BaseDataSet, TimeSeriesMixin


@_deprecate_compatibility_shape
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


@_deprecate_compatibility_shape
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


@_deprecate_compatibility_shape
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


@_deprecate_compatibility_shape
class StockDividend(BaseModel):
    corporate_action_type: str
    symbol: str
    cusip: str
    rate: float
    process_date: date
    ex_date: date
    record_date: Optional[date] = None
    payable_date: Optional[date] = None


@_deprecate_compatibility_shape
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


@_deprecate_compatibility_shape
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


@_deprecate_compatibility_shape
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


@_deprecate_compatibility_shape
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


@_deprecate_compatibility_shape
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


@_deprecate_compatibility_shape
class Redemption(BaseModel):
    corporate_action_type: str
    symbol: str
    cusip: str
    rate: float
    process_date: date
    payable_date: Optional[date] = None


@_deprecate_compatibility_shape
class NameChange(BaseModel):
    corporate_action_type: str
    old_symbol: str
    old_cusip: str
    new_symbol: str
    new_cusip: str
    process_date: date


@_deprecate_compatibility_shape
class WorthlessRemoval(BaseModel):
    corporate_action_type: str
    symbol: str
    cusip: str
    process_date: date


@_deprecate_compatibility_shape
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
    PartialCall,
    Reorganization,
    CapitalGainsDistribution,
]

# Types with no hand-written model parse into the generated one. Generated models
# have no corporate_action_type field; the key they are listed under names the type.
_GENERATED_CORPORATE_ACTIONS = {
    "partial_calls": PartialCall,
    "reorganizations": Reorganization,
    "capital_gains_distributions": CapitalGainsDistribution,
}


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
            elif corporate_action_type in _GENERATED_CORPORATE_ACTIONS:
                model = _GENERATED_CORPORATE_ACTIONS[corporate_action_type]
                parsed_corporate_actions[corporate_action_type] = [
                    model.model_validate(corporate_action)
                    for corporate_action in corporate_actions
                ]

        super().__init__(data=parsed_corporate_actions)

    @property
    def df(self) -> DataFrame:
        """Returns a pandas dataframe of the corporate actions, indexed by type.

        The type comes from the key each action is listed under, so the generated
        models, which have no corporate_action_type field, are labelled too.

        Returns:
            DataFrame: corporate actions in a pandas dataframe
        """
        rows = [
            {"corporate_action_type": corporate_action_type, **corporate_action}
            for corporate_action_type, corporate_actions in self.dict().items()
            for corporate_action in corporate_actions
        ]
        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.set_index(["corporate_action_type"])
        df.dropna(axis=1, how="all", inplace=True)
        return df
