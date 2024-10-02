.. _broker:

======
Broker
======

What is Broker API?
-------------------

The Broker API allows you to build investment services.
The Broker API lets you create brokerage accounts on behalf of your users,
fund those accounts, place and manage orders on behalf of those accounts, journal
cash and securities between accounts, and more.

Some common use cases of Broker API are:

* Trading/investing app (non-financial institution)
* Broker dealer (fully-disclosed, non-disclosed, omnibus)
* Registered Investment Advisor (RIA)

We support most use cases internationally.

---------

Getting Started with BrokerClient
---------------------------------

In alpaca-py, all Broker API services are accessed through the ``BrokerClient``.
For each endpoint in the Broker API, there is a corresponding method within the client.
To initialize a client, you will need to provide it your **API keys** which can be found on the
`Broker dashboard <https://broker-app.alpaca.markets/>`_. If you wish to use your sandbox keys,
you will need to set the sandbox parameter to ``True`` when initializing.

Learn more about ``BrokerClient`` in the Broker reference page.



.. code-block:: python

    from alpaca.broker import BrokerClient

    BROKER_API_KEY = "api-key"
    BROKER_SECRET_KEY = "secret-key"

    broker_client = BrokerClient(
                        api_key=Broker_API_KEY,
                        secret_key=BROKER_SECRET_KEY,
                        sandbox=True,
                    )



Using Request Objects
---------------------

In Alpaca-py, many methods will require instantiating and passing in a separate object for the request parameters.
For example, the ``BrokerClient::create_journal`` method requires you to pass in a ``CreateJournalRequest`` object as a parameter.
Once successfully instantiated, the ``CreateJournalRequest`` object will contain all the data required
for a successful request to the API.

Accounts
--------

The accounts API allows you to create and manage brokerage accounts on behalf of your users. To learn more about
accounts on Broker API, visit the `Alpaca API documentation <https://alpaca.markets/docs/api-references/broker-api/accounts/accounts/>`__.


Create an Account
^^^^^^^^^^^^^^^^^

You can create brokerage accounts on behalf of your users using the ``BrokerClient::create_account`` method.
To create an account you need to first instantiate a ``CreateAccountRequest`` with all the relevant account details.
``CreateAccountRequest`` requires ``contact``, ``identity``, ``disclosures``, and ``agreements``. There are also
two additional fields which are optional: ``documents`` and ``trusted_contact``.

First we will need to prepare our account data by organizing its constituent parts.
Then we can pass those parts into the ``CreateAccountRequest`` model before submitting our request.

.. code-block:: python

    from alpaca.broker.client import BrokerClient
    from alpaca.broker.models import (
                            Contact,
                            Identity,
                            Disclosures,
                            Agreement
                        )
    from alpaca.broker.requests import CreateAccountRequest
    from alpaca.broker.enums import TaxIdType, FundingSource, AgreementType

    broker_client = BrokerClient('api-key', 'secret-key')

    # Contact
    contact_data = Contact(
                email_address="cool_alpaca@example.com",
                phone_number="555-666-7788",
                street_address=["20 N San Mateo Dr"],
                city="San Mateo",
                state="CA",
                postal_code="94401",
                country="USA"
                )
    # Identity
    identity_data = Identity(
            given_name="John",
            middle_name="Smith",
            family_name="Doe",
            date_of_birth="1990-01-01",
            tax_id="666-55-4321",
            tax_id_type=TaxIdType.USA_SSN,
            country_of_citizenship="USA",
            country_of_birth="USA",
            country_of_tax_residence="USA",
            funding_source=[FundingSource.EMPLOYMENT_INCOME]
            )

    # Disclosures
    disclosure_data = Disclosures(
            is_control_person=False,
            is_affiliated_exchange_or_finra=False,
            is_politically_exposed=False,
            immediate_family_exposed=False,
            )

    # Agreements
    agreement_data = [
        Agreement(
          agreement=AgreementType.MARGIN,
          signed_at="2020-09-11T18:09:33Z",
          ip_address="185.13.21.99",
        ),
        Agreement(
          agreement=AgreementType.ACCOUNT,
          signed_at="2020-09-11T18:13:44Z",
          ip_address="185.13.21.99",
        ),
        Agreement(
          agreement=AgreementType.CUSTOMER,
          signed_at="2020-09-11T18:13:44Z",
          ip_address="185.13.21.99",
        ),
        Agreement(
          agreement=AgreementType.CRYPTO,
          signed_at="2020-09-11T18:13:44Z",
          ip_address="185.13.21.99",
        )
    ]

    # ## CreateAccountRequest ## #
    account_data = CreateAccountRequest(
                            contact=contact_data,
                            identity=identity_data,
                            disclosures=disclosure_data,
                            agreements=agreement_data
                            )

    # Make a request to create a new brokerage account
    account = broker_client.create_account(account_data)



