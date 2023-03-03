from typing import List
from alpaca.trading.enums import DTBPCheck, PDTCheck
from alpaca.trading.models import AccountConfiguration as TradeAccountConfiguration

from alpaca.broker.models import (
    Identity,
    Contact,
    Disclosures,
    Agreement,
    AccountDocument,
    TrustedContact,
)
from alpaca.broker.enums import (
    FundingSource,
    TaxIdType,
    AgreementType,
)


def create_dummy_identity() -> Identity:
    """
    Create a basic identity instance with prefilled data

    Returns:
        Identity: a prefilled Identity instance for testing
    """

    # These are all the fields the api always returns even if null, aka
    # non-optional but still nullable fields
    return Identity(
        given_name="John",
        family_name="Doe",
        middle_name="Smith",
        date_of_birth="1990-01-01",
        tax_id_type=TaxIdType.USA_SSN,
        country_of_citizenship="USA",
        country_of_birth="USA",
        country_of_tax_residence="USA",
        funding_source=[FundingSource.EMPLOYMENT_INCOME],
        visa_type=None,
        visa_expiration_date=None,
        date_of_departure_from_usa=None,
        permanent_resident=None,
    )


def create_dummy_contact() -> Contact:
    """
    Create a prefilled Contact instance for testing with

    Returns:
        Contact: a prefilled Contact instance for testing
    """

    return Contact(
        email_address="cool_alpaca@example.com",
        phone_number="555-666-7788",
        street_address=["20 N San Mateo Dr"],
        unit="Apt 1A",
        city="San Mateo",
        state="CA",
        postal_code="94401",
    )


def create_dummy_agreements() -> List[Agreement]:
    """
    Create a List of Agreements, one for each of the required AgreementType's

    Returns:
         List[Agreement]: A List of Agreements, one for each of the required AgreementType's
    """
    required_types = [
        AgreementType.ACCOUNT,
        AgreementType.CRYPTO,
        AgreementType.CUSTOMER,
        AgreementType.MARGIN,
    ]

    result = [
        Agreement(
            agreement=agreement_type,
            signed_at="2020-09-11T18:09:33Z",
            ip_address="185.13.21.99",
            revision="16.2021.05",
        )
        for agreement_type in required_types
    ]

    return result


def create_dummy_disclosures() -> Disclosures:
    """
    Create a basic Disclosures instance with prefilled data

    Returns:
        Disclosures:  A basic Disclosures instance with prefilled data
    """

    return Disclosures(
        is_control_person=False,
        is_affiliated_exchange_or_finra=False,
        is_politically_exposed=False,
        immediate_family_exposed=False,
        is_discretionary=False,
    )


def create_dummy_trusted_contact() -> TrustedContact:
    """
    Create a basic TrustedContact instance with prefilled dummy data
    Returns:
        TrustedContact: A basic TrustedContact instance with prefilled data for testing
    """
    return TrustedContact(
        given_name="Jane",
        family_name="Doe",
        email_address="jane.doe@example.com",
    )


def create_dummy_account_documents() -> List[AccountDocument]:
    return [
        AccountDocument(
            id="bb6de14c-9393-4b6c-8e93-c6724ac7b703",
            created_at="2022-01-21T21:25:28.189455Z",
            content="https://example.com/not-a-real-url",
            document_sub_type="passport",
            document_type="identity_verification",
        )
    ]


def create_dummy_trade_account_configuration() -> TradeAccountConfiguration:
    return TradeAccountConfiguration(
        dtbp_check=DTBPCheck.BOTH,
        fractional_trading=True,
        max_margin_multiplier="4",
        no_shorting=False,
        pdt_check=PDTCheck.ENTRY,
        suspend_trade=False,
        trade_confirm_email="all",
    )
