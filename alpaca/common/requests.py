from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from alpaca.common.models import ValidateBaseModel as BaseModel


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

            # RFC 3339
            if isinstance(val, datetime):
                # if the datetime is naive, assume it's UTC
                # https://docs.python.org/3/library/datetime.html#determining-if-an-object-is-aware-or-naive
                if val.tzinfo is None or val.tzinfo.utcoffset(val) is None:
                    val = val.replace(tzinfo=timezone.utc)
                return val.isoformat()

            return val

        # pydantic almost has what we need by passing exclude_none to dict() but it returns:
        #  {trusted_contact: {}, contact: {}, identity: None, etc}
        # so we do a simple list comprehension to filter out None and {}
        return {
            key: map_values(val)
            for key, val in self.model_dump(exclude_none=True).items()
            if val and len(str(val)) > 0
        }
