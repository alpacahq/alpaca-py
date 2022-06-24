============
Introduction
============


About
-----

Alpaca-py provides an interface for interacting with the API products Alpaca offers.
These API products are provided as various REST and WebSocket endpoints that allow you to do
everything from streaming market data to creating your own trading apps. You can learn about the API products Alpaca offers at `alpaca.markets <https://alpaca.markets/>`_.

Usage
-----

Here are some things you can do with alpaca-py.

* Access years of historical data for 5000+ equities and 20+ cryptocurrencies
* Stream live market data for equities and crypto
* Place orders for equities and crypto under uniform interface
* Create and manage brokerage accounts on behalf of others with Broker API


What's New?
-----------

If you use the previous SDK `alpaca-trade-api <https://github.com/alpacahq/alpaca-trade-api-python>`_, there are a few
key differences to be aware of.

Alpaca-py uses a more OOP approach to submitting request compared to the previous SDK.
To submit a request that requires body parameters, you will need to create
a request object containing the desired request data. There is a request object for each
type of request, for example to submit an order, you will need to provide
an ``OrderRequest`` object.

Installation
------------

Alpaca-py is supported on Python 3.8+. You can install Alpaca-py using pip.

Run the following command in your terminal.

.. code-block:: shell-session

    pip install alpaca-py

Errors
^^^^^^

Try upgrading your pip before installing if you face errors.

.. code-block:: shell-session

    pip install --upgrade pip

API Keys
--------

In order to use Alpaca's services you'll need to `sign up for an Alpaca account <https://app.alpaca.markets/signup>`_ and retrieve your API keys.
Signing up is completely free and takes only a few minutes. Sandbox environments are available to test
out the API. To use the sandbox environment, you will need to provide sandbox/paper keys. API keys are
passed into Alpaca-py through either ``TradingClient``, ``HistoricalDataClient``, ``MarketDataStream``, ``CryptoDataStream`` or ``BrokerClient``.

.. attention::

    To use the Broker API, you will need to sign up for a `broker account <https://broker-app.alpaca.markets/sign-up>`_ and retrieve
    your Broker API keys.



