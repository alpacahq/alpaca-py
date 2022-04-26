from datetime import date
from typing import Any, Optional
from uuid import UUID

from ..enums import TradeDocumentSubType, TradeDocumentType
from ...common.models import ValidateBaseModel as BaseModel


class TradeDocument(BaseModel):
    """
    Similar to the AccountDocument model but this represents documents having to do with a TradeAccount not a regular
    Account.

    IE:  Account Monthly Statements or Trade Confirmations.

    Attributes:
        id (UUID): Unique id of the TradeDocument
        name (str): Name of the document
        type (TradeDocumentType): The kind of TradeDocument this is
        sub_type (TradeDocumentSubType): The sub type of the document
        date (date): Date on when this TradeDocument was generated
    """

    id: UUID
    name: str
    type: TradeDocumentType
    sub_type: TradeDocumentSubType
    date: date

    def __init__(self, **data: Any) -> None:
        if "id" in data and isinstance(data["id"], str):
            data["id"] = UUID(data["id"])

        super().__init__(**data)
