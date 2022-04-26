from datetime import date
from typing import Any, Optional
from uuid import UUID

from ...common.models import ValidateBaseModel as BaseModel


class TradeDocument(BaseModel):
    """
    Similar to the AccountDocument model but this represents documents having to do with a TradeAccount not a regular
    Account.

    IE:  Account Monthly Statements or Trade Confirmations.

    Attributes:

    """

    id: UUID
    name: str
    type: str
    sub_type: str
    date: date

    def __init__(self, **data: Any) -> None:
        if "id" in data and isinstance(data["id"], str):
            data["id"] = UUID(data["id"])

        super().__init__(**data)
