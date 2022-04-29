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
        sub_type (Optional[TradeDocumentSubType]): The subtype of the document. The API returns "" in the case of this
          not being specified, however we transform this case into None for convenience.
        date (date): Date on when this TradeDocument was generated
    """

    id: UUID
    name: str
    type: TradeDocumentType
    sub_type: Optional[TradeDocumentSubType] = None
    date: date

    def __init__(self, **data: Any) -> None:
        if "id" in data and isinstance(data["id"], str):
            data["id"] = UUID(data["id"])

        if "sub_type" in data and data["sub_type"] == "":
            data["sub_type"] = None

        super().__init__(**data)
