from collections import defaultdict
from typing import Dict, Type

from alpaca.common import HTTPResult, RawData

"""
These functions were created and put in this file to handle all of the edge cases
for parsing data that exist in the market data API.

v2/stocks and v1beta2/crypto
"""


def parse_obj_as_symbol_dict(model: Type, raw_data: RawData) -> Dict[str, Type]:
    """
    Parses raw_data into a dictionary where the keys are the string valued symbols and the values are the
    parsed data into the model.

    Args:
        model (Type): The model we want to parse the data into
        raw_data (RawData): The raw data from the API

    Returns:
        Dict[str, Type]: The symbol keyed dictionary of parsed data
    """
    if raw_data is None:
        return {}
    return {
        k: model(symbol=k, raw_data=v) for k, v in raw_data.items() if v is not None
    }
