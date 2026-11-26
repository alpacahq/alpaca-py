"""The surface collector sees models that stream methods hand to callbacks."""

import asyncio

import _exercised
import _surface
from alpaca.data.live.stock import StockDataStream
from alpaca.data.models import TradingStatus
from msgpack import Timestamp
from scenarios._stream import trading_status


def test_collector_observes_models_delivered_to_stream_callbacks():
    collector = _exercised.Collector(_surface.collect())
    stream = StockDataStream("key", "secret")
    received = []

    async def handler(message):
        received.append(message)

    frame = trading_status("AAPL")
    frame["t"] = Timestamp(*frame["t"]["$timestamp"])

    with collector.active():
        # subscribe_* returns None: the model only reaches the handler.
        assert stream.subscribe_trading_statuses(handler, "AAPL") is None
        asyncio.run(stream._dispatch(frame))

    assert len(received) == 1 and isinstance(received[0], TradingStatus)
    assert "response:alpaca.data.TradingStatus.status_code" in collector.exercised
