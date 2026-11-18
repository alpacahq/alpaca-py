"""Public subscription methods must not block a market-data callback's loop."""

import asyncio
import subprocess
import sys
import textwrap

import pytest

from alpaca.data.live import CryptoDataStream


def test_subscription_changes_from_market_data_callback():
    script = textwrap.dedent("""
        import asyncio
        import msgpack
        from alpaca.data.live import CryptoDataStream

        async def main():
            stream = CryptoDataStream("test-key", "test-secret", raw_data=True)
            messages = []
            sent = asyncio.Event()

            class Socket:
                async def send(self, frames):
                    payload = frames if isinstance(frames, bytes) else b"".join(frames)
                    messages.append(msgpack.unpackb(payload))
                    if len(messages) == 2:
                        sent.set()

            async def other_handler(data):
                pass

            async def handler(data):
                stream.subscribe_quotes(other_handler, "ETH/USD")
                stream.unsubscribe_quotes("BTC/USD")

            stream.subscribe_quotes(handler, "BTC/USD")
            stream._loop = asyncio.get_running_loop()
            stream._ws = Socket()
            stream._running = True
            await stream._dispatch({"T": "q", "S": "BTC/USD"})
            await asyncio.wait_for(sent.wait(), 2)
            assert messages == [
                {"quotes": ["ETH/USD"], "action": "subscribe"},
                {"action": "unsubscribe", "quotes": ["BTC/USD"]},
            ]
            assert "BTC/USD" not in stream._handlers["quotes"]
            await asyncio.to_thread(stream.subscribe_quotes, other_handler, "SOL/USD")
            assert messages[-1]["quotes"] == ["ETH/USD", "SOL/USD"]

        asyncio.run(main())
    """)
    result = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.asyncio
async def test_close_cancels_pending_subscription_sends():
    stream = CryptoDataStream("test-key", "test-secret")
    entered, cancelled, closed = asyncio.Event(), asyncio.Event(), asyncio.Event()

    class Socket:
        async def send(self, frames):
            entered.set()
            try:
                await asyncio.Event().wait()
            finally:
                cancelled.set()

        async def close(self):
            closed.set()

    async def handler(data):
        pass

    stream._loop = asyncio.get_running_loop()
    stream._running = True
    stream._ws = Socket()
    stream.subscribe_quotes(handler, "BTC/USD")
    await asyncio.wait_for(entered.wait(), 1)
    await asyncio.wait_for(stream.close(), 1)
    assert cancelled.is_set()
    assert closed.is_set()
    assert not stream._subscription_tasks


@pytest.mark.asyncio
async def test_callback_subscription_errors_are_logged(caplog):
    stream = CryptoDataStream("test-key", "test-secret")
    sent = asyncio.Event()

    class Socket:
        async def send(self, frames):
            sent.set()
            raise OSError("send failed")

    async def handler(data):
        pass

    stream._loop = asyncio.get_running_loop()
    stream._running = True
    stream._ws = Socket()
    stream.subscribe_quotes(handler, "BTC/USD")
    await asyncio.wait_for(sent.wait(), 1)
    await asyncio.sleep(0)
    assert "subscription update failed" in caplog.text
    assert "send failed" in caplog.text
    assert not stream._subscription_tasks
