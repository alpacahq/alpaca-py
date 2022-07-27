from collections import defaultdict
from typing import Type, Dict

from alpaca.common import HTTPResult, RawData


def parse_obj_as_symbol_dict(model: Type, raw_data: Dict) -> Dict[str, Type]:
    return {k: model(symbol=k, raw_data=v) for k, v in raw_data.items()}


def parse_latest_data_response(response: HTTPResult, data_by_symbol: dict):
    response_data = get_data_from_response(response)

    for symbol, data in response_data.items():
        data_by_symbol[symbol] = data

    return data_by_symbol


def get_data_from_response(response: HTTPResult) -> RawData:
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


def parse_dataset_response(response: HTTPResult, data_by_symbol: defaultdict) -> RawData:
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
        data_by_symbol[symbol].extend(data)
        if isinstance(data, list)
        else data_by_symbol[symbol].append(data)
        for symbol, data in response_data.items()
    ]

    return data_by_symbol


def parse_snapshot_data(response: HTTPResult, data_by_symbol: dict):
    # TODO: Improve snapshot parsing
    if "symbol" in response:
        symbol = response["symbol"]
        del response["symbol"]
        data_by_symbol[symbol] = response
    else:
        for symbol, data in response.items():
            data_by_symbol[symbol] = data

    return data_by_symbol
