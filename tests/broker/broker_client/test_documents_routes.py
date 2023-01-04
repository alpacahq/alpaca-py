from datetime import datetime, date
from ipaddress import IPv4Address
import os.path
import tempfile
from typing import List
from alpaca.broker.models.documents import W8BenDocument

import pytest

from alpaca.broker.requests import UploadDocumentRequest, UploadW8BenDocumentRequest
from alpaca.broker.client import BrokerClient
from alpaca.common.constants import BROKER_DOCUMENT_UPLOAD_LIMIT
from alpaca.broker.enums import (
    TradeDocumentType,
    UploadDocumentMimeType,
    DocumentType,
)
from alpaca.broker.models import TradeDocument
from alpaca.broker.requests import GetTradeDocumentsRequest
from alpaca.common.enums import BaseURL


def test_get_trade_documents_for_account(reqmock, client: BrokerClient):
    account_id = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"

    reqmock.get(
        BaseURL.BROKER_SANDBOX + f"/v1/accounts/{account_id}/documents",
        text="""
        [
          {
            "id": "1b560b0f-9efd-44b4-8004-dfd520c7cdc0",
            "name": "",
            "type": "account_statement",
            "sub_type": "",
            "date": "2022-02-27"
          },
          {
            "id": "c2619f26-4cb3-4ef2-8c4d-660dc561b42d",
            "name": "",
            "type": "account_statement",
            "sub_type": "",
            "date": "2022-02-28"
          }
        ]
        """,
    )

    start = "2022-02-27"
    end = "2022-02-28"

    documents = client.get_trade_documents_for_account(
        account_id=account_id,
        documents_filter=GetTradeDocumentsRequest(
            start=start, end=end, type=TradeDocumentType.ACCOUNT_STATEMENT
        ),
    )

    assert reqmock.called_once
    assert isinstance(documents, List)
    assert isinstance(documents[0], TradeDocument)

    assert reqmock.request_history[0].qs == {
        "start": [start],
        "end": [end],
        "type": [TradeDocumentType.ACCOUNT_STATEMENT],
    }


def test_get_trade_documents_for_account_validates_account_id(
    reqmock,
    client: BrokerClient,
):
    with pytest.raises(ValueError):
        client.get_trade_documents_for_account(
            account_id="not a uuid", documents_filter=GetTradeDocumentsRequest()
        )


def test_upload_documents_to_account(reqmock, client: BrokerClient):
    account_id = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"
    reqmock.post(
        BaseURL.BROKER_SANDBOX + f"/v1/accounts/{account_id}/documents/upload",
        json={},
        status_code=202,
    )

    client.upload_documents_to_account(
        account_id=account_id,
        document_data=[
            UploadDocumentRequest(
                document_type=DocumentType.ACCOUNT_APPROVAL_LETTER,
                content="fake base64",
                mime_type=UploadDocumentMimeType.PDF,
            )
        ],
    )

    assert reqmock.called_once

    # TODO: Add a custom reqmock matcher to ensure format of request rather than this static string check
    assert (
        reqmock.request_history[0].text
        == '[{"document_type": "account_approval_letter", "content": "fake base64", "mime_type": "application/pdf"}]'
    )

def test_upload_documents_to_account(reqmock, client: BrokerClient):
    account_id = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"
    document_date = date(2023, 1, 3)
    date_of_birth = date(1999, 1,23)
    timestamp = datetime.now()
    ip_address=IPv4Address(address="189.147.173.150")

    reqmock.post(
        BaseURL.BROKER_SANDBOX + f"/v1/accounts/{account_id}/documents/upload",
        json={},
        status_code=202,
    )

    client.upload_documents_to_account(
        account_id=account_id,
        document_data=[
            UploadW8BenDocumentRequest(
                content_data=W8BenDocument(
                    country_citizen="Mexico",
                    date=document_date,
                    date_of_birth=date_of_birth,
                    full_name="Some Name",
                    ip_address=ip_address,
                    permanent_address_city_state="Springfield",
                    permanent_address_country="US",
                    permanent_address_street="742 de Evergreen Terrace",
                    revision="10-2021",
                    signer_full_name="Some Name",
                    timestamp=timestamp,
                    foreign_tax_id="CXXC990123ME2",
                ),
            )
        ],
    )

    assert reqmock.called_once
    response = reqmock.request_history[0].json()[0]
    document_type = response['document_type']
    document_sub_type = response['document_sub_type']
    mime_type = response['mime_type']
    content_data = response['content_data']

    assert ( document_type == 'w8ben')
    assert ( document_sub_type == 'Form W-8BEN')
    assert ( mime_type == 'application/json')
    assert ( content_data['date'] == str(document_date))
    assert ( content_data['date_of_birth'] == str(date_of_birth))
    assert ( content_data['timestamp'] == timestamp.isoformat("T") + "Z")