List All Accounts
^^^^^^^^^^^^^^^^^

The ``BrokerClient::list_accounts`` method allows you to list all the brokerage accounts under
your management. The method takes an optional parameter ``search_parameters`` which requires a
``ListAccountsRequest`` object. This parameter allows you to filter the list of accounts returned.

.. code-block:: python

    from alpaca.broker.client import BrokerClient
    from alpaca.broker.requests import ListAccountsRequest
    from alpaca.broker.enums import AccountEntities

    broker_client = BrokerClient('api-key', 'secret-key')

    # search for accounts created after January 30th 2022.
    #Response should contain Contact and Identity fields for each account.
    filter = ListAccountsRequest(
                        created_after=datetime.datetime.strptime("2022-01-30", "%Y-%m-%d"),
                        entities=[AccountEntities.CONTACT, AccountEntities.IDENTITY]
                        )

    accounts = broker_client.list_accounts(search_parameters=filter)


Funding
-------

The funding API allows you to create Bank/ACH connections and transfer funds in and out of accounts.
To learn more about funding on Broker API, please visit the `Alpaca API documentation <https://alpaca.markets/docs/api-references/broker-api/funding/transfers/>`__.

Create an ACH Relationship
^^^^^^^^^^^^^^^^^^^^^^^^^^

Before an account can be funded, it needs to have an external account connection established. There are two types of
connections that be created: ACH relationships and bank relationships. ACH Relationships can
be created using routing and account numbers, or via Plaid.

To use Plaid, you will require a ``processor_token`` provided by Plaid
specifically for Alpaca. View this `article <https://alpaca.markets/learn/easily-allow-your-user-to-fund-their-account-with-plaid-and-broker-api/>`_ to learn more

In this example we will use routing and account numbers to establish an ACH relationship.

.. code-block:: python

    from alpaca.broker.client import BrokerClient
    from alpaca.broker.requests import CreateACHRelationshipRequest
    from alpaca.broker.enums import BankAccountType

    broker_client = BrokerClient('api-key', 'secret-key')

    account_id = "c8f1ef5d-edc0-4f23-9ee4-378f19cb92a4"

    ach_data = CreateACHRelationshipRequest(
                        account_owner_name="John Doe",
                        bank_account_type=BankAccountType.CHECKING,
                        bank_account_number="123456789abc",
                        bank_routing_number="121000358",
                    )

    ach_relationship = broker_client.create_ach_relationship_for_account(
                        account_id=account_id,
                        ach_data=ach_data
                    )


Create a Transfer
^^^^^^^^^^^^^^^^^

After a bank or ACH relationship has been established for an account, transfers can be made.
There are two types of transfers: incoming (deposits) or outgoing (withdrawals). Transfers based on
ACH relationships must use ``CreateACHTransferRequest`` and bank relationships must use
``CreateBankTransferRequest``.

.. code-block:: python

    from alpaca.broker.client import BrokerClient
    from alpaca.broker.requests import CreateACHTransferRequest
    from alpaca.broker.enums import TransferDirection, TransferTiming

    broker_client = BrokerClient('api-key', 'secret-key')

    account_id = "c8f1ef5d-edc0-4f23-9ee4-378f19cb92a4"

    transfer_data = CreateACHTransferRequest(
                        amount=1000,
                        direction=TransferDirection.INCOMING,
                        timing=TransferTiming.IMMEDIATE,
                        relationship_id="0f08c6bc-8e9f-463d-a73f-fd047fdb5e94"
                    )
    transfer = broker_client.create_transfer_for_account(
                    account_id=account_id,
                    transfer_data=transfer_data
                )


Journals
--------

The journals API allows you to transfer cash and securities between accounts under your management.
To learn more about the journals API, visit the `Alpaca API documentation <https://alpaca.markets/docs/api-references/broker-api/journals/>`__.

Create a Journal
^^^^^^^^^^^^^^^^

A journal is made between two accounts. For every journal request, assets will leave ``from_account`` and into ``to_account``.
There are two types of journals: cash journals and security journals. Cash journals move the account currency
between accounts. Security journals move stocks between accounts.

