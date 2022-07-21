import itertools
import pprint
from typing import Any

import pandas as pd
from pandas import DataFrame

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

        # set multi-level index
        # level=0 - symbol
        # level=1 - timestamp
        df = pd.DataFrame(data_list).set_index(["symbol", "timestamp"])

        # drop null columns
        df.dropna(axis=1, how="all", inplace=True)

        return df


class BaseDataSet(BaseModel):
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

    def dict(self, **kwargs) -> dict:
        """
        Gives dictionary representation of data.

        Returns:
            dict: The data in dictionary form.
        """
        # converts each data (Bar, Quote, etc) in the symbol specific lists to its dictionary format
        return {
            symbol: list(map(lambda d: d.dict(), data_list))
            for symbol, data_list in self.data.items()
        }

    def __str__(self) -> str:
        return pprint.pformat(self.dict())
