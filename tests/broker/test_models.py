import warnings
from datetime import datetime
from typing import Optional, get_args, get_type_hints

import pytest
from pydantic import TypeAdapter

from alpaca.broker.requests import (
    UploadDocumentMimeType,
    UploadDocumentRequest,
    UploadDocumentSubType,
    DocumentType,
    UploadW8BenDocumentRequest,
    W8BenDocument,
    CreateJournalRequest,
)
from alpaca.broker.models import (
    Account,
    AccountDisclosures,
    AccountDocument,
    AccountExtended,
    Disclosures,
    MinorIdentity,
    TradeDocument,
    Transfer,
    TrustedContact,
)
from alpaca.broker.requests import (
    UpdateAccountRequest,
    UpdatableTrustedContact,
    UpdatableContact,
    UpdatableIdentity,
    UpdatableDisclosures,
    GetAccountActivitiesRequest,
    GetEventsRequest,
    GetJournalsRequest,
    GetTradeDocumentsRequest,
    CreateAccountRequest,
    CreateBankRequest,
    CreateACHRelationshipRequest,
    CreateACHTransferRequest,
    CreateBankTransferRequest,
    BatchJournalRequestEntry,
    CreateOptionExerciseRequest,
    TransferIRA,
)
from alpaca.broker.enums import (
    AgreementType,
    BankAccountType,
    IdentifierType,
    TaxIdType,
    TransferType,
    TransferDirection,
    JournalEntryType,
    JournalStatus,
)
from alpaca.broker.models.funding import BankAdditionalFields
from alpaca.trading.enums import (
    ActivityCategory,
    ActivityType,
    AssetClass,
    AssetStatus,
    CalendarDateType,
)
from alpaca.trading.requests import GetCalendarRequest
from tests.broker.factories import create_dummy_w8ben_document
from uuid import UUID, uuid4


def test_document_validates_id():
    """
    Test the validation logic in Document model, note this isn't testing the validation we get from pydantic
    simply testing the allowing str to auto convert into uuid
    """

    with pytest.raises(ValueError):
        AccountDocument(
            id="not a uuid str",
            created_at="2022-01-21T21:25:28.189455Z",
            content="https://example.com/not-a-real-url",
            document_sub_type="passport",
            document_type="identity_verification",
        )

    with pytest.raises(ValueError):
        AccountDocument(
            id=12,
            created_at="2022-01-21T21:25:28.189455Z",
            content="https://example.com/not-a-real-url",
            document_sub_type="passport",
            document_type="identity_verification",
        )


def test_account_update_request_to_request_fields():
    name = "TEST"
    req = UpdateAccountRequest(trusted_contact=UpdatableTrustedContact(given_name=name))

    result = req.to_request_fields()
    expected = {"trusted_contact": {"given_name": name}}

    assert expected == result
    assert {} == UpdateAccountRequest().to_request_fields()

    empty_req = UpdateAccountRequest(
        identity=UpdatableIdentity(),
        disclosures=UpdatableDisclosures(),
        contact=UpdatableContact(),
        trusted_contact=UpdatableTrustedContact(),
    )

    assert {} == empty_req.to_request_fields()


def test_get_account_activities_request_validates_date_parameters_for_conflicts():
    req = GetAccountActivitiesRequest(date=datetime.now())

    with pytest.raises(ValueError) as e:
        req.after = datetime.now()

    assert "Cannot set date and after at the same time" in str(e.value)

    with pytest.raises(ValueError) as e:
        req.until = datetime.now()

    assert "Cannot set date and until at the same time" in str(e.value)


def test_get_account_activities_request_to_request_fields():
    req = GetAccountActivitiesRequest()

    assert req.to_request_fields() == {}

    req = GetAccountActivitiesRequest(activity_types=[ActivityType.DIV])

    assert req.to_request_fields() == {"activity_types": "DIV"}

    req = GetAccountActivitiesRequest(
        activity_types=[ActivityType.DIV, ActivityType.DIVNRA]
    )

    assert req.to_request_fields() == {"activity_types": "DIV,DIVNRA"}


def test_trade_document_sub_type_empty_str_to_none():
    doc = TradeDocument(
        id="1b560b0f-9efd-44b4-8004-dfd520c7cdc0",
        name="",
        type="account_statement",
        sub_type="",
        date="2022-02-28",
    )

    assert doc.sub_type is None


