from datetime import date
from typing import Any, List, Optional
from uuid import UUID

from pydantic import root_validator

from .models import ValidateBaseModel as BaseModel


class NonEmptyRequest(BaseModel):
    """
    Mixin for models that represent requests where we don't want to send nulls for optional fields.
    """

    def to_request_fields(self) -> dict:
        """
        the equivalent of self::dict but removes empty values and handles converting non json serializable types.

        Ie say we only set trusted_contact.given_name instead of generating a dict like:
          {contact: {city: None, country: None...}, etc}
        we generate just:
          {trusted_contact:{given_name: "new value"}}

        NOTE: This function recurses to handle nested models, so do not use on a self-referential model

        Returns:
            dict: a dict containing any set fields
        """

        def map_values(val: Any) -> Any:
            """
            Some types have issues being json encoded, we convert them here to be encodable

            also handles nested models and lists
            """

            if isinstance(val, UUID):
                return str(val)

            if isinstance(val, NonEmptyRequest):
                return val.to_request_fields()

            if isinstance(val, dict):
                return {k: map_values(v) for k, v in val.items()}

            if isinstance(val, list):
                return [map_values(v) for v in val]

            return val

        # pydantic almost has what we need by passing exclude_none to dict() but it returns:
        #  {trusted_contact: {}, contact: {}, identity: None, etc}
        # so we do a simple list comprehension to filter out None and {}
        return {
            key: map_values(val)
            for key, val in self.dict(exclude_none=True).items()
            if val and len(str(val)) > 0
        }


class ClosePositionRequest(NonEmptyRequest):
    """
    Attributes:
        qty (str): The number of shares to liquidate.
        percentage (str): The percentage of shares to liquidate.
    """

    qty: Optional[str]
    percentage: Optional[str]

    @root_validator()
    def root_validator(cls, values: dict) -> dict:
        if "qty" not in values or "percentage" not in values:
            return values

        if values["qty"] is None and values["percentage"] is None:
            raise ValueError(
                "qty or percentage must be given to the ClosePositionRequest, got None for both."
            )

        if values["qty"] is not None and values["percentage"] is not None:
            raise ValueError(
                "Only one of qty or percentage must be given to the ClosePositionRequest, got both."
            )

        return values


class GetPortfolioHistoryRequest(NonEmptyRequest):
    """
    Attributes:
        period (Optional[str]): The duration of the data in number + unit, such as 1D. unit can be D for day, W for
          week, M for month and A for year. Defaults to 1M.
        timeframe (Optional[str]): The resolution of time window. 1Min, 5Min, 15Min, 1H, or 1D. If omitted, 1Min for
          less than 7 days period, 15Min for less than 30 days, or otherwise 1D.
        date_end (Optional[date]): The date the data is returned up to. Defaults to the current market date (rolls over
          at the market open if extended_hours is false, otherwise at 7am ET).
        extended_hours (Optional[bool]): If true, include extended hours in the result. This is effective only for
          timeframe less than 1D.
    """

    period: Optional[str]
    timeframe: Optional[str]
    date_end: Optional[date]
    extended_hours: Optional[bool]


class GetCalendarRequest(NonEmptyRequest):
    """
    Represents the optional filtering you can do when requesting a Calendar object
    """

    start: Optional[date] = None
    end: Optional[date] = None


class CreateWatchlistRequest(NonEmptyRequest):
    """
    Represents the fields you can specify when creating a Watchlist

    Attributes:
        name(str): Name of the Watchlist
        symbols(List[str]): Symbols of Assets to watch
    """

    name: str
    symbols: List[str]

    @root_validator()
    def root_validator(cls, values: dict) -> dict:
        return values


class UpdateWatchlistRequest(NonEmptyRequest):
    """
    Represents the fields you can specify when updating a Watchlist

    Attributes:
        name(Optional[str]): Name of the Watchlist
        symbols(Optional[List[str]]): Symbols of Assets to watch
    """

    name: Optional[str]
    symbols: Optional[List[str]]

    @root_validator()
    def root_validator(cls, values: dict) -> dict:
        if ("name" not in values or values["name"] is None) and (
            "symbols" not in values or values["symbols"] is None
        ):
            raise ValueError("One of 'name' or 'symbols' must be defined")

        return values
