"""Helpers for market-data websocket scenarios.

Live ticks are not deterministic, so the scenarios serve fixed frames
(``stub_websocket``) instead of connecting. ``run_until`` is the usual user
shape: subscribe, ``run`` until a handler has seen the messages, unsubscribe
from another thread (the stream loop must not call ``unsubscribe_*`` itself:
that waits on the same loop), then ``stop``.
"""

from __future__ import annotations

import threading
from typing import Any, Callable, Dict, List, Mapping, MutableMapping

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


# The crypto and option frames below follow the shapes of the REST recordings
# (crypto_data.latest_crypto_data_by_symbol, option_data.chain_then_latest_
# contract_data): the stream carries the same per-asset fields, so a model that
# only works for the stock shape must fail these scenarios.


def crypto_trade(symbol: str) -> Dict[str, Any]:
    # No exchange, conditions or tape; "tks" is the taker side.
    return {
        "T": "t",
        "S": symbol,
        "i": 8827103037403251704,
        "p": 74100.0,
        "s": 1.35e-05,
        "t": TIMESTAMP,
        "tks": "S",
    }


def crypto_quote(symbol: str) -> Dict[str, Any]:
    # No exchanges, conditions or tape.
    return {
        "T": "q",
        "S": symbol,
        "bp": 74062.27,
        "bs": 0.0009913,
        "ap": 74085.74,
        "as": 0.0010096,
        "t": TIMESTAMP,
    }


def option_trade(symbol: str) -> Dict[str, Any]:
    # No trade id or tape; the condition is a single string, not a list.
    return {
        "T": "t",
        "S": symbol,
        "x": "I",
        "p": 132.38,
        "s": 6,
        "c": "f",
        "t": TIMESTAMP,
    }


def option_quote(symbol: str) -> Dict[str, Any]:
    # No tape; the condition is a string.
    return {
        "T": "q",
        "S": symbol,
        "bx": "X",
        "bp": 140.28,
        "bs": 175,
        "ax": "I",
        "ap": 142.05,
        "as": 17,
        "c": " ",
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
    stream: Any,
    ready: threading.Event,
    unsubscribe: Callable[[], None],
    pending: Mapping[str, bool],
) -> None:
    """Run ``stream`` until ``ready``, then unsubscribe and stop it.

    ``pending`` is the mapping given to ``take``: on timeout it names the
    channels that never delivered a message.
    """
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
            missing = sorted(name for name, seen in pending.items() if not seen)
            raise AssertionError(f"no message reached the handlers for: {missing}")
        if not failed:
            unsubscribe()
    finally:
        stream.stop()
        thread.join(10)
    if failed:
        raise failed[0]
    if thread.is_alive():
        raise AssertionError("market data stream did not stop")
