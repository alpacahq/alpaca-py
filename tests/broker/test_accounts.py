import pytest
import requests_mock

from alpaca.common import APIError
from alpaca.broker.client import BrokerClient
from alpaca.broker.models import Account, AccountCreationRequest

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


def test_create_account(client: BrokerClient):
    created_id = "0d969814-40d6-4b2b-99ac-2e37427f1ad2"

    with requests_mock.mock() as m:
        m.post(
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

        assert m.called
        assert type(returned_account) == Account
        assert returned_account.id == created_id


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

    assert type(account) == Account
    assert account.id == account_id


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


def test_get_account_validates_non_uuid_str(client: BrokerClient):
    with pytest.raises(ValueError):
        client.get_account_by_id("not a valid uuid")

    with pytest.raises(ValueError):
        client.get_account_by_id(4)
