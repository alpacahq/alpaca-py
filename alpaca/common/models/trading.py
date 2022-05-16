from uuid import UUID
from ..enums import AssetClass, AssetStatus, AssetExchange
from .models import ValidateBaseModel as BaseModel
from pydantic import Field
from typing import Optional


class Asset(BaseModel):
    """
    Represents a security. Some Assets are not tradable with Alpaca. These Assets are
    marked with the flag `tradable=false`.

    For more info, visit https://alpaca.markets/docs/api-references/trading-api/assets/
    """

    id: UUID
    asset_class: AssetClass = Field(
        alias="class"
    )  # using a pydantic alias to allow parsing data with the `class` keyword field
    exchange: AssetExchange
    symbol: str
    name: Optional[str] = None
    status: AssetStatus
    tradable: bool
    marginable: bool
    shortable: bool
    easy_to_borrow: bool
    fractionable: bool
