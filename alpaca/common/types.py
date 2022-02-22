from typing import Dict, List, Union

from ..common.time import TimeFrame

RawBar = Dict[str, str]
RawQuote = Dict[str, str]
RawTrade = Dict[str, str]

RawBarSet = List[RawBar]
RawQuoteSet = List[RawQuote]
RawTradeSet = List[RawTrade]

TimeFrameType = Union[TimeFrame, str]