def test_get_trade_documents_request_upcasts_dates():
    # We have this part out here to assert a non raise as pytest will auto fail non caught exceptions
    GetTradeDocumentsRequest(start="2022-02-02", end="2022-02-02")

    with pytest.raises(ValueError) as e:
        GetTradeDocumentsRequest(
            start="2022-02-02-2",
        )

    assert "Invalid isoformat" in str(e.value)

    with pytest.raises(ValueError) as e:
        GetTradeDocumentsRequest(
            end="2022-02-02-2",
        )

    assert "Invalid isoformat" in str(e.value)


def test_get_trade_documents_request_validates_start_not_after_end():
    with pytest.raises(ValueError) as e:
        GetTradeDocumentsRequest(start="2022-02-02", end="2022-01-02")

    assert "start must not be after end" in str(e.value)


def test_upload_document_request_rejects_w8_ben():
    with pytest.raises(ValueError) as e:
        UploadDocumentRequest(
            document_type=DocumentType.W8BEN,
            content="",
            mime_type=UploadDocumentMimeType.JSON,
        )

    assert (
        "Error please use the UploadW8BenDocument class for uploading W8BEN documents"
        in str(e.value)
    )

    with pytest.raises(ValueError) as e:
        UploadDocumentRequest(
            document_type=DocumentType.ACCOUNT_APPROVAL_LETTER,
            document_sub_type=UploadDocumentSubType.FORM_W8_BEN,
            content="",
            mime_type=UploadDocumentMimeType.JSON,
        )

    assert (
        "Error please use the UploadW8BenDocument class for uploading W8BEN documents"
        in str(e.value)
    )


def test_upload_w8ben_document_request_defaults_values():
    """This test has no asserts as it verifies no raise of exception"""

    UploadW8BenDocumentRequest(
        content="fake base64", mime_type=UploadDocumentMimeType.PDF
    )


def test_upload_w8ben_document_request_validates_w8ben_document_type():
    val = UploadW8BenDocumentRequest(
        content="",
        mime_type=UploadDocumentMimeType.PDF,
    )

    with pytest.raises(ValueError) as e:
        val.document_type = DocumentType.ACCOUNT_APPROVAL_LETTER

    assert "document_type must be W8BEN." in str(e.value)


def test_upload_w8ben_document_request_validates_w8ben_sub_type():
    val = UploadW8BenDocumentRequest(
        content="",
        mime_type=UploadDocumentMimeType.PDF,
    )

    with pytest.raises(ValueError) as e:
        val.document_sub_type = UploadDocumentSubType.ACCOUNT_APPLICATION

    assert "document_sub_type must be FORM_W8_BEN." in str(e.value)


def test_upload_w8ben_document_request_validates_at_least_one_content_field():
    with pytest.raises(ValueError) as e:
        UploadW8BenDocumentRequest(mime_type=UploadDocumentMimeType.PDF)

    assert (
        "You must specify one of either the `content` or `content_data` fields"
        in str(e.value)
    )


def test_upload_w8ben_document_request_validates_only_one_content_field_set():
    with pytest.raises(ValueError) as e:
        UploadW8BenDocumentRequest(
            content="",
            content_data=create_dummy_w8ben_document(),
        )

    assert (
        "You can only specify one of either the `content` or `content_data` fields"
        in str(e.value)
    )


def test_upload_w8ben_document_request_validates_json_mime_when_content_data():
    with pytest.raises(ValueError) as e:
        UploadW8BenDocumentRequest(
            content_data=create_dummy_w8ben_document(),
            mime_type=UploadDocumentMimeType.PDF,
        )

    assert "If `content_data` is set then `mime_type` must be JSON" in str(e.value)


def test_w8ben_document_upcasts_str_like_fields():
    W8BenDocument(
        country_citizen="",
        date="2022-02-02",
        date_of_birth="2022-02-02",
        full_name="Beans",
        ip_address="192.168.1.1",
        permanent_address_city_state="",
        permanent_address_country="",
        permanent_address_street="",
        revision="",
        signer_full_name="",
        timestamp="2022-04-29T09:30:00-04:00",
        ftin_not_required=False,
    )


