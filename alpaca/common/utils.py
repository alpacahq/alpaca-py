from typing import Union, Optional
from uuid import UUID


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
        f"symbol_or_asset_id must be a UUID of an asset id or a string of a symbol."
    )