def test_upload_documents_to_account_validates_limit(reqmock, client: BrokerClient):
    with pytest.raises(ValueError) as e:
        client.upload_documents_to_account(
            account_id="2a87c088-ffb6-472b-a4a3-cd9305c8605c",
            document_data=list(range(0, 11)),
        )

    assert not reqmock.called
    assert f"document_data cannot be longer than {BROKER_DOCUMENT_UPLOAD_LIMIT}" in str(
        e.value
    )


def test_upload_documents_to_account_validates_account_id(
    reqmock,
    client: BrokerClient,
):
    with pytest.raises(ValueError):
        client.upload_documents_to_account(
            account_id="not a uuid", document_data=list(range(1, 10))
        )

    assert not reqmock.called


def test_get_trade_document_for_account_by_id_validates_uuids(
    reqmock,
    client: BrokerClient,
):
    uuid = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"

    with pytest.raises(ValueError):
        client.get_trade_document_for_account_by_id(
            account_id=uuid, document_id="not a uuid"
        )

    with pytest.raises(ValueError):
        client.get_trade_document_for_account_by_id(
            account_id="not a uuid",
            document_id=uuid,
        )


def test_get_trade_document_for_account_by_id(reqmock, client: BrokerClient):
    account_id = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"
    document_id = "2a87c089-ffb6-472b-a4a3-cd9305c8605d"

    reqmock.get(
        BaseURL.BROKER_SANDBOX + f"/v1/accounts/{account_id}/documents/{document_id}",
        text="""
        {
          "id": "1b560b0f-9efd-44b4-8004-dfd520c7cdc0",
          "name": "",
          "type": "account_statement",
          "sub_type": "",
          "date": "2022-02-28"
        }
        """,
    )

    result = client.get_trade_document_for_account_by_id(
        account_id=account_id,
        document_id=document_id,
    )

    assert reqmock.called_once
    assert isinstance(result, TradeDocument)


def test_download_trade_document_for_account_by_id(reqmock, client: BrokerClient):
    """
    High level steps for how to do this test:
      * make a tempdir as with for auto delete
      * get a tempfile name in said tempdir
      * mock out main api request that returns a fake url
      * mock out fake url with fake data
      * check tempfile to ensure size is as expected
        * this could technically have issues with different encodings n such
        * maybe just read back out the data to ensure it's the same

    going to keep this docblock here to show thought process/possible downsides for future ref if this test proves
    too flakey
    """
    account_id = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"
    document_id = "2a87c089-ffb6-472b-a4a3-cd9305c8605d"
    fake_dl_url = f"https://fake-dl.com/{document_id}"
    fake_dl_text = """
    here is
    some fake
    text
    """

    reqmock.get(
        BaseURL.BROKER_SANDBOX
        + f"/v1/accounts/{account_id}/documents/{document_id}/download",
        status_code=301,
        headers={"Location": fake_dl_url},
        text=f"""
        <a href="{fake_dl_url}">
          Moved Permanently
        </a>.
        """,
    )

    reqmock.get(fake_dl_url, text=fake_dl_text)

    with tempfile.TemporaryDirectory() as tempdir:
        tempname = os.path.join(tempdir, "test.pdf")
        print(tempname)

        client.download_trade_document_for_account_by_id(
            account_id=account_id, document_id=document_id, file_path=tempname
        )

        assert reqmock.call_count == 2

        assert os.path.isfile(tempname)

        with open(tempname, mode="r") as file:
            assert file.read() == fake_dl_text


def test_download_trade_document_for_account_by_id_validates_uuids(
    reqmock, client: BrokerClient
):
    uuid = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"

    with pytest.raises(ValueError):
        client.download_trade_document_for_account_by_id(
            account_id=uuid,
            document_id="not a uuid",
            file_path="",
        )

    with pytest.raises(ValueError):
        client.download_trade_document_for_account_by_id(
            account_id="not a uuid",
            document_id=uuid,
            file_path="",
        )
