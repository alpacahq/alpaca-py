import random
from typing import Union, Optional
from uuid import UUID
from datetime import datetime


def reconnect_delay(
    retries: int,
    min_backoff: float,
    max_backoff: float,
) -> float:
    """Computes the delay before the next websocket reconnection attempt.

    Uses exponential backoff with equal jitter so repeated failures (e.g. a
    stream that only allows a single connection and is being rejected while a
    stale connection is reaped) do not turn into a tight reconnect/HTTP 429 storm.

    Args:
        retries (int): The number of consecutive failed attempts (>= 1).
        min_backoff (float): The base delay in seconds for the first retry.
        max_backoff (float): The maximum delay in seconds to cap the backoff at.

    Returns:
        float: The number of seconds to wait before retrying, in the range
        [capped / 2, capped] where ``capped`` is the exponentially-grown,
        max-capped delay.
    """
    capped = min_backoff
    for _ in range(max(0, retries - 1)):
        if capped >= max_backoff / 2:
            capped = max_backoff
            break
        capped *= 2
    capped = min(max_backoff, capped)
    # equal jitter: wait between half and the full computed delay
    return capped / 2 + random.uniform(0, capped / 2)


def validate_uuid_id_param(
    id: Union[UUID, str],
    var_name: Optional[str] = None,
) -> UUID:
    """
    A small helper function to eliminate duplicate checks of various id parameters to ensure they are
    valid UUIDs. Upcasts str instances that are valid UUIDs into UUID instances.

    Args:
        id (Union[UUID, str]): The parameter to be validated
        var_name (Optional[str]): the name of the parameter you'd like to generate in the error message. Defaults to
          using `account_id` due to it being the most commonly needed case

    Returns:
        UUID: The valid UUID instance
    """

    if var_name is None:
        var_name = "account_id"

    # should raise ValueError
    if type(id) == str:
        id = UUID(id)
    elif type(id) != UUID:
        raise ValueError(f"{var_name} must be a UUID or a UUID str")

    return id


def validate_symbol_or_asset_id(
    symbol_or_asset_id: Union[UUID, str],
) -> Union[UUID, str]:
    """
    A helper function to eliminate duplicate checks of symbols or asset ids.

    If the argument given is a string, assumed to be a symbol name. If a UUID object, assumed to be an asset id.
    ValueError if neither type.

    Args:
        symbol_or_asset_id: String representing a symbol name or a UUID representing an asset id.

    Returns:
        String if symbol, UUID if asset id.
    """
    if isinstance(symbol_or_asset_id, (UUID, str)):
        return symbol_or_asset_id
    raise ValueError(
        "symbol_or_asset_id must be a UUID of an asset id or a string of a symbol."
    )


def validate_symbol_or_contract_id(
    symbol_or_contract_id: Union[UUID, str],
) -> Union[UUID, str]:
    """
    A helper function to eliminate duplicate checks of symbols or contract id.

    If the argument given is a string, assumed to be a symbol name. If a UUID object, assumed to be a contract id.
    ValueError if neither type.

    Args:
        symbol_or_contract_id: String representing a symbol name or a UUID representing a contract id.

    Returns:
        String if symbol, UUID if contract id.
    """
    if isinstance(symbol_or_contract_id, (UUID, str)):
        return symbol_or_contract_id
    raise ValueError(
        "symbol_or_contract_id must be a UUID of a contract id or a string of a symbol."
    )


def tz_aware(dt: datetime) -> bool:
    """
    Returns if a given datetime is timezone aware

    Args:
        dt: the datetime to bo checked

    Returns: timezone awareness

    """
    return dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None
