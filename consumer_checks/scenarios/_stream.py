"""Helpers for market-data websocket scenarios.

Live ticks are not deterministic, so the scenarios serve fixed frames
(``stub_websocket``) instead of connecting. ``run_until`` is the usual user
shape: subscribe, ``run`` until a handler has seen the messages, unsubscribe
from another thread (the stream loop must not call ``unsubscribe_*`` itself:
that waits on the same loop), then ``stop``.
"""

from __future__ import annotations

import threading
from typing import Any, Callable, Dict, List, MutableMapping

# One instant, packed as a msgpack timestamp by the harness.
TIMESTAMP: Dict[str, List[int]] = {"$timestamp": [1_710_000_000, 0]}

CONNECTED = [{"T": "success", "msg": "connected"}]
AUTHENTICATED = [{"T": "success", "msg": "authenticated"}]


def handshake() -> List[List[Dict[str, Any]]]:
    return [CONNECTED, AUTHENTICATED]


def frame(message: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [message]


def bar(symbol: str, kind: str) -> Dict[str, Any]:
    return {
        "T": kind,
        "S": symbol,
        "o": 177.94,
        "h": 178.005,
        "l": 177.94,
        "c": 178.005,
        "v": 8547,
        "t": TIMESTAMP,
        "n": 66,
        "vw": 177.987562,
    }


def quote(symbol: str) -> Dict[str, Any]:
    return {
        "T": "q",
        "S": symbol,
        "bx": "V",
        "bp": 25.41,
        "bs": 35,
        "ax": "V",
        "ap": 25.43,
        "as": 35,
        "c": ["R"],
        "z": "B",
        "t": TIMESTAMP,
    }


def trade(symbol: str) -> Dict[str, Any]:
    return {
        "T": "t",
        "S": symbol,
        "i": 6142,
        "x": "V",
        "p": 177.79,
        "s": 90,
        "c": ["@", "I"],
        "z": "C",
        "t": TIMESTAMP,
    }


def trading_status(symbol: str) -> Dict[str, Any]:
    return {
        "T": "s",
        "S": symbol,
        "t": TIMESTAMP,
        "sc": "T",
        "sm": "Trading Resumption",
        "rc": "C11",
        "rm": "",
        "z": "C",
    }


def trade_cancel(symbol: str) -> Dict[str, Any]:
    return {
        "T": "x",
        "S": symbol,
        "i": 4868,
        "x": "D",
        "p": 36.18,
        "s": 31800,
        "a": "C",
        "z": "C",
        "t": TIMESTAMP,
    }


def trade_correction(symbol: str) -> Dict[str, Any]:
    return {
        "T": "c",
        "S": symbol,
        "t": TIMESTAMP,
        "x": "V",
        "oi": 1,
        "op": 100.0,
        "os": 10,
        "oc": ["@"],
        "ci": 2,
        "cp": 101.0,
        "cs": 10,
        "cc": ["@"],
        "z": "C",
    }


def orderbook(symbol: str) -> Dict[str, Any]:
    return {
        "T": "o",
        "S": symbol,
        "t": TIMESTAMP,
        "b": [{"p": 65128.1, "s": 1.6542}],
        "a": [{"p": 65129.2, "s": 0.4}],
        "r": True,
    }


def news(symbol: str) -> Dict[str, Any]:
    return {
        "T": "n",
        "id": 39358670,
        "headline": "Example headline",
        "summary": "",
        "author": "Benzinga Newsdesk",
        "created_at": TIMESTAMP,
        "updated_at": TIMESTAMP,
        "url": "https://example.test/news/39358670",
        "content": "",
        "symbols": [symbol],
        "source": "benzinga",
    }


def take(
    bucket: List[Any],
    pending: MutableMapping[str, bool],
    name: str,
    ready: threading.Event,
) -> Callable[[Any], Any]:
    async def handler(message: Any) -> None:
        bucket.append(message)
        pending[name] = True
        if all(pending.values()):
            ready.set()

    return handler


def run_until(
    stream: Any, ready: threading.Event, unsubscribe: Callable[[], None]
) -> None:
    """Run ``stream`` until ``ready``, then unsubscribe and stop it."""
    failed: List[BaseException] = []

    def target() -> None:
        try:
            stream.run()
        except KeyboardInterrupt:
            raise
        except BaseException as exc:
            failed.append(exc)
            ready.set()

    thread = threading.Thread(target=target, name="consumer-stream")
    thread.start()
    try:
        if not ready.wait(10):
            raise AssertionError("market data stream produced no message")
        if not failed:
            unsubscribe()
    finally:
        stream.stop()
        thread.join(10)
    if failed:
        raise failed[0]
    if thread.is_alive():
        raise AssertionError("market data stream did not stop")