def test_w8ben_document_validates_ftin_not_required_states():
    # no error with foreign_tax_id set
    W8BenDocument(
        country_citizen="",
        date="2022-02-02",
        date_of_birth="2022-02-02",
        full_name="Beans",
        ip_address="192.168.1.1",
        permanent_address_city_state="",
        permanent_address_country="",
        permanent_address_street="",
        revision="",
        signer_full_name="",
        timestamp="2022-04-29T09:30:00-04:00",
        foreign_tax_id="fake",
    )

    # no error with tax_id_ssn set
    W8BenDocument(
        country_citizen="",
        date="2022-02-02",
        date_of_birth="2022-02-02",
        full_name="Beans",
        ip_address="192.168.1.1",
        permanent_address_city_state="",
        permanent_address_country="",
        permanent_address_street="",
        revision="",
        signer_full_name="",
        timestamp="2022-04-29T09:30:00-04:00",
        tax_id_ssn="fake ssn",
    )

    with pytest.raises(ValueError) as e:
        W8BenDocument(
            country_citizen="",
            date="2022-02-02",
            date_of_birth="2022-02-02",
            full_name="Beans",
            ip_address="192.168.1.1",
            permanent_address_city_state="",
            permanent_address_country="",
            permanent_address_street="",
            revision="",
            signer_full_name="",
            timestamp="2022-04-29T09:30:00-04:00",
        )

    assert (
        "ftin_not_required must be set if foreign_tax_id and tax_id_ssn are not"
        in str(e.value)
    )


def test_valid_aba_bank():
    CreateBankRequest(
        name="name",
        bank_code_type=IdentifierType.ABA,
        bank_code="123456789",
        account_number="123456789abc",
    )


def test_valid_bic_bank():
    CreateBankRequest(
        name="name",
        bank_code_type=IdentifierType.BIC,
        bank_code="123456789",
        account_number="123456789abc",
        country="United States",
        state_province="New York",
        postal_code="10036",
        city="Manhattan",
        street_address="Sixth Avenue & 42nd Street",
    )


def test_extra_parameters_for_aba_bank():
    with pytest.raises(ValueError) as e:
        CreateBankRequest(
            name="name",
            bank_code_type=IdentifierType.ABA,
            bank_code="123456789",
            account_number="123456789abc",
            country="United States",
            state_province="New York",
            postal_code="10036",
            city="Manhattan",
            street_address="Sixth Avenue & 42nd Street",
        )

    assert "You may only specify" in str(e.value)


def test_missing_parameters_for_bic_bank():
    with pytest.raises(ValueError) as e:
        CreateBankRequest(
            name="name",
            bank_code_type=IdentifierType.BIC,
            bank_code="123456789",
            account_number="123456789abc",
        )

    assert "You must specify" in str(e.value)


def test_valid_ach_transfer_request():
    CreateACHTransferRequest(
        relationship_id=uuid4(),
        amount="100.0",
        direction=TransferDirection.INCOMING,
    )


def test_valid_bank_transfer_request():
    CreateBankTransferRequest(
        bank_id=uuid4(),
        amount="100.0",
        direction=TransferDirection.INCOMING,
    )


def test_zero_transfer_amount():
    with pytest.raises(ValueError) as e:
        CreateACHTransferRequest(
            relationship_id=uuid4(),
            amount="0",
            direction=TransferDirection.INCOMING,
        )

    assert "You must provide an amount > 0." in str(e.value)


def test_negative_transfer_amount():
    with pytest.raises(ValueError) as e:
        CreateACHTransferRequest(
            relationship_id=uuid4(),
            amount="-100.0",
            direction=TransferDirection.INCOMING,
        )

    assert "You must provide an amount > 0." in str(e.value)


def test_ach_transfer_with_wire_transfer_type():
    with pytest.raises(ValueError) as e:
        CreateACHTransferRequest(
            relationship_id=uuid4(),
            amount="0",
            direction=TransferDirection.INCOMING,
            transfer_type=TransferType.WIRE,
        )

    assert "Transfer type must be TransferType.ACH for ACH transfer requests." in str(
        e.value
    )


def test_bank_transfer_with_ach_transfer_type():
    with pytest.raises(ValueError) as e:
        CreateBankTransferRequest(
            relationship_id=uuid4(),
            amount="0",
            direction=TransferDirection.INCOMING,
            transfer_type=TransferType.ACH,
        )

    assert "Transfer type must be TransferType.WIRE for bank transfer requests." in str(
        e.value
    )


