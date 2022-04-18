from datetime import datetime
from typing import List, Optional, Union
from uuid import UUID

from pydantic import BaseModel

from ..enums import CIPApprovalStatus, CIPProvider, CIPResult, CIPStatus


class CIPKYCInfo(BaseModel, validate_assignment=True):
    """
    Represents Know Your Customer (KYC) info for a CIPInfo

    Attributes:
        id (str): Your internal ID of check
        risk_score (Optional[int]): Overall risk score returned by KYC provider or assessed
        risk_level (Optional[str]): Overall risk level returned by KYC provider or assessed
        risk_categories (Optional[List[str]]): The list of risk categories returned by the KYC provider or assessed
        applicant_name (Optional[str]): Given and family name of applicant
        email_address (Optional[str]): email address of applicant
        nationality (Optional[str]): nationality of applicant
        date_of_birth (Optional[datetime]): DOB of applicant
        address (Optional[str]): Concatenated street address, city, state and country of applicant
        postal_code (Optional[str]): postal code for `address` field
        country_of_residency (Optional[str]): country for `address` field
        kyc_completed_at (Optional[datetime]): Datetime that KYC check was completed at
        ip_address (Optional[str]): ip address of applicant at time of KYC check
        check_initiated_at (Optional[datetime]): start datetime of KYC check
        check_completed_at (Optional[datetime]): completion datetime of KYC check
        approval_status (Optional[CIPApprovalStatus]): Approval status of KYC check
        approved_by (Optional[str]): Identifier of who approved KYC check
        approved_reason (Optional[str]): Reason for approving this KYC check
        approved_at (Optional[datetime]): Datetime that this KYC check was approved
    """

    id: str
    risk_score: Optional[int]
    risk_level: Optional[str]
    risk_categories: Optional[List[str]]
    applicant_name: Optional[str]
    email_address: Optional[str]
    nationality: Optional[str]
    date_of_birth: Optional[datetime]
    address: Optional[str]
    postal_code: Optional[str]
    country_of_residency: Optional[str]
    kyc_completed_at: Optional[datetime]
    ip_address: Optional[str]
    check_initiated_at: Optional[datetime]
    check_completed_at: Optional[datetime]
    approval_status: Optional[CIPApprovalStatus]
    approved_by: Optional[str]
    approved_reason: Optional[str]
    approved_at: Optional[datetime]


class CIPDocument(BaseModel, validate_assignment=True):
    """
    Represents results of checking a document for CIPInfo

    Attributes:
        id (str): Your internal ID of check
        result (Optional[CIPResult]): Overall result of specific check
        status (Optional[CIPStatus]): Overall status of specific check
        created_at (Optional[datetime]): Datetime for when this check was done
        date_of_birth (Optional[datetime]): DOB for applicant if found on document
        date_of_expiry (Optional[datetime]): date of expiry for the checked document
        document_numbers (Optional[List[str]]): Number of the document that was checked
        document_type (Optional[str]): Type of the document that was checked
        first_name (Optional[str]): First name extracted from the document
        last_name (Optional[str]): Last name extracted from the document
        gender (Optional[str]): Gender info extracted from the document
        issuing_country (Optional[str]): Country for which issued the document
        nationality (Optional[str]):
        age_validation (Optional[CIPResult]): Result of checks on whether the age calculated from the document’s date
          of birth data point is greater than or equal to the minimum accepted age set at account level
        compromised_document (Optional[CIPResult]): Result of check on whether the image of the document has been found
          in our internal database of compromised documents
        police_record (Optional[CIPStatus]): Result of check on whether the document has been identified as lost,
          stolen or otherwise compromised
        data_comparison (Optional[CIPResult]): Result of check on whether data on the document is consistent with data
          provided when creating an applicant through the API
        data_comparison_breakdown (Optional[str]): json object representing the results of the various sub-checks
          done when calculating the result on `data_comparison`. Example: {“date_of_birth”: “clear”,
          “date_of_expiry”: “clear” “document_numbers”: “clear”, “document_type”: “clear”, “first_name”: “clear”,
          “gender”: “clear”, “issuing_country”: “clear”, “last_name”: “clear”}
        image_integrity (Optional[CIPResult]): Result of checks on whether the document was of sufficient quality to
          verify
        image_integrity_breakdown (Optional[str]): json object representing the results of the various sub-checks done
          when calculating the result on `image_integrity`. Example: example: {“colour_picture”: “clear”,
          “conclusive_document_quality”: “clear”, “image_quality”: “clear”, “supported_document”: “clear”}
        visual_authenticity (Optional[str]): json object representing the the various sub-checks done when determening
          whether visual (non-textual) elements are correct given the document type. Example: {
          “digital_tampering”: “clear”, “face_detection”: “clear”, “fonts”: “clear”, “original_document_present”:
          “clear”, “picture_face_integrity”: “clear”, “security_features”: “clear”, “template”: “clear”}

    """

    id: str
    result: Optional[CIPResult]
    status: Optional[CIPStatus]
    created_at: Optional[datetime]
    date_of_birth: Optional[datetime]
    date_of_expiry: Optional[datetime]
    document_numbers: Optional[List[str]]
    document_type: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    gender: Optional[str]
    issuing_country: Optional[str]
    nationality: Optional[str]
    age_validation: Optional[CIPResult]
    compromised_document: Optional[CIPResult]
    police_record: Optional[CIPStatus]
    data_comparison: Optional[CIPResult]
    data_comparison_breakdown: Optional[str]
    image_integrity: Optional[CIPResult]
    image_integrity_breakdown: Optional[str]
    visual_authenticity: Optional[str]


class CIPPhoto(BaseModel, validate_assignment=True):
    pass


class CIPIdentity(BaseModel, validate_assignment=True):
    pass


class CIPWatchlist(BaseModel, validate_assignment=True):
    """
    CIPWatchlist

    Attributes:
    """

    pass


class CIPInfo(BaseModel, validate_assignment=True):
    """
    The Customer Identification Program (CIP) API allows you to submit the CIP results received from your KYC provider.

    This model is how to represent that information when talking to Alpaca

    Args:
        id (UUID): ID of this CIPInfo
        account_id (UUID): UUID of the Account instance this CIPInfo is for
        provider_name (List[CIPProvider]): List of KYC providers this information came from
        created_at (datetime): date and time this CIPInfo was first uploaded to Alpaca
        updated_at (datetime): date and time that this CIPInfo was last update
        kyc (Optional[CIPKYCInfo]): KYC info for this Account if any
        document (Optional[CIPDocument]): Any CIP documents uploaded for this Account
        photo (Optional[CIPPhoto]): Any photos attached for CIP
        identity (Optional[CIPIdentity]): Any CIP Identity information
        watchlist (Optional[CIPWatchlist]): Any CIP watchlist information
    """

    id: UUID
    account_id: UUID
    provider_name: List[CIPProvider]
    created_at: datetime
    updated_at: datetime
    kyc: Optional[CIPKYCInfo] = None
    document: Optional[CIPDocument] = None
    photo: Optional[CIPPhoto] = None
    identity: Optional[CIPIdentity] = None
    watchlist: Optional[CIPWatchlist] = None

    def __init__(self, *args, **kwargs):
        # upcast into uuid
        if "id" in kwargs and type(kwargs["id"]) == str:
            kwargs["id"] = UUID(kwargs["id"])

        if "account_id" in kwargs and type(kwargs["account_id"]) == str:
            kwargs["account_id"] = UUID(kwargs["account_id"])

        super().__init__(*args, **kwargs)
