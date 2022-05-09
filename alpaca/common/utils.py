import os
from typing import Tuple, Optional

Credentials = Tuple[str, str, str]


def validate_credentials(
    api_key: Optional[str] = None,
    secret_key: Optional[str] = None,
    oauth_token: Optional[str] = None,
) -> Credentials:
    """Gathers API credentials from parameters and environment variables, and validates them.

    Args:
        api_key (Optional[str]): The API key for authentication. Defaults to None.
        secret_key (Optional[str]): The secret key for authentication. Defaults to None.
        oauth_token (Optional[str]): The oauth token if authenticating via OAuth. Defaults to None.

    Returns:
        Credentials: The set of validated authentication keys

    """
    oauth_token = oauth_token or os.environ.get("APCA_API_OAUTH_TOKEN")

    api_key = api_key or os.environ.get("APCA_API_KEY_ID")
    secret_key = secret_key or os.environ.get("APCA_API_SECRET_KEY")

    if not oauth_token and not api_key:
        raise ValueError("You must supply a method of authentication")

    if oauth_token and (api_key or secret_key):
        raise ValueError(
            "Either an oauth_token or an api_key may be supplied, but not both"
        )

    if not oauth_token and not (api_key and secret_key):
        raise ValueError("A corresponding secret_key must be supplied with the api_key")

    return api_key, secret_key, oauth_token


def get_api_version(api_version: str) -> str:
    """Returns the API version

    Args:
        api_version:

    Returns:

    """
    api_version = api_version or os.environ.get("APCA_API_VERSION")
    if api_version is None:
        api_version = "v2"

    return api_version
