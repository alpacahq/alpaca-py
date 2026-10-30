"""RunState: the per-run stop/wakeup state shared by the websocket streams."""

import asyncio
import threading
import time

import pytest

from alpaca.common.utils import RunState


def test_wake_before_the_run_starts_is_a_safe_no_op():
    """A reserved run has no loop yet; waking it must not raise, and the stop
    must still be visible once the run starts and checks it."""
    run = RunState()

    run.request_stop()

    assert run.wake() is False
    assert run.stopping


def test_wake_after_the_loop_closed_returns_false():
    loop = asyncio.new_event_loop()
    loop.close()

    assert RunState(loop).wake() is False


@pytest.mark.asyncio
async def test_sleep_waits_out_the_delay_when_not_stopped():
    loop = asyncio.get_running_loop()
    run = RunState(loop)

    began = loop.time()
    await run.sleep(0.05)

    assert loop.time() - began >= 0.045


@pytest.mark.asyncio
async def test_sleep_returns_immediately_when_already_stopped():
    loop = asyncio.get_running_loop()
    run = RunState(loop)
    run.request_stop()

    await asyncio.wait_for(run.sleep(30), timeout=0.5)


@pytest.mark.asyncio
async def test_sleep_returns_early_on_a_stop_from_another_thread():
    loop = asyncio.get_running_loop()
    run = RunState(loop)

    def stop_soon():
        time.sleep(0.05)
        run.request_stop()
        run.wake()

    threading.Thread(target=stop_soon).start()
    began = loop.time()
    await asyncio.wait_for(run.sleep(30), timeout=2)

    assert loop.time() - began < 1


@pytest.mark.asyncio
async def test_a_wake_without_a_stop_does_not_cut_sleep_short():
    """subscribe() wakes the run too; during a reconnect backoff that must not
    end the backoff early."""
    loop = asyncio.get_running_loop()
    run = RunState(loop)
    loop.call_later(0.01, run.wake)

    began = loop.time()
    await run.sleep(0.1)

    assert loop.time() - began >= 0.095
    assert not run.stopping
