import os
from typing import Tuple

Credentials = Tuple[str, str]


def get_credentials(key_id: str = None, secret_key: str = None) -> Credentials:

    key_id = key_id or os.environ.get("APCA_API_KEY_ID")
    if key_id is None:
        raise ValueError(
            "Key ID must be given to access Alpaca trade API", " (env: APCA_API_KEY_ID)"
        )

    secret_key = secret_key or os.environ.get("APCA_API_SECRET_KEY")
    if secret_key is None:
        raise ValueError(
            "Secret key must be given to access Alpaca trade API"
            " (env: APCA_API_SECRET_KEY"
        )

    return key_id, secret_key


def get_api_version(api_version: str) -> str:
    api_version = api_version or os.environ.get("APCA_API_VERSION")
    if api_version is None:
        api_version = "v2"

    return api_version
