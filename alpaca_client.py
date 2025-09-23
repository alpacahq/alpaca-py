from __future__ import annotations

import os

from alpaca.common.exceptions import APIError
from alpaca.trading.client import TradingClient


class AlpacaClient:
    """Thin wrapper around ``alpaca-py``'s :class:`TradingClient`."""

    def __init__(self, api_key: str, secret_key: str, paper: bool = True):
        self.client = TradingClient(
            api_key=api_key,
            secret_key=secret_key,
            paper=paper,
        )

    @classmethod
    def from_env(cls) -> "AlpacaClient":
        """Instantiate the client using standard Alpaca environment variables."""

        api_key = os.environ["APCA_API_KEY_ID"]
        secret_key = os.environ["APCA_API_SECRET_KEY"]
        base_url = os.environ.get("APCA_API_BASE_URL", "")
        paper = "paper" in base_url.lower()
        return cls(api_key=api_key, secret_key=secret_key, paper=paper)

    def get_account(self) -> dict:
        """Fetch account details using the official SDK."""

        try:
            account = self.client.get_account()
        except APIError as exc:
            raise APIError(
                f"Failed to fetch account: {exc.status_code} {exc.code} {exc.message}"
            ) from exc
        return account.model_dump()
