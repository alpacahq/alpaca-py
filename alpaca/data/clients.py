from datetime import datetime
from typing import Optional

from ..common.enums import BaseURL
from ..common.rest import RESTClient
from ..common.time import TimeFrame
from .models import BarSet

class HistoricalDataClient(RESTClient):

    def __init__(self, 
                api_key: Optional[str] = None, 
                secret_key: Optional[str] = None, 
                api_version: str = 'v2',
                raw_data: bool = False,
                ) -> None:
        """_summary_
        Args:
        api_key (Optional[str], optional): _description_. Defaults to None.
        secret_key (Optional[str], optional): _description_. Defaults to None.
        api_version (str, optional): _description_. Defaults to 'v1'.
        raw_data (bool, optional): _description_. Defaults to False.
        """
        super().__init__(api_key=api_key, 
                        secret_key=secret_key, 
                        api_version=api_version, 
                        base_url=BaseURL.DATA, 
                        sandbox=False, 
                        raw_data=raw_data)

    def get_bars(self,
                symbol: str, 
                timeframe: TimeFrame,
                start: datetime,
                end: Optional[datetime] = None,
                limit: Optional[int] = None):

        timeframe_value = timeframe.value
        
        bars = self._data_get(endpoint=f'bars', symbol_or_symbols=symbol, timeframe=timeframe_value, start=start, end=end, limit=limit)

        return self.response_wrapper(BarSet, symbol=symbol, timeframe=timeframe, bars=list(bars))