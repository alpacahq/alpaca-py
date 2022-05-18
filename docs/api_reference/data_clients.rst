.. toctree::
   :maxdepth: 2
   :caption: Contents:

Market Data Clients
===================

Historical Data Client
----------------------

Alpaca provides over 5 years of historical market data for equities and cryptocurrencies. This data includes
bar (OHLCV), level 1 quotes and trade (price and sales) data. The historical data client
allows you to easily access this data and format it into object models or dataframes. To learn more about
the object models check out the market data models section.


.. autoclass:: alpaca.data.historical.HistoricalDataClient
   :members:



Live Data Client
----------------

Equity
~~~~~~

Using the MarketDataClient, you can access live equity data across both IEX and SIP datafeeds.
Minute bar data, trade data and quote data are available. See common


.. autoclass:: alpaca.data.live.MarketDataStream

Crypto
~~~~~~

Using the CryptoDataClient, you can access live crypto data for over 20+ coins.
Minute bar data, trade data, and quote data are available.

.. autoclass:: alpaca.data.live.CryptoDataStream