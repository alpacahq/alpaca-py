.. _market-data:

===========
Market Data
===========

The market data API allows you to access both live and historical data for equities and cryptocurrencies. 
Over 5 years of historical data is available for thousands of equity and cryptocurrency symbols. 
Various data types are available such as bars/candles (OHLCV), trade data (price and sales), and quote data. For
crypto, there is also orderbook data. For more information on the data types available,
please look at the `API reference <https://alpaca.markets/docs/market-data/>`_.


Subscription Plans
------------------

Most market data features are free to use. However, if you are a professional or institution, you may
wish to expand with the unlimited plan. Learn more about the subscriptions plans at
`alpaca.markets/data <https://alpaca.markets/data>`_.


API Keys
--------

Crypto data does not require authentication to use. i.e. you can initialize ``CryptoHistoricalDataClient`` without
providing API keys. If you do provide API keys, your rate limit will be higher.

However, to access stock data, you will need to provide your API keys. The keys can be found
on the dashboard after signing in.


Getting Started with Clients
----------------------------

There are 4 different clients that let you access market data. There are 2 historical data clients
and 2 real-time data clients. The crypto data clients do not require API keys to use.


Historical Data
^^^^^^^^^^^^^^^

.. code-block:: python

    from alpaca.data import CryptoHistoricalDataClient, StockHistoricalDataClient

    API_KEY = "api-key"
    SECRET_KEY = "secret-key"

    # no keys required.
    crypto_client = CryptoHistoricalDataClient()

    # keys required
    stock_client = StockHistoricalDataClient(API_KEY, SECRET_KEY)


Real-time Data Stream
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from alpaca.data import CryptoDataStream, StockDataStream

    API_KEY = "api-key"
    SECRET_KEY = "secret-key"

    # no keys required.
    crypto_stream = CryptoDataStream()

    # keys required
    stock_stream = StockDataStream(API_KEY, SECRET_KEY)