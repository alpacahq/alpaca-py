from datetime import datetime
from typing import Optional
from uuid import UUID

from ..enums import ACHRelationshipStatus, BankAccountType
from alpaca.common.models import ValidateBaseModel as BaseModel


class ACHRelationship(BaseModel):
    """
    Attributes:
        id (UUID): ID of Relationship
        account_id (UUID): ID of the Account this ACHRelationship is tied to
        created_at (datetime): Date and time this relationship was created
        updated_at (datetime): Date and time of when this relationship was last updated
        status (ACHRelationshipStatus): Current status of the relationship
        account_owner_name (str): Full name of the account owner
        bank_account_type (BankAccountType): The kind of bank account this relationship points to
        bank_account_number (str): The number of bank account that the relationship points to
        bank_routing_number (str): Routing number for the bank account
        nickname (str): User provided name for account
        processor_token (Optional[str]): If you are using Plaid, then this is a Plaid processor token.
    """

    id: UUID
    account_id: UUID
    created_at: datetime
    updated_at: datetime
    status: ACHRelationshipStatus
    account_owner_name: str
    bank_account_type: BankAccountType
    bank_account_number: str
    bank_routing_number: str
    nickname: str
    processor_token: Optional[str] = None
