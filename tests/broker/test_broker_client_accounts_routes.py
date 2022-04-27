from typing import Iterator, List
from uuid import UUID
from datetime import datetime

import pytest
import requests_mock
from requests_mock import Mocker

from alpaca.broker.enums import AccountEntities
from alpaca.common import APIError
from alpaca.broker.client import BrokerClient, PaginationType
from alpaca.broker.models import (
    Account,
    AccountCreationRequest,
    AccountUpdateRequest,
    Contact,
    Identity,
    ListAccountsRequest,
    TradeAccount,
    UpdatableContact,
    UpdatableTrustedContact,
    UpdatableIdentity,
    UpdatableDisclosures,
    BaseActivity,
    GetAccountActivitiesRequest,
    NonTradeActivity,
    TradeActivity,
)
from alpaca.common.enums import BaseURL, Sort

from factories import common as factory


@pytest.fixture
def reqmock() -> Iterator[Mocker]:
    with requests_mock.Mocker() as m:
        yield m


@pytest.fixture
def client():
    client = BrokerClient(
        "key-id",
        "secret-key",
        sandbox=True,  # Expressly call out sandbox as true for correct urls in reqmock
    )
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


def test_get_trade_account_by_id(reqmock, client: BrokerClient):
    account_id = "5fc0795e-1f16-40cc-aa90-ede67c39d7a9"

    reqmock.get(
        BaseURL.BROKER_SANDBOX + f"/v1/trading/accounts/{account_id}/account",
        text="""
        {
          "id": "5fc0795e-1f16-40cc-aa90-ede67c39d7a9",
          "account_number": "684486106",
          "status": "ACTIVE",
          "crypto_status": "ACTIVE",
          "currency": "USD",
          "buying_power": "0",
          "regt_buying_power": "0",
          "daytrading_buying_power": "0",
          "non_marginable_buying_power": "0",
          "cash": "0",
          "cash_withdrawable": "0",
          "cash_transferable": "0",
          "accrued_fees": "0",
          "pending_transfer_out": "0",
          "pending_transfer_in": "0",
          "portfolio_value": "0",
          "pattern_day_trader": false,
          "trading_blocked": false,
          "transfers_blocked": false,
          "account_blocked": false,
          "created_at": "2022-04-14T15:51:14.523349Z",
          "trade_suspended_by_user": false,
          "multiplier": "1",
          "shorting_enabled": false,
          "equity": "0",
          "last_equity": "0",
          "long_market_value": "0",
          "short_market_value": "0",
          "initial_margin": "0",
          "maintenance_margin": "0",
          "last_maintenance_margin": "0",
          "sma": "0",
          "daytrade_count": 0,
          "previous_close": "2022-04-13T20:00:00-04:00",
          "last_long_market_value": "0",
          "last_short_market_value": "0",
          "last_cash": "0",
          "last_initial_margin": "0",
          "last_regt_buying_power": "0",
          "last_daytrading_buying_power": "0",
          "last_buying_power": "0",
          "last_daytrade_count": 0,
          "clearing_broker": "VELOX"
        }
              """,
    )

    account = client.get_trade_account_by_id(account_id)

    assert reqmock.called_once

    request = reqmock.request_history[0]
    assert request.method == "GET"
    assert request.qs == {}

    assert type(account) == TradeAccount
    assert account.id == UUID(account_id)


def test_get_trade_account_by_id_validates_account_id(reqmock, client: BrokerClient):
    with pytest.raises(ValueError) as e:
        client.get_trade_account_by_id("not a uuid")

    with pytest.raises(ValueError) as e:
        client.get_trade_account_by_id(4)

    assert "account_id must be a UUID or a UUID str" in str(e.value)


