from datetime import date
from uuid import UUID

from .models import ValidateBaseModel as BaseModel
from ..enums import CorporateActionType, CorporateActionSubType


class CorporateActionAnnouncement(BaseModel):
    """
    An announcement of a corporate action. Corporate actions are events like dividend payouts, mergers and stock splits.

    Attributes:
        id (UUID): The unique identifier for this single announcement.
        corporate_action_id (str): ID that remains consistent across all announcements for the same corporate action.
        ca_type (CorporateActionType): The type of corporate action that was announced.
        ca_sub_type (CorporateActionSubType): The specific subtype of corporate action that was announced.
        initiating_symbol (str): Symbol of the company initiating the announcement.
        initiating_original_cusip (str): CUSIP of the company initiating the announcement.
        target_symbol (str): Symbol of the child company involved in the announcement.
        target_original_cusip (str): CUSIP of the child company involved in the announcement.
        declaration_date (date): Date the corporate action or subsequent terms update was announced.
        ex_date (date): The first date that purchasing a security will not result in a corporate action entitlement.
        record_date (date): The date an account must hold a settled position in the security in order to receive the
            corporate action entitlement.
        payable_date (date): The date the announcement will take effect. On this date, account stock and cash
            balances are expected to be processed accordingly.
        cash (float): The amount of cash to be paid per share held by an account on the record date.
        old_rate (float): The denominator to determine any quantity change ratios in positions.
        new_rate (float): The numerator to determine any quantity change ratios in positions.
    """

    id: UUID
    corporate_action_id: str
    ca_type: CorporateActionType
    ca_sub_type: CorporateActionSubType
    initiating_symbol: str
    initiating_original_cusip: str
    target_symbol: str
    target_original_cusip: str
    declaration_date: date
    ex_date: date
    record_date: date
    payable_date: date
    cash: float
    old_rate: float
    new_rate: float
