import datetime

from .models import ValidateBaseModel as BaseModel
from typing import Optional
from datetime import date
from pydantic import root_validator
from uuid import UUID


class NonEmptyRequest(BaseModel):
    """
    Mixin for models that represent requests where we don't want to send nulls for optional fields.
    """

    def to_request_fields(self) -> dict:
        """
        the equivalent of self::dict but removes empty values.

        Ie say we only set trusted_contact.given_name instead of generating a dict like:
          {contact: {city: None, country: None...}, etc}
        we generate just:
          {trusted_contact:{given_name: "new value"}}

        Returns:
            dict: a dict containing any set fields
        """

        # pydantic almost has what we need by passing exclude_none to dict() but it returns:
        #  {trusted_contact: {}, contact: {}, identity: None, etc}
        # so we do a simple list comprehension to filter out None and {}
        return {
            key: (val if not isinstance(val, UUID) else str(val))
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