def setup_reqmock_for_paginated_account_activities_response(reqmock: Mocker):
    resp_one = """
    [
      {
        "id": "20220419000000000::fd84741b-59c5-4ddd-a303-69f70eb7753f",
        "account_id": "aba134b6-217d-4fd2-b460-e3c80bbfb9b4",
        "activity_type": "CSD",
        "date": "2022-04-19",
        "net_amount": "33324.35",
        "description": "",
        "status": "executed"
      },
      {
        "id": "20220419000000000::fb876acb-76b0-405c-8c7f-96a1c171ec5c",
        "account_id": "673272aa-2aa7-484b-9d5b-dd2bd19e9bca",
        "activity_type": "CSD",
        "date": "2022-04-19",
        "net_amount": "29161.91",
        "description": "",
        "status": "executed"
      },
      {
        "id": "20220304095318500::092cd749-b783-49cb-a36e-4d8666be201f",
        "account_id": "6e8cb861-e8b9-4278-8ed2-c8452535a165",
        "activity_type": "FILL",
        "transaction_time": "2022-03-04T14:53:18.500245Z",
        "type": "fill",
        "price": "2630.95",
        "qty": "9",
        "side": "buy",
        "symbol": "GOOGL",
        "leaves_qty": "0",
        "order_id": "b677e464-c2d0-4fdd-a4b1-8830b386aa50",
        "cum_qty": "10.177047834",
        "order_status": "filled"
      },
      {
        "id": "20220419000000000::f77b60bf-ea39-4551-a3d6-000548e6f11c",
        "account_id": "6188a8e4-4551-4c00-9387-fcb38ff8eef3",
        "activity_type": "CSD",
        "date": "2022-04-19",
        "net_amount": "45850.47",
        "description": "",
        "status": "executed"
      }
    ]
    """
    resp_two = """
    [
      {
        "id": "20220419000000000::ed22fc4d-897c-474b-876a-b492d40f83d2",
        "account_id": "e1bade5e-7988-4449-8791-86d47d721d19",
        "activity_type": "CSD",
        "date": "2022-04-19",
        "net_amount": "43864.18",
        "description": "",
        "status": "executed"
      },
      {
        "id": "20220419000000000::ec75b06d-1d29-4d1e-9143-c7e59aa842bc",
        "account_id": "a3f59eac-7c03-42b2-a336-d078b3671308",
        "activity_type": "CSD",
        "date": "2022-04-19",
        "net_amount": "32155.97",
        "description": "",
        "status": "executed"
      },
      {
        "id": "20220419000000000::ec624f60-ca70-42d6-9086-f47a1eeebeb7",
        "account_id": "34f33a89-390d-4001-aced-a5e978864b8d",
        "activity_type": "CSD",
        "date": "2022-04-19",
        "net_amount": "20979.69",
        "description": "",
        "status": "executed"
      },
      {
        "id": "20220419000000000::e96b84c0-15b8-4821-9c78-cce1d836ff5b",
        "account_id": "f78eb5ae-76c0-48ef-b5d9-07613da2e827",
        "activity_type": "CSD",
        "date": "2022-04-19",
        "net_amount": "22386.64",
        "description": "",
        "status": "executed"
      }
    ]
    """

    reqmock.get(
        BaseURL.BROKER_SANDBOX + "/v1/accounts/activities",
        [{"text": resp_one}, {"text": resp_two}, {"text": """[]"""}],
    )


def test_get_activities_for_account_default_asserts(reqmock, client: BrokerClient):
    setup_reqmock_for_paginated_account_activities_response(reqmock)

    result = client.get_account_activities(GetAccountActivitiesRequest())

    assert reqmock.call_count == 3
    assert isinstance(result, List)
    assert len(result) == 8
    assert isinstance(result[0], NonTradeActivity)
    assert isinstance(result[2], TradeActivity)

    # verify we asked for the correct ids when paginating
    assert reqmock.request_history[1].qs == {
        "page_token": ["20220419000000000::f77b60bf-ea39-4551-a3d6-000548e6f11c"]
    }
    assert reqmock.request_history[2].qs == {
        "page_token": ["20220419000000000::e96b84c0-15b8-4821-9c78-cce1d836ff5b"]
    }


def test_get_activities_for_account_full_pagination(reqmock, client: BrokerClient):
    setup_reqmock_for_paginated_account_activities_response(reqmock)

    result = client.get_account_activities(
        GetAccountActivitiesRequest(), handle_pagination=PaginationType.FULL
    )

    assert reqmock.call_count == 3
    assert isinstance(result, List)
    assert len(result) == 8
    assert isinstance(result[0], NonTradeActivity)
    assert isinstance(result[2], TradeActivity)