def test_journal_with_amount_and_qty():
    with pytest.raises(ValueError) as e:
        CreateJournalRequest(
            from_account="c94bu7rn-4483-4199-840f-6c5fe0b7ca24",
            entry_type=JournalEntryType.CASH,
            to_account="fn68sbrk-6f2a-433c-8c33-17b66b8941fa",
            amount=51,
            qty=32,
        )

    assert "Symbol and qty are reserved for security journals." in str(e.value)

    with pytest.raises(ValueError) as e:
        CreateJournalRequest(
            from_account="5f7fb16f-b530-4b1a-bffe-d710fbd106b7",
            entry_type=JournalEntryType.SECURITY,
            to_account="c117d42d-e1c8-4281-a6be-4e39fae2c821",
            qty=32,
        )

    assert (
        "Security journals must contain a symbol and corresponding qty to transfer."
        in str(e.value)
    )

    with pytest.raises(ValueError) as e:
        CreateJournalRequest(
            from_account="c94bu7rn-4483-4199-840f-6c5fe0b7ca24",
            entry_type=JournalEntryType.SECURITY,
            to_account="fn68sbrk-6f2a-433c-8c33-17b66b8941fa",
            amount=20,
            qty=2,
        )

    assert "Amount is reserved for cash journals." in str(e.value)

    with pytest.raises(ValueError) as e:
        CreateJournalRequest(
            from_account="c94bu7rn-4483-4199-840f-6c5fe0b7ca24",
            entry_type=JournalEntryType.CASH,
            to_account="fn68sbrk-6f2a-433c-8c33-17b66b8941fa",
        )

    assert "Cash journals must contain an amount to transfer." in str(e.value)


def test_trusted_contact_string_street_address_warns_and_serializes_as_list():
    with pytest.warns(DeprecationWarning, match="street_address"):
        contact = TrustedContact(
            given_name="Ada",
            family_name="Lovelace",
            email_address="ada@example.com",
            street_address="20 N San Mateo Dr",
        )

    assert contact.street_address == "20 N San Mateo Dr"
    assert contact.model_dump()["street_address"] == ["20 N San Mateo Dr"]


def test_trusted_contact_keeps_street_address_list():
    lines = ["20 N San Mateo Dr", "Apt 1A"]
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        contact = TrustedContact(
            given_name="Ada",
            family_name="Lovelace",
            email_address="ada@example.com",
            street_address=lines,
        )

    assert contact.street_address == lines
    assert contact.model_dump()["street_address"] == lines


def test_updatable_trusted_contact_string_street_address_warns_and_serializes_as_list():
    with pytest.warns(DeprecationWarning, match="street_address"):
        contact = UpdatableTrustedContact(street_address="20 N San Mateo Dr")
        fields = UpdateAccountRequest(trusted_contact=contact).to_request_fields()

    assert contact.street_address == "20 N San Mateo Dr"
    assert fields == {"trusted_contact": {"street_address": ["20 N San Mateo Dr"]}}


def test_updatable_trusted_contact_list_street_address_serializes_as_list():
    lines = ["20 N San Mateo Dr", "Apt 1A"]
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        contact = UpdatableTrustedContact(street_address=lines)
        fields = UpdateAccountRequest(trusted_contact=contact).to_request_fields()

    assert contact.street_address == lines
    assert fields == {"trusted_contact": {"street_address": lines}}


def test_get_events_request_since_id_and_until_id_warn_on_read():
    request = GetEventsRequest(since_id=1, until_id=2)

    with pytest.warns(DeprecationWarning, match="since_id"):
        assert request.since_id == 1

    with pytest.warns(DeprecationWarning, match="until_id"):
        assert request.until_id == 2

    assert request.to_request_fields() == {"since_id": 1, "until_id": 2}


def test_get_events_request_since_ulid_and_until_ulid_do_not_warn():
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        request = GetEventsRequest(
            since_ulid="01ARZ3NDEKTSV4RRFFQ69G5FAV",
            until_ulid="01ARZ3NDEKTSV4RRFFQ69G5FAW",
        )

    assert request.to_request_fields() == {
        "since_ulid": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
        "until_ulid": "01ARZ3NDEKTSV4RRFFQ69G5FAW",
    }


def _account_with_trusted_street_address(street_address):
    return {
        "id": "0d969814-40d6-4b2b-99ac-2e37427f1ad2",
        "account_number": "682389557",
        "status": "SUBMITTED",
        "currency": "USD",
        "last_equity": "0",
        "created_at": "2022-04-12T17:24:31.30283Z",
        "trusted_contact": {
            "given_name": "Jane",
            "family_name": "Doe",
            "email_address": "jane.doe@example.com",
            "street_address": street_address,
        },
    }


