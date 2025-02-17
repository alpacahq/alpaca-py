from typing import Union, Optional
from uuid import UUID
from datetime import datetime


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
    symbol_or_asset_id: Union[UUID, str]
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
    symbol_or_contract_id: Union[UUID, str]
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


def iso_to_unix(iso_str):
    """
    Convert an ISO 8601 formatted timestamp to a Unix timestamp in milliseconds.

    Args:
        iso_str (str): The ISO 8601 timestamp string to be converted. It can be in one of the following formats:
                       - "YYYY-MM-DDTHH:MM:SSZ" (UTC)
                       - "YYYY-MM-DDTHH:MM:SS+/-hh:mm" (with a timezone offset)
                       - "YYYY-MM-DDTHH:MM:SS" (UTC, assumed)

    Returns:
        int: The corresponding Unix timestamp in milliseconds.

    Raises:
        ValueError: If the input string is not in a valid ISO 8601 format.
    """
    try:
        # Handle 'Z' by replacing it with '+00:00' for UTC (ISO 8601 format)
        if iso_str.endswith("Z"):
            iso_str = iso_str.replace("Z", "+00:00")

        # Parse the datetime string to a datetime object, handling any offset
        dt = datetime.fromisoformat(iso_str)

        # Return Unix timestamp in milliseconds
        return int(dt.timestamp() * 1000)

    except ValueError as e:
        # If parsing fails, raise a clear error message
        raise ValueError(f"Invalid timestamp format: {iso_str}") from e
