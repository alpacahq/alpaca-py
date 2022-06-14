============
Introduction
============


About
-----

Alpaca-py provides an interface for interacting with the various REST and WebSocket endpoints Alpaca offers.
You can access both historical and live market data for equities and cryptocurrencies via the Market Data API. 
You can place easily place trades for both crypto and equities through a uniform interface. Alpaca-py also offers the ability
to manage your Broker API account by creating accounts, managing funds, and more. 

Learn more about the API products Alpaca offers at the `homepage <https://alpaca.markets/>`_.

What's New?
-----------

If you use the previous SDK `alpaca-trade-api <https://github.com/alpacahq/alpaca-trade-api-python>`_, there are a few
key differences to be aware of.

Alpaca-py uses

Installation
------------

Alpaca-py is supported on Python 3.7+.  You can install Alpaca-py using pip.

Run the following command in your terminal.

.. code-block:: shell-session

    pip install alpaca-py

API Keys
--------

In order to use Alpaca's services you'll need to `sign up for an Alpaca account <https://app.alpaca.markets/signup>`_ and retrieve your API keys.
Signing up is completely free and takes only a few minutes. Sandbox environments are available to test
out the API. To use the sandbox environment, you will need to provide sandbox/paper keys. API keys are
passed into Alpaca-py through either ``TradingClient``, ``HistoricalDataClient``, ``MarketDataStream``, ``CryptoDataStream`` or ``BrokerClient``.

.. attention::

    To use the Broker API, you will need to sign up for a `broker account <https://broker-app.alpaca.markets/sign-up>`_ and retrieve
    your Broker API keys.