def test_account_response_string_street_address_does_not_warn():
    payload = _account_with_trusted_street_address("20 N San Mateo Dr")
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        account = Account(**payload)
        accounts = TypeAdapter(list[Account]).validate_python([payload])

    assert account.trusted_contact.street_address == "20 N San Mateo Dr"
    assert accounts[0].trusted_contact.street_address == "20 N San Mateo Dr"
    assert account.trusted_contact.model_dump()["street_address"] == [
        "20 N San Mateo Dr"
    ]


def test_account_response_list_street_address_stays_list():
    lines = ["20 N San Mateo Dr", "Apt 1A"]
    payload = _account_with_trusted_street_address(lines)
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        account = Account(**payload)
        accounts = TypeAdapter(list[Account]).validate_python([payload])

    assert account.trusted_contact.street_address == lines
    assert accounts[0].trusted_contact.street_address == lines
    assert account.trusted_contact.model_dump()["street_address"] == lines


def test_trusted_contact_street_address_annotation_stays_optional_str():
    assert TrustedContact.model_fields["street_address"].annotation == Optional[str]
    assert (
        UpdatableTrustedContact.model_fields["street_address"].annotation
        == Optional[str]
    )
    assert get_type_hints(TrustedContact)["street_address"] == Optional[str]
    assert get_type_hints(UpdatableTrustedContact)["street_address"] == Optional[str]


def test_trusted_contact_street_address_schema_uses_stored_list():
    string_schema = {"deprecated": True, "type": "string"}
    list_schema = {"items": {"type": "string"}, "type": "array"}
    null_schema = {"type": "null"}
    validation = TrustedContact.model_json_schema()["properties"]["street_address"]
    serialization = TypeAdapter(TrustedContact).json_schema(mode="serialization")[
        "properties"
    ]["street_address"]

    assert string_schema in validation["anyOf"]
    assert list_schema in validation["anyOf"]
    assert null_schema in validation["anyOf"]
    assert "deprecated" not in validation
    assert list_schema in serialization["anyOf"]
    assert null_schema in serialization["anyOf"]
    assert string_schema not in serialization["anyOf"]
    assert {"type": "string"} not in serialization["anyOf"]


def test_trusted_contact_rejects_non_string_street_address():
    with pytest.raises(ValueError):
        TrustedContact(
            given_name="Ada",
            family_name="Lovelace",
            email_address="ada@example.com",
            street_address=123,
        )

    with pytest.raises(ValueError):
        TrustedContact(
            given_name="Ada",
            family_name="Lovelace",
            email_address="ada@example.com",
            street_address=["20 N San Mateo Dr", 2],
        )


def test_calendar_request_accepts_date_type_and_datetime_bounds():
    request = GetCalendarRequest(
        start="2026-01-01T00:00:00Z",
        end="2026-01-02T00:00:00Z",
        date_type="SETTLEMENT",
    )

    assert request.date_type == CalendarDateType.SETTLEMENT
    assert request.to_request_fields()["date_type"] == "SETTLEMENT"
    assert request.to_request_fields()["start"] == "2026-01-01"

    with pytest.raises(ValueError):
        GetCalendarRequest(date_type="session")


def test_asset_status_includes_all():
    assert AssetStatus.ALL == "all"


def test_journals_request_sends_limit():
    request = GetJournalsRequest(
        after="2026-01-01",
        status=JournalStatus.PENDING,
        entry_type=JournalEntryType.CASH,
        limit=1,
    )

    assert request.to_request_fields()["limit"] == 1
    assert request.to_request_fields()["entry_type"] == JournalEntryType.CASH


def test_account_activities_request_category_and_order_id():
    order_id = uuid4()
    request = GetAccountActivitiesRequest(
        category=ActivityCategory.TRADE_ACTIVITY,
        order_id=order_id,
        date="2026-01-01T00:00:00Z",
    )

    fields = request.to_request_fields()
    assert fields["category"] == "trade_activity"
    assert fields["order_id"] == str(order_id)
    assert "activity_types" not in fields

    with pytest.raises(ValueError, match="category and activity_types"):
        GetAccountActivitiesRequest(
            category=ActivityCategory.NON_TRADE_ACTIVITY,
            activity_types=[ActivityType.DIV],
        )

    with pytest.raises(ValueError, match="date and after"):
        GetAccountActivitiesRequest(date=datetime.now(), after=datetime.now())


