from collections import defaultdict
from typing import Type, Dict

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


def get_data_from_response(response: HTTPResult) -> RawData:
    """
    From the raw API response, retrieves the field that contains market data.

    Args:
        response (HTTPResult): The raw API response

    Returns:
        RawData: The market data from the response
    """
    data_keys = {
        "trade",
        "trades",
        "quote",
        "quotes",
        "bar",
        "bars",
        "snapshot",
        "snapshots",
        "orderbook",
        "orderbooks",
    }

    selected_key = data_keys.intersection(response)

    if selected_key is None or len(selected_key) < 1:
        raise ValueError("The data in response does not match any known keys.")

    # assume selected_key only contains 1 value
    selected_key = selected_key.pop()

    # formatting a single symbol response so that this method
    # always returns a symbol keyed data dictionary
    if "symbol" in response:
        return {response["symbol"]: response[selected_key]}

    return response[selected_key]


def format_dataset_response(
    response: HTTPResult, data_by_symbol: defaultdict
) -> defaultdict:
    """
    Formats data from BarSet, TradeSet endpoints. Uses defaultdict for simpler syntax when
    doing list comprehension.

    Args:
        response (HTTPResult): The raw response from bars, trades, quotes, endpoint
        data_by_symbol (defaultdict):  The dictionary we want to format the raw response into

    Returns:
        defaultdict: The dictionary populated with data
    """
    # data_by_symbol is in format of
    #    {
    #       "symbol1": [ "data1", "data2", ... ],
    #       "symbol2": [ "data1", "data2", ... ],
    #                ....
    #    }

    response_data = get_data_from_response(response)

    # add elements to data_by_symbol
    # for list data types just extend
    # for non-list types, add as element of a list.
    # list comprehension used for speed
    [
        (
            data_by_symbol[symbol].extend(data)
            if isinstance(data, list)
            else data_by_symbol[symbol].append(data)
        )
        for symbol, data in response_data.items()
    ]

    return data_by_symbol


def format_latest_data_response(
    response: HTTPResult, data_by_symbol: defaultdict
) -> defaultdict:
    """
    Parses data from the "latest" endpoints and populates the data_by_symbol dict. (latest_quote, latest_bar). Also includes crypto/snapshots endpoint,
    but not stocks/snapshots.

    Args:
        response (HTTPResult): The response from the latest data endpoint.
        data_by_symbol (defaultdict): The dictionary we want to format the raw response into

    Returns:
        defaultdict: The dictionary populated with latest data points
    """
    response_data = get_data_from_response(response)

    for symbol, data in response_data.items():
        data_by_symbol[symbol] = data

    return data_by_symbol


def format_snapshot_data(
    response: HTTPResult, data_by_symbol: defaultdict
) -> defaultdict:
    """
    Formats data from stocks/snapshot endpoint. Exists because v2/stocks/snapshot
    is different from v1beta2/crypto/snapshot.

    Args:
        response (HTTPResult): The raw response from v2/stocks/snapshot endpoint
        data_by_symbol (defaultdict):  The dictionary we want to format the raw response into

    Returns:
        defaultdict: The dictionary populated with data
    """
    # TODO: Improve snapshot parsing.
    if "symbol" in response:
        symbol = response["symbol"]
        del response["symbol"]
        data_by_symbol[symbol] = response
    else:
        if "snapshots" in response:
            response = response["snapshots"]
        for symbol, data in response.items():
            data_by_symbol[symbol] = data

    return data_by_symbol
