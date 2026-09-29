import warnings
from datetime import datetime

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
    AccountDocument,
    TradeDocument,
    TrustedContact,
)
from alpaca.broker.requests import (
    UpdateAccountRequest,
    UpdatableTrustedContact,
    UpdatableContact,
    UpdatableIdentity,
    UpdatableDisclosures,
    GetAccountActivitiesRequest,
    GetTradeDocumentsRequest,
    CreateBankRequest,
    CreateACHTransferRequest,
    CreateBankTransferRequest,
)
from alpaca.broker.enums import (
    IdentifierType,
    TransferType,
    TransferDirection,
    TransferTiming,
    JournalEntryType,
)
from alpaca.trading.enums import ActivityType
from tests.broker.factories import create_dummy_w8ben_document
from uuid import uuid4


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
        timing=TransferTiming.IMMEDIATE,
    )


def test_valid_bank_transfer_request():
    CreateBankTransferRequest(
        bank_id=uuid4(),
        amount="100.0",
        direction=TransferDirection.INCOMING,
        timing=TransferTiming.IMMEDIATE,
    )


def test_zero_transfer_amount():
    with pytest.raises(ValueError) as e:
        CreateACHTransferRequest(
            relationship_id=uuid4(),
            amount="0",
            direction=TransferDirection.INCOMING,
            timing=TransferTiming.IMMEDIATE,
        )

    assert "You must provide an amount > 0." in str(e.value)


def test_negative_transfer_amount():
    with pytest.raises(ValueError) as e:
        CreateACHTransferRequest(
            relationship_id=uuid4(),
            amount="-100.0",
            direction=TransferDirection.INCOMING,
            timing=TransferTiming.IMMEDIATE,
        )

    assert "You must provide an amount > 0." in str(e.value)


def test_ach_transfer_with_wire_transfer_type():
    with pytest.raises(ValueError) as e:
        CreateACHTransferRequest(
            relationship_id=uuid4(),
            amount="0",
            direction=TransferDirection.INCOMING,
            timing=TransferTiming.IMMEDIATE,
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
            timing=TransferTiming.IMMEDIATE,
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

    assert contact.street_address == ["20 N San Mateo Dr"]
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

    assert contact.street_address == ["20 N San Mateo Dr"]
    assert fields == {"trusted_contact": {"street_address": ["20 N San Mateo Dr"]}}


def test_updatable_trusted_contact_list_street_address_serializes_as_list():
    lines = ["20 N San Mateo Dr", "Apt 1A"]
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        contact = UpdatableTrustedContact(street_address=lines)
        fields = UpdateAccountRequest(trusted_contact=contact).to_request_fields()

    assert contact.street_address == lines
    assert fields == {"trusted_contact": {"street_address": lines}}


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

    assert account.trusted_contact.street_address == ["20 N San Mateo Dr"]
    assert accounts[0].trusted_contact.street_address == ["20 N San Mateo Dr"]


def test_trusted_contact_street_address_schema_uses_stored_list():
    string_schema = {"type": "string"}
    list_schema = {"items": {"type": "string"}, "type": "array"}
    null_schema = {"type": "null"}
    validation = TrustedContact.model_json_schema()["properties"]["street_address"]
    serialization = TypeAdapter(TrustedContact).json_schema(mode="serialization")[
        "properties"
    ]["street_address"]

    assert string_schema in validation["anyOf"]
    assert list_schema in validation["anyOf"]
    assert null_schema in validation["anyOf"]
    assert list_schema in serialization["anyOf"]
    assert null_schema in serialization["anyOf"]
    assert string_schema not in serialization["anyOf"]


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
