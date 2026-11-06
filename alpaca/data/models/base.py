import itertools
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from pandas import DataFrame
from pydantic import model_serializer

from alpaca.common.models import ValidateBaseModel as BaseModel


class TimeSeriesMixin:
    @property
    def df(self) -> DataFrame:
        """Returns a pandas dataframe containing the bar data.
        Requires mapping to be defined in child class.

        Returns:
            DataFrame: data in a pandas dataframe
        """
        # combine all lists of data into one list
        data_list = list(itertools.chain.from_iterable(self.dict().values()))

        df = pd.DataFrame(data_list)
        columns = df.columns

        # set multi-level index
        if "news" in self.dict():
            # level=0 - id
            df = df.set_index(["id"])
        elif "corporate_action_type" in columns:
            # level=0 - corporate_action_type
            df = df.set_index(["corporate_action_type"])
        elif set(["symbol", "timestamp"]).issubset(columns):
            # level=0 - symbol
            # level=1 - timestamp
            df = df.set_index(["symbol", "timestamp"])

        # drop null columns
        df.dropna(axis=1, how="all", inplace=True)

        return df


class BaseDataSet(BaseModel):
    """
    Base class to process data models for trades, bars quotes, and news.

    Attributes:
        data (Dict[str, List[BaseModel]]): The data keyed by symbol.
        next_page_token (Optional[str]): Only set on a single page of results, i.e. when the set was returned with
          ``handle_pagination=PaginationType.NONE`` or yielded by ``PaginationType.ITERATOR``. Pass it as the
          request's ``page_token`` to fetch the next page. ``None`` when there are no more pages.
    """

    data: Dict[str, List[BaseModel]] = {}
    next_page_token: Optional[str] = None

    @model_serializer(mode="wrap")
    def _serialize(self, handler: Any) -> Any:
        """Omit an unset page token so a merged set serializes as it did before the field existed.

        A token that was assigned, including an explicit ``None`` on the last page, is kept.
        """
        dumped = handler(self)
        if (
            isinstance(dumped, dict)
            and "next_page_token" not in self.model_fields_set
            and dumped.get("next_page_token") is None
        ):
            dumped.pop("next_page_token", None)
        return dumped

    def __getitem__(self, symbol: str) -> Any:
        """Gives dictionary-like access to multi-symbol data

        Args:
            symbol (str): The ticker identifier for the desired data

        Raises:
            KeyError: Symbol does not exist for data

        Returns:
            List[Bar]: The data for the given symbol
        """
        if symbol not in self.data:
            raise KeyError(f"No key {symbol} was found.")

        return self.data[symbol]

    def __contains__(self, key: str) -> bool:
        """Checks if key exists in the dataset.

        Args:
            key (str): The key to check for

        Returns:
            bool: True if key is in dataset, False otherwise
        """
        return key in self.data

    def dict(self, **kwargs) -> dict:
        """
        Gives dictionary representation of data.

        Returns:
            dict: The data in dictionary form.
        """
        # converts each data (Bar, Quote, etc) in the symbol specific lists to its dictionary format
        return {
            symbol: list(map(lambda d: d.model_dump(), data_list))
            for symbol, data_list in self.data.items()
        }
