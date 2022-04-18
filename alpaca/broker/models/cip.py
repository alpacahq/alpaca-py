from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

from ..enums import (
    CIPProvider,
)


class KYCInfo(BaseModel, validate_assignment=True):
    pass


class CIPDocument(BaseModel, validate_assignment=True):
    pass


class CIPPhoto(BaseModel, validate_assignment=True):
    pass


class CIPIdentity(BaseModel, validate_assignment=True):
    pass


class CIPWatchlist(BaseModel, validate_assignment=True):
    pass


class CIPInfo(BaseModel, validate_assignment=True):
    """ """

    id: str
    account_id: UUID
    provider_name: List[CIPProvider]
    created_at: datetime
    updated_at: datetime
    kyc: Optional[KYCInfo] = None
    document: Optional[CIPDocument] = None
    photo: Optional[CIPPhoto] = None
    identity: Optional[CIPIdentity] = None
    watchlist: Optional[CIPWatchlist] = None

    def __init__(self, *args, **kwargs):
        # upcast into uuid
        if "account_id" in kwargs and type(kwargs["account_id"]) == str:
            kwargs["account_id"] = UUID(kwargs["account_id"])

        super().__init__(*args, **kwargs)
