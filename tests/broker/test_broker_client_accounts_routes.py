from uuid import UUID

import pytest
import requests_mock

from alpaca.broker.enums import AccountEntities
from alpaca.common import APIError
from alpaca.broker.client import BrokerClient
from alpaca.broker.models import (
    Account,
    AccountCreationRequest,
    AccountUpdateRequest,
    Contact,
    Identity,
    ListAccountsRequest,
    UpdatableContact,
    UpdatableTrustedContact,
    UpdatableIdentity,
    UpdatableDisclosures,
)
from alpaca.common.enums import BaseURL, Sort

from factories import common as factory


@pytest.fixture
def reqmock():
    with requests_mock.Mocker() as m:
        yield m


@pytest.fixture
def client():
    client = BrokerClient("key-id", "secret-key")
    return client


@pytest.fixture
def raw_client():
    raw_client = BrokerClient("key-id", "secret-key", raw_data=True)
    return raw_client


def test_create_account(reqmock, client: BrokerClient):
    created_id = "0d969814-40d6-4b2b-99ac-2e37427f1ad2"

    reqmock.post(
        "https://broker-api.sandbox.alpaca.markets/v1/accounts",
        text="""
        {
          "id": "0d969814-40d6-4b2b-99ac-2e37427f1ad2",
          "account_number": "682389557",
          "status": "SUBMITTED",
          "crypto_status": "INACTIVE",
          "currency": "USD",
          "last_equity": "0",
          "created_at": "2022-04-12T17:24:31.30283Z",
          "contact": {
            "email_address": "cool_alpaca@example.com",
            "phone_number": "555-666-7788",
            "street_address": [
              "20 N San Mateo Dr"
            ],
            "unit": "Apt 1A",
            "city": "San Mateo",
            "state": "CA",
            "postal_code": "94401"
          },
          "identity": {
            "given_name": "John",
            "family_name": "Doe",
            "middle_name": "Smith",
            "date_of_birth": "1990-01-01",
            "tax_id_type": "USA_SSN",
            "country_of_citizenship": "USA",
            "country_of_birth": "USA",
            "country_of_tax_residence": "USA",
            "funding_source": [
              "employment_income"
            ],
            "visa_type": null,
            "visa_expiration_date": null,
            "date_of_departure_from_usa": null,
            "permanent_resident": null
          },
          "disclosures": {
            "is_control_person": false,
            "is_affiliated_exchange_or_finra": false,
            "is_politically_exposed": false,
            "immediate_family_exposed": false,
            "is_discretionary": false
          },
          "agreements": [
            {
              "agreement": "margin_agreement",
              "signed_at": "2020-09-11T18:09:33Z",
              "ip_address": "185.13.21.99",
              "revision": "16.2021.05"
            },
            {
              "agreement": "account_agreement",
              "signed_at": "2020-09-11T18:13:44Z",
              "ip_address": "185.13.21.99",
              "revision": "16.2021.05"
            },
            {
              "agreement": "customer_agreement",
              "signed_at": "2020-09-11T18:13:44Z",
              "ip_address": "185.13.21.99",
              "revision": "16.2021.05"
            },
            {
              "agreement": "crypto_agreement",
              "signed_at": "2020-09-11T18:13:44Z",
              "ip_address": "185.13.21.99",
              "revision": "04.2021.10"
            }
          ],
          "trusted_contact": {
            "given_name": "Jane",
            "family_name": "Doe",
            "email_address": "jane.doe@example.com"
          },
          "account_type": "trading",
          "trading_configurations": null
        }
        """,
    )

    create_data = AccountCreationRequest(
        agreements=factory.create_dummy_agreements(),
        contact=factory.create_dummy_contact(),
        disclosures=factory.create_dummy_disclosures(),
        documents=factory.create_dummy_documents(),
        identity=factory.create_dummy_identity(),
        trusted_contact=factory.create_dummy_trusted_contact(),
    )

    returned_account = client.create_account(create_data)

    assert reqmock.called_once
    assert type(returned_account) == Account
    assert returned_account.id == UUID(created_id)


