.. toctree::
   :maxdepth: 2
   :caption: Contents:

Market Data API
===============

The market data API allows you to access both live and historical data for equities and cryptocurrencies. 
Over 5 years of historical data is available for thousands of equity and cryptocurrency symbols. 
Various data types are available such as bars/candles (OHLCV), trade data (price and sales), and quote data.
For more information on the data types available, please look at the API reference. 


Equities
--------

Alpaca provides market data from two data sources:

1. IEX (Investors Exchange LLC) which accounts for ~2.5% market volume

    IEX is optimal to start testing out your app and utilize it where visualizing accurate price information may not take precedence.

2. All US exchanges which account for 100% market volume

    This Alpaca data feed is coming as direct feed from exchanges consolidated by the Securities Information Processors (SIPs). These link the U.S. markets by processing and consolidating all bid/ask quotes and trades from every trading venue into a single, easily consumed data feed.

    We provide ultra low latency and high reliability as the data comes directly into Alpaca’s bare metal servers located in New Jersey sitting next to most of the market participants.

    SIP data is great for creating your trading app where accurate price information is essential for traders and internal use.




Crypto
------

**Please note that Alpaca Crypto Data is in beta - we welcome any feedback to improve our offering.**

Alpaca provides crypto data from multiple venues and but currently routes orders to FTX.US only.

.. list-table:: Crypto Exchanges Supported by Alpaca
   :widths: 25 25 50
   :header-rows: 1

   * - Exchange Code
     - Name of Exchanges
     - Enum Value
   * - FTXU
     - FTX
     - ``Exchange.FTXU``
   * - ERSX
     - ErisX
     - ``Exchange.ERSX``
   * - CBSE
     - Coinbase
     - ``Exchange.CBSE``
   * - GNSS
     - Genesis
     - ``Exchange.ERSX``