def test_option_exercise_qty_is_optional():
    assert CreateOptionExerciseRequest(commission=0.25).to_request_fields() == {
        "commission": 0.25
    }
    assert CreateOptionExerciseRequest(qty="1").to_request_fields()["qty"] == "1"


def test_create_account_request_sends_minor_identity():
    minor = MinorIdentity(
        given_name="Jamie",
        family_name="Doe",
        date_of_birth="2012-04-05",
        tax_id_type=TaxIdType.USA_SSN,
        country_of_tax_residence="USA",
        state="CA",
        email="jamie.doe@example.com",
        country_of_birth="USA",
        country_of_citizenship="USA",
        tax_id="666-55-1234",
    )
    identity = {
        "given_name": "John",
        "family_name": "Doe",
        "date_of_birth": "1990-01-01",
        "country_of_tax_residence": "USA",
        "funding_source": ["employment_income"],
        "tax_id": "666-55-4321",
        "tax_id_type": "USA_SSN",
    }
    contact = {
        "email_address": "john.doe@example.com",
        "phone_number": "+15556667788",
        "street_address": ["123 Main Street"],
        "city": "San Mateo",
        "state": "CA",
        "postal_code": "94401",
    }
    disclosures = {
        "is_control_person": False,
        "is_affiliated_exchange_or_finra": False,
        "is_politically_exposed": False,
        "immediate_family_exposed": False,
    }
    request = CreateAccountRequest(
        account_type="custodial",
        contact=contact,
        identity=identity,
        disclosures=disclosures,
        agreements=[
            {
                "agreement": "customer_agreement",
                "signed_at": "2020-09-11T18:13:44Z",
                "ip_address": "185.13.21.99",
            }
        ],
        minor_identity=minor,
    )

    sent = request.to_request_fields()["minor_identity"]
    assert sent["given_name"] == "Jamie"
    assert sent["email"] == "jamie.doe@example.com"
    assert sent["tax_id_type"] == TaxIdType.USA_SSN

    contact_without_phone = dict(contact)
    del contact_without_phone["phone_number"]
    without_phone = CreateAccountRequest(
        account_type="custodial",
        contact=contact_without_phone,
        identity=identity,
        disclosures=disclosures,
        agreements=[
            {
                "agreement": "customer_agreement",
                "signed_at": "2020-09-11T18:13:44Z",
                "ip_address": "185.13.21.99",
            }
        ],
        minor_identity=minor,
    )
    assert "phone_number" not in without_phone.to_request_fields()["contact"]


def test_ach_relationship_can_include_instant_and_processor_token():
    request = CreateACHRelationshipRequest(
        account_owner_name="sample",
        bank_account_type=BankAccountType.CHECKING,
        bank_account_number="sample",
        bank_routing_number="sample",
        instant=False,
        processor_token="processor-token",
    )

    fields = request.to_request_fields()
    assert fields["instant"] is False
    assert fields["processor_token"] == "processor-token"
    assert fields["bank_account_number"] == "sample"


def test_batch_journal_entry_sends_currency_qty_and_symbol():
    entry = BatchJournalRequestEntry(
        to_account=uuid4(),
        amount="10.00",
        currency="USD",
        qty="1",
        symbol="AAPL",
    )

    fields = entry.to_request_fields()
    assert fields["currency"] == "USD"
    assert fields["qty"] == "1"
    assert fields["symbol"] == "AAPL"
    assert fields["amount"] == "10.00"

    with pytest.raises(ValueError):
        BatchJournalRequestEntry(
            to_account=uuid4(),
            amount="10.00",
            qty=1.5,
        )


def test_create_bank_request_sends_intermediary_fields():
    request = CreateBankRequest(
        name="name",
        bank_code_type=IdentifierType.BIC,
        bank_code="123456789",
        account_number="123456789abc",
        country="United States",
        state_province="New York",
        postal_code="10036",
        city="Manhattan",
        street_address="Sixth Avenue & 42nd Street",
        extra_fields=BankAdditionalFields(
            intermediary_bank1_bic="AAAAUS33",
            intermediary_bank2_bic="BBBBUS33",
            intermediary_bank3_bic="CCCCUS33",
        ),
    )

    extra = request.to_request_fields()["extra_fields"]
    assert extra["intermediary_bank1_bic"] == "AAAAUS33"
    assert extra["intermediary_bank3_bic"] == "CCCCUS33"