def test_get_account(reqmock, client: BrokerClient):
    account_id = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"

    reqmock.get(
        f"https://broker-api.sandbox.alpaca.markets/v1/accounts/{account_id}",
        text="""
        {
          "id": "2a87c088-ffb6-472b-a4a3-cd9305c8605c",
          "account_number": "601865070",
          "status": "ACTIVE",
          "crypto_status": "INACTIVE",
          "currency": "USD",
          "last_equity": "47604.17306484226",
          "created_at": "2022-01-21T21:25:26.470131Z",
          "contact": {
            "email_address": "agitated_golick_69906574@example.com",
            "phone_number": "386-555-3557",
            "street_address": [
              "20 N San Mateo Dr"
            ],
            "city": "San Mateo",
            "state": "CA",
            "postal_code": "94401"
          },
          "identity": {
            "given_name": "Agitated",
            "family_name": "Golick",
            "date_of_birth": "1970-01-01",
            "tax_id_type": "USA_SSN",
            "country_of_citizenship": "USA",
            "country_of_birth": "USA",
            "country_of_tax_residence": "USA",
            "funding_source": [
              "employment_income"
            ],
            "visa_type": null,
            "visa_expiration_date": null,
            "date_of_departure_from_usa": null,
            "permanent_resident": null
          },
          "disclosures": {
            "is_control_person": false,
            "is_affiliated_exchange_or_finra": false,
            "is_politically_exposed": false,
            "immediate_family_exposed": false,
            "is_discretionary": false
          },
          "agreements": [
            {
              "agreement": "margin_agreement",
              "signed_at": "2022-01-21T21:25:26.466094194Z",
              "ip_address": "127.0.0.1",
              "revision": null
            },
            {
              "agreement": "customer_agreement",
              "signed_at": "2022-01-21T21:25:26.466094194Z",
              "ip_address": "127.0.0.1",
              "revision": null
            },
            {
              "agreement": "account_agreement",
              "signed_at": "2022-01-21T21:25:26.466094194Z",
              "ip_address": "127.0.0.1",
              "revision": null
            }
          ],
          "documents": [
            {
              "document_type": "identity_verification",
              "document_sub_type": "passport",
              "id": "bb6de14c-9393-4b6c-8e93-c6724ac7b703",
              "content": "https://example.com/not-a-real-url",
              "created_at": "2022-01-21T21:25:28.189455Z"
            }
          ],
          "trusted_contact": {
            "given_name": "Jane",
            "family_name": "Doe",
            "email_address": "agitated_golick_69906574@example.com"
          },
          "account_type": "trading",
          "trading_configurations": null
        }
            """,
    )

    account = client.get_account_by_id(account_id)

    assert reqmock.called_once
    assert type(account) == Account
    assert account.id == UUID(account_id)


def test_get_account_account_not_found(reqmock, client: BrokerClient):
    account_id = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"
    status_code = 401

    # Api returns an unauthorized if you try to ask for a uuid thats not one of your accounts
    reqmock.get(
        f"https://broker-api.sandbox.alpaca.markets/v1/accounts/{account_id}",
        status_code=status_code,
        text="""
        {
          "code": 40110000,
          "message": "request is not authorized"
        }
        """,
    )

    with pytest.raises(APIError) as error:
        client.get_account_by_id(account_id)

    assert error.value.status_code == status_code


def test_get_account_validates_account_id(reqmock, client: BrokerClient):
    with pytest.raises(ValueError):
        client.get_account_by_id("not a valid uuid")

    with pytest.raises(ValueError):
        client.get_account_by_id(4)