def test_get_activities_for_account_max_items_and_single_request_date(
    reqmock, client: BrokerClient
):
    """
    The api when `date` is specified is allowed to drop the pagination defaults and return all results at once.
    This test is to ensure in this case if there is a max items requested that we still only request
    that max items amount.
    """

    # Note we purposly have this returning more than requested, the api currently respects paging even in this state
    # but we should still be able to handle the case where it doesn't, so we don't go over max items
    reqmock.get(
        BaseURL.BROKER_SANDBOX + "/v1/accounts/activities",
        text="""
        [
          {
            "id": "20220304135420903::047e252a-a8a3-4e35-84e2-29814cbf5057",
            "account_id": "3dcb795c-3ccc-402a-abb9-07e26a1b1326",
            "activity_type": "FILL",
            "transaction_time": "2022-03-04T18:54:20.903569Z",
            "type": "partial_fill",
            "price": "2907.15",
            "qty": "1.792161878",
            "side": "buy",
            "symbol": "AMZN",
            "leaves_qty": "1",
            "order_id": "cddf433b-1a41-497d-ae31-50b1fee56fff",
            "cum_qty": "1.792161878",
            "order_status": "partially_filled"
          },
          {
            "id": "20220304135420898::2b9e8979-48b4-4b70-9ba0-008210b76ebf",
            "account_id": "3dcb795c-3ccc-402a-abb9-07e26a1b1326",
            "activity_type": "FILL",
            "transaction_time": "2022-03-04T18:54:20.89822Z",
            "type": "fill",
            "price": "2907.15",
            "qty": "1",
            "side": "buy",
            "symbol": "AMZN",
            "leaves_qty": "0",
            "order_id": "cddf433b-1a41-497d-ae31-50b1fee56fff",
            "cum_qty": "2.792161878",
            "order_status": "filled"
          },
          {
            "id": "20220304123922801::3b8a937c-b1d9-4ebe-ae94-5e0b52c3f350",
            "account_id": "3dcb795c-3ccc-402a-abb9-07e26a1b1326",
            "activity_type": "FILL",
            "transaction_time": "2022-03-04T17:39:22.801228Z",
            "type": "fill",
            "price": "2644.84",
            "qty": "0.058773239",
            "side": "sell",
            "symbol": "GOOGL",
            "leaves_qty": "0",
            "order_id": "642695e3-def7-4637-9525-2e7f698ebfc7",
            "cum_qty": "0.058773239",
            "order_status": "filled"
          },
          {
            "id": "20220304123922310::b53b6d71-a644-4be1-9f88-39d1c8d29831",
            "account_id": "3dcb795c-3ccc-402a-abb9-07e26a1b1326",
            "activity_type": "FILL",
            "transaction_time": "2022-03-04T17:39:22.310917Z",
            "type": "partial_fill",
            "price": "837.45",
            "qty": "1.998065556",
            "side": "sell",
            "symbol": "TSLA",
            "leaves_qty": "4",
            "order_id": "5f4a07dc-6503-4cbf-902a-8c6608401d97",
            "cum_qty": "1.998065556",
            "order_status": "partially_filled"
          },
          {
            "id": "20220304123922305::bc84b8a8-8758-42aa-be3b-618d097c2867",
            "account_id": "3dcb795c-3ccc-402a-abb9-07e26a1b1326",
            "activity_type": "FILL",
            "transaction_time": "2022-03-04T17:39:22.305629Z",
            "type": "fill",
            "price": "837.45",
            "qty": "4",
            "side": "sell",
            "symbol": "TSLA",
            "leaves_qty": "0",
            "order_id": "5f4a07dc-6503-4cbf-902a-8c6608401d97",
            "cum_qty": "5.998065556",
            "order_status": "filled"
          }
        ]
        """,
    )

    max_limit = 2
    date_str = "2022-03-04"

    result = client.get_account_activities(
        GetAccountActivitiesRequest(date=datetime.strptime(date_str, "%Y-%m-%d")),
        handle_pagination=PaginationType.FULL,
        max_items_limit=max_limit,
    )

    assert reqmock.call_count == 1
    assert isinstance(result, List)
    assert len(result) == max_limit

    request = reqmock.request_history[0]
    assert "date" in request.qs and request.qs["date"] == [f"{date_str} 00:00:00"]
    assert "page_size" in request.qs and request.qs["page_size"] == ["2"]


def test_get_activities_for_account_full_pagination_and_max_items(
    reqmock, client: BrokerClient
):
    # Note in this test we'll still have the api return too many results in the response just to validate that
    # we respect max limit regardless of what the api does
    setup_reqmock_for_paginated_account_activities_response(reqmock)

    max_limit = 5

    result = client.get_account_activities(
        GetAccountActivitiesRequest(),
        handle_pagination=PaginationType.FULL,
        max_items_limit=max_limit,
    )

    assert reqmock.call_count == 2
    assert isinstance(result, List)
    assert len(result) == max_limit

    # First limit is irrelevant since we hardcode returning 4 anyway, but second request needs to only request 1 item
    second_request = reqmock.request_history[1]
    assert "page_size" in second_request.qs and second_request.qs["page_size"] == ["1"]


def test_get_activities_for_account_none_pagination(reqmock, client: BrokerClient):
    setup_reqmock_for_paginated_account_activities_response(reqmock)

    result = client.get_account_activities(
        GetAccountActivitiesRequest(), handle_pagination=PaginationType.NONE
    )

    assert reqmock.call_count == 1
    assert isinstance(result, List)
    assert len(result) == 4
    assert isinstance(result[0], BaseActivity)


def test_get_account_activities_iterator_pagination(reqmock, client: BrokerClient):
    setup_reqmock_for_paginated_account_activities_response(reqmock)

    generator = client.get_account_activities(
        GetAccountActivitiesRequest(), handle_pagination=PaginationType.ITERATOR
    )

    assert isinstance(generator, Iterator)

    # When asking for an iterator we should not have made any requests yet
    assert not reqmock.called

    results = next(generator)

    assert isinstance(results, List)
    assert len(results) == 4
    assert isinstance(results[0], BaseActivity)
    assert reqmock.called_once

    results = next(generator)
    assert isinstance(results, List)
    assert len(results) == 4

    # generator should now be empty
    results = next(generator, None)
    assert reqmock.call_count == 3

    assert results is None


def test_get_account_activities_validates_max_items(reqmock, client: BrokerClient):
    with pytest.raises(ValueError) as e:
        client.get_account_activities(
            GetAccountActivitiesRequest(),
            max_items_limit=45,
            handle_pagination=PaginationType.ITERATOR,
        )

    assert "max_items_limit can only be specified for PaginationType.FULL" in str(
        e.value
    )