def test_ach_transfer_sends_ira_distribution():
    request = CreateACHTransferRequest(
        relationship_id=uuid4(),
        amount="1.0",
        direction=TransferDirection.INCOMING,
        fee_payment_method="invoice",
        ira=TransferIRA(
            distribution_reason="normal",
            tax_withholding={"fed_pct": "10.25", "state_pct": "8.25"},
            tax_year="2024",
        ),
    )

    fields = request.to_request_fields()
    assert "timing" not in fields
    assert fields["ira"]["distribution_reason"] == "normal"
    assert fields["ira"]["tax_withholding"]["fed_pct"] == "10.25"
    assert fields["ira"]["tax_year"] == "2024"
    assert fields["transfer_type"] == TransferType.ACH


def test_ach_transfer_sends_ira_contribution():
    request = CreateACHTransferRequest(
        relationship_id=uuid4(),
        amount="100",
        direction=TransferDirection.INCOMING,
        ira=TransferIRA(tax_year="2026"),
    )

    fields = request.to_request_fields()
    assert fields["transfer_type"] == TransferType.ACH
    assert fields["ira"] == {"tax_year": "2026"}
    assert "timing" not in fields


def test_wire_transfer_sends_ira_distribution():
    request = CreateBankTransferRequest(
        bank_id=uuid4(),
        amount="1000",
        direction=TransferDirection.OUTGOING,
        fee_payment_method="invoice",
        ira=TransferIRA(
            distribution_reason="normal",
            tax_withholding={"fed_pct": "10", "state_pct": "5"},
        ),
    )

    fields = request.to_request_fields()
    assert fields["transfer_type"] == TransferType.WIRE
    assert fields["direction"] == TransferDirection.OUTGOING
    assert fields["ira"]["distribution_reason"] == "normal"
    assert fields["ira"]["tax_withholding"]["fed_pct"] == "10"
    assert fields["ira"]["tax_withholding"]["state_pct"] == "5"
    assert "timing" not in fields


def test_update_account_request_sends_extended_fields():
    request = UpdateAccountRequest(
        agreements=[
            {
                "agreement": AgreementType.CUSTOMER_AGREEMENT,
                "ip_address": "185.13.21.99",
                "signed_at": "2019-09-11T18:09:33Z",
                "revision": "sample",
            }
        ],
        allow_instant_ach=False,
        beneficiaries=[
            {
                "given_name": "John",
                "middle_name": "P",
                "family_name": "Smith",
                "date_of_birth": "1970-01-01",
                "tax_id": "xxx-xx-xxxx",
                "tax_id_type": "USA_SSN",
                "relationship": "spouse",
                "type": "primary",
                "share_pct": "100",
            }
        ],
        cash_interest={"USD": {"apr_tier_name": "gold", "status": "ACTIVE"}},
        enabled_assets=[AssetClass.US_EQUITY, AssetClass.CRYPTO],
        fpsl={"US": {"status": "ACTIVE", "tier_id": str(uuid4())}},
        identity=UpdatableIdentity(
            country_of_birth="AUS",
            country_of_citizenship="AUS",
            country_of_tax_residence="USA",
            date_of_birth="1990-01-01",
            tax_id="666-55-4321",
            tax_id_type=TaxIdType.USA_SSN,
        ),
    )

    fields = request.to_request_fields()
    assert fields["allow_instant_ach"] is False
    assert fields["agreements"][0]["agreement"] == AgreementType.CUSTOMER_AGREEMENT
    assert fields["beneficiaries"][0]["share_pct"] == "100"
    assert fields["cash_interest"]["USD"]["apr_tier_name"] == "gold"
    assert fields["enabled_assets"] == [AssetClass.US_EQUITY, AssetClass.CRYPTO]
    assert fields["fpsl"]["US"]["status"] == "ACTIVE"
    identity = fields["identity"]
    assert identity["country_of_birth"] == "AUS"
    assert identity["country_of_citizenship"] == "AUS"
    assert identity["country_of_tax_residence"] == "USA"
    assert identity["date_of_birth"] == "1990-01-01"
    assert identity["tax_id"] == "666-55-4321"
    assert identity["tax_id_type"] == TaxIdType.USA_SSN
    assert "primary_account_holder_id" not in fields
    assert "is_discretionary" not in UpdatableDisclosures.model_fields
    disclosures = UpdatableDisclosures(
        is_control_person=False,
        is_affiliated_exchange_or_finra=False,
        is_politically_exposed=False,
        immediate_family_exposed=False,
        is_discretionary=True,
    )
    sent_disclosures = UpdateAccountRequest(disclosures=disclosures).to_request_fields()
    assert "is_discretionary" not in sent_disclosures["disclosures"]


