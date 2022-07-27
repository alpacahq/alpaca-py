![Alpaca-py](https://github.com/alpacahq/alpaca-py/blob/master/docs/images/alpaca-py-banner.png?raw=true)

[![Downloads](https://pepy.tech/badge/alpaca-py/month)](https://pepy.tech/project/alpaca-py)
[![Python Versions](https://img.shields.io/pypi/pyversions/alpaca-py.svg?logo=python&logoColor=white)](https://pypi.org/project/alpaca-py)
[![GitHub](https://img.shields.io/github/license/alpacahq/alpaca-py?color=blue)](https://github.com/alpacahq/alpaca-py/blob/master/LICENSE.md)
[![PyPI](https://img.shields.io/pypi/v/alpaca-py?color=blue)](https://pypi.org/project/alpaca-py/)

## Table of Contents
* [About](#About)
* [Installation](#Installation)
* [Usage](#Usage)
* [What's New?](#whats-new)
* [API Keys](#api-keys)

## About

Alpaca-py provides an interface for interacting with the API products Alpaca offers. These API products are provided as various REST, WebSocket and SSE endpoints that allow you to do everything from streaming market data to creating your own trading apps. 

Learn more about the API products Alpaca offers https://alpaca.markets.


## Installation

Alpaca-py is supported on Python 3.7+.  You can install Alpaca-py using pip.

Run the following command in your terminal.

```shell
  pip install alpaca-py
```

## Usage
Alpaca’s APIs allow you to do everything from building algorithmic trading strategies to building a full brokerage experience for your own end users. Here are some things you can do with Alpaca-py.

**Market Data API**: Access live and historical market data for 5000+ stocks and 20+ crypto.

**Trading API**: Trade stock and crypto with lightning fast execution speeds.

**Broker API & Connect**: Build investment apps - from robo-advisors to brokerages.

## What’s New? <a name="whats-new"></a>
If you’ve used the previous python SDK alpaca-trade-api, there are a few key differences to be aware of.

### Broker API
Alpaca-py lets you use Broker API to start building your investment apps! Learn more at the Broker page.

### OOP Design
Alpaca-py uses a more OOP approach to submitting requests compared to the previous SDK. To submit a request, you will most likely need to create a request object containing the desired request data. There is a request object for each type of request.

Example

To submit an order, you will need to provide a `MarketOrderRequest` object.

```python
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

client = TradingClient('api-key', 'secret-key')

request_params = MarketOrderRequest(
                        symbol="SPY",
                        qty=3,
                        side=OrderSide.BUY,
                        time_in_force=TimeInForce.DAY
                        )

client.submit_order(order_data=request_params)
```

### Data Validation
Alpaca-py uses pydantic to validate data models at run-time. This means if you are receiving request data via JSON from a client. You can handle parsing and validation through Alpaca’s request models. All request models can be instantiated by passing in data in dictionary format.

### Many Clients
Alpaca-py has a lot of client classes. There is a client for each API and even asset class specific clients (StockHistoricalData, CryptoDataStream). This requires you to pick and choose clients based on your needs.

## API Keys <a name="api-keys"></a>

### Trading and Market Data API
In order to use Alpaca’s services you’ll need to sign up for an Alpaca account and retrieve your API keys. Signing up is completely free and takes only a few minutes. Sandbox environments are available to test out the API. To use the sandbox environment, you will need to provide sandbox/paper keys. API keys are passed into Alpaca-py through either TradingClient, StockHistoricalDataClient, CryptoHistoricalDataClient, StockDataStream, or CryptoDataStream.

### Broker API
To use the Broker API, you will need to sign up for a broker account and retrieve your Broker API keys. The API keys can be found on the dashboard once you’ve logged in. Alpaca also provides a sandbox environment to test out Broker API. To use the sandbox mode, provide your sandbox keys. Once you have your keys, you can pass them into BrokerClient to get started.

## Dev setup

This project is managed via poetry so setup should be just running `poetry install`.

This repo is using [`pre-commit`](https://pre-commit.com/) to setup some checks to happen at commit time to keep the
repo clean. To set these up after you've run `poetry install` just run `poetry run pre-commit install` to have
pre-commit setup these hooks