def test_update_account(reqmock, client: BrokerClient):
    account_id = "0d969814-40d6-4b2b-99ac-2e37427f1ad2"
    family_name = "New Name"
    identity = factory.create_dummy_identity()

    identity.family_name = family_name

    update_data = AccountUpdateRequest(identity=identity)

    reqmock.patch(
        f"https://broker-api.sandbox.alpaca.markets/v1/accounts/{account_id}",
        text="""
        {
          "id": "0d969814-40d6-4b2b-99ac-2e37427f1ad2",
          "account_number": "682389557",
          "status": "ACTIVE",
          "kyc_results": {
            "reject": {},
            "accept": {},
            "indeterminate": {},
            "summary": "pass"
          },
          "currency": "USD",
          "last_equity": "0",
          "created_at": "2022-04-12T17:24:31.30283Z",
          "contact": {
            "email_address": "cool_alpaca@example.com",
            "phone_number": "555-666-7788",
            "street_address": [
              "20 N San Mateo Dr"
            ],
            "unit": "Apt 1A",
            "city": "San Mateo",
            "state": "CA",
            "postal_code": "94401"
          },
          "identity": {
            "given_name": "John",
            "family_name": "New Name",
            "middle_name": "Smith",
            "date_of_birth": "1990-01-01",
            "tax_id_type": "USA_SSN",
            "country_of_citizenship": "USA",
            "country_of_birth": "USA",
            "country_of_tax_residence": "USA",
            "funding_source": [
              "employment_income"
            ],
            "visa_type": null,
            "visa_expiration_date": null,
            "date_of_departure_from_usa": null,
            "permanent_resident": null
          },
          "disclosures": {
            "is_control_person": false,
            "is_affiliated_exchange_or_finra": false,
            "is_politically_exposed": false,
            "immediate_family_exposed": false,
            "is_discretionary": false
          },
          "agreements": [
            {
              "agreement": "margin_agreement",
              "signed_at": "2020-09-11T18:09:33Z",
              "ip_address": "185.13.21.99",
              "revision": "16.2021.05"
            },
            {
              "agreement": "account_agreement",
              "signed_at": "2020-09-11T18:13:44Z",
              "ip_address": "185.13.21.99",
              "revision": "16.2021.05"
            },
            {
              "agreement": "customer_agreement",
              "signed_at": "2020-09-11T18:13:44Z",
              "ip_address": "185.13.21.99",
              "revision": "16.2021.05"
            },
            {
              "agreement": "crypto_agreement",
              "signed_at": "2020-09-11T18:13:44Z",
              "ip_address": "185.13.21.99",
              "revision": "04.2021.10"
            }
          ],
          "documents": [
            {
              "document_type": "identity_verification",
              "document_sub_type": "passport",
              "id": "6458a6f5-0cd1-4206-a240-2666dd7089a8",
              "content": "https://s3.amazonaws.com/stg.alpaca.markets/documents/accounts/0d969814-40d6-4b2b-99ac-2e37427f1ad2/544869c3-483e-4844-9de8-33166e04acdf.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAJLDF4SCWSL6HUQKA%2F20220413%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20220413T182315Z&X-Amz-Expires=900&X-Amz-SignedHeaders=host&X-Amz-Signature=9d2b6a38329a3f35723d018983fb9783a6b39d9a59f0ce414bcfdfde858119de",
              "created_at": "2022-04-12T17:24:32.282494Z"
            }
          ],
          "trusted_contact": {
            "given_name": "Jane",
            "family_name": "Doe",
            "email_address": "jane.doe@example.com"
          },
          "account_type": "trading",
          "trading_configurations": null
        }
        """,
    )

    account = client.update_account(account_id, update_data)

    assert reqmock.called_once
    assert type(account) == Account
    assert account.id == UUID(account_id)
    assert account.identity.family_name == family_name


def test_update_account_validates_account_id(reqmock, client: BrokerClient):
    # dummy update request just to test param parsing
    update_data = AccountUpdateRequest()

    with pytest.raises(ValueError):
        client.update_account("not a uuid", update_data)

    with pytest.raises(ValueError):
        client.update_account(4, update_data)


def test_update_account_validates_non_empty_request(reqmock, client: BrokerClient):
    account_id = "0d969814-40d6-4b2b-99ac-2e37427f1ad2"
    update_data = AccountUpdateRequest(
        identity=UpdatableIdentity(),
        disclosures=UpdatableDisclosures(),
        contact=UpdatableContact(),
        trusted_contact=UpdatableTrustedContact(),
    )

    with pytest.raises(ValueError) as e:
        client.update_account(account_id, update_data)

    assert str(e.value) == "update_data must contain at least 1 field to change"


def test_delete_account(reqmock, client: BrokerClient):
    account_id = "0d969814-40d6-4b2b-99ac-2e37427f1ad2"

    reqmock.delete(
        f"https://broker-api.sandbox.alpaca.markets/v1/accounts/{account_id}",
        status_code=204,
    )

    assert client.delete_account(account_id) is None
    assert reqmock.called_once


def test_delete_account_validates_account_id(reqmock, client: BrokerClient):
    with pytest.raises(ValueError):
        client.delete_account("not a uuid")

    with pytest.raises(ValueError):
        client.delete_account(4)