def test_account_extended_keeps_documented_fields():
    account_id = uuid4()
    document_id = uuid4()
    payload = {
        "id": str(account_id),
        "account_number": "601842165",
        "account_type": "custodial",
        "status": "ACTIVE",
        "currency": "USD",
        "last_equity": "40645.13",
        "created_at": "2022-01-21T21:25:26.583576Z",
        "account_name": "Jamie Doe",
        "primary_account_holder_id": str(uuid4()),
        "allow_instant_ach": True,
        "instant_ach_blocked": False,
        "custodial_account_type": "UGMA",
        "enabled_assets": ["us_equity"],
        "investment_objective": "growth",
        "investment_time_horizon": "more_than_10_years",
        "liquidity_needs": "does_not_matter",
        "risk_tolerance": "moderate",
        "beneficiaries": [
            {
                "given_name": "Jane",
                "middle_name": "P",
                "family_name": "Doe",
                "date_of_birth": "1970-01-01",
                "tax_id": "xxx-xx-xxxx",
                "tax_id_type": "USA_SSN",
                "relationship": "spouse",
                "type": "primary",
                "share_pct": "100",
            }
        ],
        "cash_interest": {"USD": {"apr_tier_name": "gold", "status": "ACTIVE"}},
        "fpsl": {"US": {"status": "ACTIVE", "tier_id": str(uuid4())}},
        "usd": {"last_equity": "123.45"},
        "trading_configurations": {
            "fractional_trading": True,
            "max_margin_multiplier": "1",
            "trade_confirm_email": "none",
        },
        "disclosures": {
            "is_control_person": False,
            "is_affiliated_exchange_or_finra": False,
            "is_politically_exposed": False,
            "immediate_family_exposed": False,
            "is_discretionary": True,
        },
        "documents": [
            {
                "id": str(document_id),
                "document_type": "identity_verification",
                "created_at": "2019-09-30T23:55:31.185998Z",
            }
        ],
        "minor_identity": {
            "given_name": "Jamie",
            "family_name": "Doe",
            "date_of_birth": "2012-04-05",
            "tax_id_type": "USA_SSN",
            "country_of_tax_residence": "USA",
            "state": "CA",
            "email": "jamie.doe@example.com",
        },
    }

    account = AccountExtended(**payload)

    assert Disclosures in get_args(Account.model_fields["disclosures"].annotation)
    assert AccountDisclosures in get_args(
        AccountExtended.model_fields["disclosures"].annotation
    )
    assert account.account_name == "Jamie Doe"
    assert account.allow_instant_ach is True
    assert account.beneficiaries[0].family_name == "Doe"
    assert account.cash_interest.USD.status == "ACTIVE"
    assert account.custodial_account_type == "UGMA"
    assert account.disclosures.is_discretionary is True
    assert account.documents[0].created_at is not None
    assert account.enabled_assets == [AssetClass.US_EQUITY]
    assert account.fpsl.US.status == "ACTIVE"
    assert account.instant_ach_blocked is False
    assert account.investment_objective == "growth"
    assert account.investment_time_horizon == "more_than_10_years"
    assert account.liquidity_needs == "does_not_matter"
    assert account.minor_identity.email == "jamie.doe@example.com"
    assert account.primary_account_holder_id == UUID(
        payload["primary_account_holder_id"]
    )
    assert account.risk_tolerance == "moderate"
    assert account.trading_configurations.trade_confirm_email == "none"
    assert account.usd.last_equity == "123.45"


def test_transfer_keeps_ira_details():
    transfer = Transfer(
        id=uuid4(),
        account_id=uuid4(),
        created_at="2021-05-05T07:55:31.190788Z",
        amount="498",
        type="ach",
        status="COMPLETE",
        direction="INCOMING",
        ira={
            "distribution_reason": "normal",
            "fed_withholding_amount": "102.5",
            "fed_withholding_pct": "10.25",
            "state_withholding_amount": "97.5",
            "state_withholding_pct": "9.75",
            "tax_year": "2024",
        },
    )

    assert transfer.ira.fed_withholding_pct == "10.25"
    assert transfer.ira.tax_year == "2024"
