.. _market-data:

===========
Market Data
===========

The market data API allows you to access both live and historical data for equities and cryptocurrencies. 
Over 5 years of historical data is available for thousands of equity and cryptocurrency symbols. 
Various data types are available such as bars/candles (OHLCV), trade data (price and sales), and quote data.
For more information on the data types available, please look at the API reference. 


Equities
--------

Alpaca provides two market data subscription plans. The free plan offers data from IEX (Investors Exchange LLC), which accounts for 2.5% of market volume.
The premium plan offers data from all US exchanges consolidated by the Securities Information Processor (SIP), which accounts for 100% of market volume. and from 
Alpaca provides ultra low latency and high reliability as the data comes directly into Alpaca’s bare metal servers located in New Jersey sitting next to most of the market participants.
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


Alpaca provides over 20 coin pairs for trading. The table below lists all the coins available and the pairs
that can be traded.


.. list-table:: Coins Available on Alpaca
   :widths: 25 25 50
   :header-rows: 1

   * - Name
     - Ticker
     - Pairs Offered
   * - Aave
     - AAVE
     - AAVEUSD
   * - Basic Attention Token
     - BAT
     - BATUSD
   * - Bitcoin
     - BTC
     - BTCUSD
   * - Bitcoin Cash
     - BCH
     - BCHUSD
   * - ChainLink Token
     - LINK
     - LINKUSD
   * - Dai
     - Dai
     - DAIUSD
   * - Dogecoin 
     - DOGE
     - DOGEUSD
   * - Ethereum 
     - ETH
     - ETHUSD
   * - Graph Token 
     - GRT
     - GRTUSD
   * - Litecoin 
     - LTC
     - LTCUSD
   * - Maker 
     - MKR
     - MKRUSD
   * - Matic 
     - MATIC
     - MATICUSD
   * - PAX Gold 
     - PAXG
     - PAXGUSD
   * - Shiba Inu 
     - SHIB
     - SHIBUSD
   * - Solana 
     - SOL
     - SOLUSD
   * - Sushi 
     - SUSHI
     - SUSHIUSD
   * - Tether 
     - USDT
     - USDTUSD
   * - TRON 
     - TRX
     - TRXUSD
   * - Uniswap Protocol Token 
     - UNI
     - UNIUSD
   * - Wrapped BTC
     - WBTC
     - WBTCUSD
   * - Yearn.Finance 
     - YFI
     - YFIUSD

