from datetime import datetime

import pytest

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