.. code-block:: python

    from alpaca.broker.client import BrokerClient
    from alpaca.broker.requests import CreateJournalRequest
    from alpaca.broker.enums import JournalEntryType

    broker_client = BrokerClient('api-key', 'secret-key')

    journal_data = CreateJournalRequest(
                        from_account="c8f1ef5d-edc0-4f23-9ee4-378f19cb92a4",
                        entry_type=JournalEntryType.CASH,
                        to_account="0f08c6bc-8e9f-463d-a73f-fd047fdb5e94",
                        amount=50
                    )

    journal = broker_client.create_journal(journal_data=journal_data)

Create a Batch Journal
^^^^^^^^^^^^^^^^^^^^^^

A batch journal lets you journal from one account into many accounts at the same time.

.. code-block:: python

    from alpaca.broker.client import BrokerClient
    from alpaca.broker.requests import CreateBatchJournalRequest, BatchJournalRequestEntry
    from alpaca.broker.enums import JournalEntryType

    broker_client = BrokerClient('api-key', 'secret-key')

    # Receiving accounts
    batch_entries = [
        BatchJournalRequestEntry(
                to_account="d7017fd9-60dd-425b-a09a-63ff59368b62",
                amount=50,
        ),
        BatchJournalRequestEntry(
                to_account="94fa473d-9a92-40cd-908c-25da9fba1e65",
                amount=100,
        ),
        BatchJournalRequestEntry(
                to_account="399f85f1-cbbd-4eaa-a934-70027fb5c1de",
                amount=700,
        ),
    ]

    batch_journal_data = CreateBatchJournalRequest(
                        entry_type=JournalEntryType.CASH,
                        from_account="8f8c8cee-2591-4f83-be12-82c659b5e748",
                        entries=batch_entries
                    )

    batch_journal = broker_client.create_batch_journal(batch_data=batch_journal_data)


Trading
-------

The Broker trading API allows you to place orders and manage positions on behalf of your users.
To learn more about trading on Broker API, visit the `Alpaca API documentation <https://alpaca.markets/docs/api-references/broker-api/trading/orders/>`__.

.. attention::
    Keep in mind, all models necessary for trading on Broker API live within the ``alpaca.broker`` and **not** ``alpaca.trading``. Although
    the trading models in ``alpaca.broker`` and ``alpaca.trading`` have the same name, they are different.


Create an Order
^^^^^^^^^^^^^^^

To create an order on Alpaca-py you must use an ``OrderRequest`` object. There are different
``OrderRequest`` objects based on the type of order you want to make. For market orders, there is
``MarketOrderRequest``, limit orders have ``LimitOrderRequest``, stop orders ``StopOrderRequest``, and
trailing stop orders have ``TrailingStopOrderRequest``. Each order type have their own required parameters
for a successful order.

.. code-block:: python

    from alpaca.broker.client import BrokerClient
    from alpaca.broker.requests import MarketOrderRequest, LimitOrderRequest
    from alpaca.trading.enums import OrderSide, TimeInForce

    broker_client = BrokerClient('api-key', 'secret-key')

    # account to make order for
    account_id = "c8f1ef5d-edc0-4f23-9ee4-378f19cb92a4"

    # preparing orders
    market_order_data = MarketOrderRequest(
                        symbol="BTCUSD",
                        qty=1,
                        side=OrderSide.BUY,
                        time_in_force=TimeInForce.GTC,
                        commission=1
                )

    limit_order_data = LimitOrderRequest(
                        symbol="SPY",
                        limit_price=300,
                        qty=10,
                        side=OrderSide.SELL,
                        time_in_force=TimeInForce.FOK,
                        commission=1
                  )

    # Market order
    market_order = broker_client.submit_order_for_account(
                    account_id=account_id,
                    order_data=market_order_data
                    )

    # Limit order
    limit_order = broker_client.submit_order_for_account(
                    account_id=account_id,
                    order_data=limit_order_data
                   )

Get All Positions
^^^^^^^^^^^^^^^^^

You can retrieve all open positions for a specific account using only the ``account_id``.
This will return a list of ``Position`` objects.


.. code-block:: python

    from alpaca.broker import BrokerClient

    broker_client = BrokerClient('api-key', 'secret-key')

    # account to get positions for
    account_id = "c8f1ef5d-edc0-4f23-9ee4-378f19cb92a4"

    positions = broker_client.get_all_positions_for_account(account_id=account_id)