def test_list_accounts_no_params(reqmock, client: BrokerClient):
    reqmock.get(
        BaseURL.BROKER_SANDBOX + "/v1/accounts",
        text="""
        [
          {
            "id": "5fc0795e-1f16-40cc-aa90-ede67c39d7a9",
            "account_number": "684486106",
            "status": "ACTIVE",
            "crypto_status": "ACTIVE",
            "kyc_results": {
              "reject": {},
              "accept": {},
              "indeterminate": {},
              "summary": "pass"
            },
            "currency": "USD",
            "last_equity": "0",
            "created_at": "2022-04-14T15:51:14.523349Z",
            "account_type": "trading"
          },
          {
            "id": "0d969814-40d6-4b2b-99ac-2e37427f1ad2",
            "account_number": "682389557",
            "status": "ACTIVE",
            "crypto_status": "ACTIVE",
            "kyc_results": {
              "reject": {},
              "accept": {},
              "indeterminate": {},
              "summary": "pass"
            },
            "currency": "USD",
            "last_equity": "0",
            "created_at": "2022-04-12T17:24:31.30283Z",
            "account_type": "trading"
          }
        ]
        """,
    )

    accounts = client.list_accounts()

    assert reqmock.called_once

    request = reqmock.request_history[0]

    assert request.method == "GET"
    assert request.qs == {}

    assert len(accounts) == 2

    for account in accounts:
        assert type(account) == Account

        # assert the optional fields we didn't request are None
        assert account.identity is None
        assert account.contact is None
        assert account.disclosures is None
        assert account.documents is None
        assert account.trusted_contact is None
        assert account.agreements is None


def test_list_accounts_parses_entities_if_present(reqmock, client: BrokerClient):
    reqmock.get(
        BaseURL.BROKER_SANDBOX + "/v1/accounts",
        text="""
        [
          {
            "id": "5fc0795e-1f16-40cc-aa90-ede67c39d7a9",
            "account_number": "684486106",
            "status": "ACTIVE",
            "crypto_status": "ACTIVE",
            "kyc_results": {
              "reject": {},
              "accept": {},
              "indeterminate": {},
              "summary": "pass"
            },
            "currency": "USD",
            "last_equity": "0",
            "created_at": "2022-04-14T15:51:14.523349Z",
            "contact": {
              "email_address": "test_dummy-1@example.com",
              "phone_number": "555-666-7788",
              "street_address": [
                "20 N San Mateo Dr"
              ],
              "unit": "Apt 1A",
              "city": "San Mateo",
              "state": "CA",
              "postal_code": "94401"
            },
            "identity": {
              "given_name": "John",
              "family_name": "Doe",
              "middle_name": "Smith",
              "date_of_birth": "1990-01-01",
              "tax_id_type": "USA_SSN",
              "country_of_citizenship": "USA",
              "country_of_birth": "USA",
              "country_of_tax_residence": "USA",
              "funding_source": null,
              "visa_type": null,
              "visa_expiration_date": null,
              "date_of_departure_from_usa": null,
              "permanent_resident": null
            },
            "account_type": "trading"
          },
          {
            "id": "0d969814-40d6-4b2b-99ac-2e37427f1ad2",
            "account_number": "682389557",
            "status": "ACTIVE",
            "crypto_status": "ACTIVE",
            "kyc_results": {
              "reject": {},
              "accept": {},
              "indeterminate": {},
              "summary": "pass"
            },
            "currency": "USD",
            "last_equity": "0",
            "created_at": "2022-04-12T17:24:31.30283Z",
            "contact": {
              "email_address": "cool_alpaca@example.com",
              "phone_number": "555-666-7788",
              "street_address": [
                "20 N San Mateo Dr"
              ],
              "unit": "Apt 1A",
              "city": "San Mateo",
              "state": "CA",
              "postal_code": "94401"
            },
            "identity": {
              "given_name": "John",
              "family_name": "Doe",
              "middle_name": "Smith",
              "date_of_birth": "1990-01-01",
              "tax_id_type": "USA_SSN",
              "country_of_citizenship": "USA",
              "country_of_birth": "USA",
              "country_of_tax_residence": "USA",
              "funding_source": [
                "employment_income"
              ],
              "visa_type": null,
              "visa_expiration_date": null,
              "date_of_departure_from_usa": null,
              "permanent_resident": null
            },
            "account_type": "trading"
          }
        ]
        """,
    )

    params = ListAccountsRequest(
        entities=[AccountEntities.IDENTITY, AccountEntities.CONTACT]
    )

    accounts = client.list_accounts(params)

    assert reqmock.called_once

    request = reqmock.request_history[0]

    assert request.qs == {"sort": ["desc"], "entities": ["identity,contact"]}
    assert len(accounts) == 2

    for account in accounts:
        assert type(account) == Account

        # assert the optional fields we didn't request are None and the ones we did request are set
        assert type(account.identity) == Identity
        assert type(account.contact) == Contact
        assert account.disclosures is None
        assert account.documents is None
        assert account.trusted_contact is None
        assert account.agreements is None
