from datetime import datetime

import pytest

from alpaca.broker import (
    UploadDocumentMimeType,
    UploadDocumentRequest,
    UploadDocumentSubType,
    UploadDocumentType,
    UploadW8BenDocumentRequest,
    W8BenDocument,
)
from alpaca.broker.models import (
    AccountDocument,
    AccountUpdateRequest,
    UpdatableTrustedContact,
    UpdatableContact,
    UpdatableIdentity,
    UpdatableDisclosures,
    GetAccountActivitiesRequest,
    GetTradeDocumentsRequest,
    TradeDocument,
)
from tests.broker.factories import create_dummy_w8ben_document


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
    req = AccountUpdateRequest(trusted_contact=UpdatableTrustedContact(given_name=name))

    result = req.to_request_fields()
    expected = {"trusted_contact": {"given_name": name}}

    assert expected == result
    assert {} == AccountUpdateRequest().to_request_fields()

    empty_req = AccountUpdateRequest(
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
            document_type=UploadDocumentType.W8BEN,
            content="",
            mime_type=UploadDocumentMimeType.JSON,
        )

    assert (
        "Error please use the UploadW8BenDocument class for uploading W8BEN documents"
        in str(e.value)
    )

    with pytest.raises(ValueError) as e:
        UploadDocumentRequest(
            document_type=UploadDocumentType.ACCOUNT_APPROVAL_LETTER,
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
        val.document_type = UploadDocumentType.ACCOUNT_APPROVAL_LETTER

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
