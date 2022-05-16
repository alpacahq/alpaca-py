.. toctree::
   :maxdepth: 2
   :caption: Contents:

Market Data Models
==================

Bar
---

A bar is a unit of aggregrated price data of a defined interval of time. Bars, also known as candlesticks, contain
open, high, low, close, volume (OHLCV) information.

.. autoclass:: alpaca.data.models.Bar
   :members:

BarSet
------

A dictionary of Bars keyed by string valued symbol identifiers. See Bar.

.. autoclass:: alpaca.data.models.BarSet
   :members:


Quote
-----

A quote is a level 1 best bid and offer. Quotes can be across exchanges or for a single exchange. Quotes contain a bid
an ask, each with a price and size.

.. autoclass:: alpaca.data.models.Quote
   :members:


QuoteSet
--------

A dictionary of Quotes keyed by string valued symbol identifiers. See Quote.

.. autoclass:: alpaca.data.models.QuoteSet
   :members:


Trade
-----

A Trade is a transaction that has occurred on an exchange.

.. autoclass:: alpaca.data.models.Trade
   :members:


TradeSet
--------

A dictionary of Trades keyed by string valued symbol identifiers. See Trade.

.. autoclass:: alpaca.data.models.TradeSet
   :members:


Snapshot
--------

A snapshot is a collection of various market data types. A snapshot contains the
latest quote, the latest trade, the latest minute bar and the latest daily bar.

.. autoclass:: alpaca.data.models.Snapshot

SnapshotSet
-----------

A dictionary of Snapshots keyed by string valued symbol identifiers.


.. autoclass:: alpaca.data.models.SnapshotSet
