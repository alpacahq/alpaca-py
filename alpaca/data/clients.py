from datetime import datetime
from typing import Optional, Union, List

from ..common.constants import DATA_V2_MAX_LIMIT
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

    def _data_get(self,
                  endpoint: str,
                  symbol_or_symbols: Union[str, List[str]],
                  endpoint_base: str = 'stocks',
                  resp_grouped_by_symbol: Optional[bool] = None,
                  page_limit: int = DATA_V2_MAX_LIMIT,
                  **kwargs):
        page_token = None
        total_items = 0
        limit = kwargs.get('limit')
        if resp_grouped_by_symbol is None:
            resp_grouped_by_symbol = not isinstance(symbol_or_symbols, str)
        while True:
            actual_limit = None
            if limit:
                actual_limit = min(int(limit) - total_items, page_limit)
                if actual_limit < 1:
                    break
            data = kwargs
            data['limit'] = actual_limit
            data['page_token'] = page_token
            path = f'/{endpoint_base}'
            if isinstance(symbol_or_symbols, str) and symbol_or_symbols:
                path += f'/{symbol_or_symbols}'
            else:
                data['symbols'] = ','.join(symbol_or_symbols)
            if endpoint:
                path += f'/{endpoint}'
            resp = self.get(path, data=data)
            if not resp_grouped_by_symbol:
                k = endpoint or endpoint_base
                for item in resp.get(k, []) or []:
                    yield item
                    total_items += 1
            else:
                by_symbol = resp.get(endpoint, {}) or {}
                for sym, items in sorted(by_symbol.items()):
                    for item in items or []:
                        item['S'] = sym
                        yield item
                        total_items += 1
            page_token = resp.get('next_page_token')
            if not page_token:
                break