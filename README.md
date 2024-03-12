[![Alpaca-py](https://github.com/alpacahq/alpaca-py/blob/master/docs/images/alpaca-py-banner.png?raw=true)](https://alpaca.markets/docs/python-sdk)

[![Downloads](https://pepy.tech/badge/alpaca-py/month)](https://pepy.tech/project/alpaca-py)
[![Python Versions](https://img.shields.io/pypi/pyversions/alpaca-py.svg?logo=python&logoColor=white)](https://pypi.org/project/alpaca-py)
[![GitHub](https://img.shields.io/github/license/alpacahq/alpaca-py?color=blue)](https://github.com/alpacahq/alpaca-py/blob/master/LICENSE.md)
[![PyPI](https://img.shields.io/pypi/v/alpaca-py?color=blue)](https://pypi.org/project/alpaca-py/)

## Table of Contents
* [About](#about)
* [Documentation](#documentation)
* [Installation](#installation)
* [Update](#update)
* [What's New?](#whats-new)
   1. [Broker API](#broker-api-new)
   2. [OOP Design](#oop-design)
   3. [Data Validation](#data-validation)
   4. [Many Clients](#many-clients)
* [API Keys](#api-keys)
   1. [Trading and Market Data API Keys](#trading-api-keys)
   2. [Broker API Keys](#trading-api-keys)
* [Usage](#usage)
   1. [Broker API Example](#broker-api-example)
   2. [Trading API Example](#trading-api-example)
   3. [Market Data API Example](#data-api-example)
* [Contributing](https://github.com/alpacahq/alpaca-py/blob/master/CONTRIBUTING.md)
* [License](https://github.com/alpacahq/alpaca-py/blob/master/LICENSE)

## About <a name="about"></a>

Alpaca-py provides an interface for interacting with the API products Alpaca offers. These API products are provided as various REST, WebSocket and SSE endpoints that allow you to do everything from streaming market data to creating your own investment apps. 

Learn more about the API products Alpaca offers at https://alpaca.markets.

## Documentation <a name="documentation"></a>

Alpaca-py has a supplementary documentation site which contains references for all clients, methods and models found in this codebase. The documentation
also contains examples to get started with alpaca-py.

You can find the documentation site here: https://docs.alpaca.markets/docs/getting-started-1

## Installation <a name="installation"></a>

Alpaca-py is supported on Python 3.7+.  You can install Alpaca-py using pip.

Run the following command in your terminal.

```shell
  pip install alpaca-py
```

## Update <a name="update"></a>

If you already have Alpaca-py installed, and would like to use the latest version available...

Run the following command in your terminal:

```shell
  pip install alpaca-py --upgrade
```

## What’s New? <a name="whats-new"></a>
If you’ve used the previous python SDK alpaca-trade-api, there are a few key differences to be aware of.

### Broker API <a name="broker-api-new"></a>
Alpaca-py lets you use Broker API to start building your investment apps! Learn more at the [Broker](https://docs.alpaca.markets/docs/broker-api) page.

### OOP Design <a name="oop-design"></a>
Alpaca-py uses a more OOP approach to submitting requests compared to the previous SDK. To submit a request, you will most likely need to create a request object containing the desired request data. Generally, there is a unique request model for each method. 

Some examples of request models corresponding to methods: 

* ``GetOrdersRequest`` for ``TradingClient.get_orders()``
* ``CryptoLatestOrderbookRequest`` for ``CryptoHistoricalDataClient.get_crypto_latest_orderbook()``

**Request Models Usage Example**

To get historical bar data for crypto, you will need to provide a ``CryptoBarsRequest`` object.

```python
from alpaca.data.historical import CryptoHistoricalDataClient
from alpaca.data.requests import CryptoBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime

# no keys required for crypto data
client = CryptoHistoricalDataClient()

request_params = CryptoBarsRequest(
                        symbol_or_symbols=["BTC/USD", "ETH/USD"],
                        timeframe=TimeFrame.Day,
                        start=datetime(2022, 7, 1)
                 )

bars = client.get_crypto_bars(request_params)
```

### Data Validation <a name="data-validation"></a>
Alpaca-py uses *pydantic* to validate data models at run-time. This means if you are receiving request data via JSON from a client. You can handle parsing and validation through Alpaca’s request models. All request models can be instantiated by passing in data in dictionary format.

Here is a rough example of what is possible.

```python

 @app.route('/post_json', methods=['POST'])
 def do_trade():
     # ...

     order_data_json = request.get_json()

     # validate data
     MarketOrderRequest(**order_data_json)

     # ...
```

### Many Clients <a name="many-clients"></a>
Alpaca-py has a lot of client classes. There is a client for each API and even asset class specific clients (``StockHistoricalDataClient``, ``CryptoDataStream``, ``OptionHistoricalDataClient``). This requires you to pick and choose clients based on your needs.

**Broker API:** ``BrokerClient``

**Trading API:** ``TradingClient``

**Market Data API:**  ``StockHistoricalDataClient``, ``CryptoHistoricalDataClient``, ``OptionHistoricalDataClient``, ``CryptoDataStream``, ``StockDataStream``, ``OptionDataStream``

## API Keys <a name="api-keys"></a>

### Trading and Market Data API <a name="trading-api-keys"></a>
In order to use Alpaca’s services you’ll need to sign up for an Alpaca account and retrieve your API keys. Signing up is completely free and takes only a few minutes. Sandbox environments are available to test out the API. To use the sandbox environment, you will need to provide sandbox/paper keys. API keys are passed into Alpaca-py through either ``TradingClient``, ``StockHistoricalDataClient``, ``CryptoHistoricalDataClient``, ``OptionHistoricalDataClient``. ``StockDataStream``, ``CryptoDataStream``, or ``OptionDataStream``.

### Broker API <a name="broker-api-keys"></a>
To use the Broker API, you will need to sign up for a broker account and retrieve your Broker API keys. The API keys can be found on the dashboard once you’ve logged in. Alpaca also provides a sandbox environment to test out Broker API. To use the sandbox mode, provide your sandbox keys. Once you have your keys, you can pass them into ``BrokerClient`` to get started.

## Usage <a name="usage"></a>
Alpaca’s APIs allow you to do everything from building algorithmic trading strategies to building a full brokerage experience for your own end users. Here are some things you can do with Alpaca-py.

To view full descriptions and examples view the [documentation page](https://docs.alpaca.markets/docs/getting-started-1).

**Market Data API**: Access live and historical market data for 5000+ stocks, 20+ crypto, and options(beta).

**Trading API**: Trade stock and crypto with lightning fast execution speeds.

**Broker API & Connect**: Build investment apps - from robo-advisors to brokerages.

### Broker API Example <a name="broker-api-example"></a>

**Listing All Accounts**

The ``BrokerClient.list_accounts`` method allows you to list all the brokerage accounts under your management. The method takes an optional parameter ``search_parameters`` which requires a ``ListAccountsRequest`` object. This parameter allows you to filter the list of accounts returned.

```python
from alpaca.broker.client import BrokerClient
from alpaca.broker.requests import ListAccountsRequest
from alpaca.broker.enums import AccountEntities

broker_client = BrokerClient('api-key', 'secret-key')

# search for accounts created after January 30th 2022.
# Response should contain Contact and Identity fields for each account.
filter = ListAccountsRequest(
                    created_after=datetime.datetime.strptime("2022-01-30", "%Y-%m-%d"),
                    entities=[AccountEntities.CONTACT, AccountEntities.IDENTITY]
                    )

accounts = broker_client.list_accounts(search_parameters=filter)
```

### Trading API Example <a name="trading-api-example"></a>

**Submitting an Order**

To create an order on Alpaca-py you must use an ``OrderRequest`` object. There are different ``OrderRequest`` objects based on the type of order you want to make. For market orders, there is ``MarketOrderRequest``, limit orders have ``LimitOrderRequest``, stop orders ``StopOrderRequest``, and trailing stop orders have ``TrailingStopOrderRequest``. Each order type have their own required parameters for a successful order.


```python
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

trading_client = TradingClient('api-key', 'secret-key')


# preparing order data
market_order_data = MarketOrderRequest(
                      symbol="BTC/USD",
                      qty=0.0001,
                      side=OrderSide.BUY,
                      time_in_force=TimeInForce.DAY
                  )

# Market order
market_order = trading_client.submit_order(
                order_data=market_order_data
                )
```


### Market Data API Example <a name="data-api-example"></a>
**Querying Historical Bar Data**

You can request bar data via the HistoricalDataClients. In this example, we query daily bar data for “BTC/USD” and “ETH/USD” since July 1st 2022. You can convert the response to a multi-index pandas dataframe using the ``.df`` property.

```python
from alpaca.data.historical import CryptoHistoricalDataClient
from alpaca.data.requests import CryptoBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime

# no keys required for crypto data
client = CryptoHistoricalDataClient()

request_params = CryptoBarsRequest(
                        symbol_or_symbols=["BTC/USD", "ETH/USD"],
                        timeframe=TimeFrame.Day,
                        start=datetime.strptime("2022-07-01", '%Y-%m-%d')
                        )

bars = client.get_crypto_bars(request_params)

# convert to dataframe
bars.df

```

### Options Trading (Beta) <a name="options-trading"></a>

We're excited to support options trading! Use this section to read up on Alpaca's Beta trading capabilities.
For more details, please refer to [our documentation page for options trading](https://docs.alpaca.markets/v1.1/docs/options-trading)

> Options trading is in BETA. Only BETA users are able to access options endpoints. We will continue to update our documentation as we collect your valuable feedback.

There is an example jupyter notebook to explain methods of alpaca-py for options trading.

* [jupyter notebook: options trading basic example with alpaca-py](https://github.com/alpacahq/alpaca-py/blob/master/examples/options-trading-basic.ipynb)
