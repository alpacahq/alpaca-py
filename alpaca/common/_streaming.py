import asyncio
import concurrent.futures
import logging
from typing import Any, Coroutine


def send_subscription(
    coroutine: Coroutine[Any, Any, None],
    loop: asyncio.AbstractEventLoop,
    tasks: set[asyncio.Task],
    logger: logging.Logger,
) -> None:
    """Schedule a stream-loop send, or wait for it when called from another thread.

    The task is registered on the stream loop before its coroutine runs, so a
    later ``close()`` can cancel it. Callers already running on that loop return
    immediately; waiting on their own task would deadlock it.
    """
    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        current_loop = None
    if current_loop is not None and current_loop is loop:
        # A handler runs on this loop; waiting for its own future deadlocks it.
        _track_subscription(coroutine, loop, tasks, logger)
        return

    waiter: concurrent.futures.Future[None] = concurrent.futures.Future()

    def schedule() -> None:
        # Register the task before this callback returns. The loop runs nothing
        # else until then, including the new coroutine and close(), which copies
        # the set as soon as it starts. A close() that begins afterwards always
        # sees this send.
        try:
            task = _track_subscription(coroutine, loop, tasks, None)
        except BaseException as exc:
            _reject_waiter(waiter, exc)
            return
        task.add_done_callback(lambda done: _relay_result(waiter, done))

    try:
        loop.call_soon_threadsafe(schedule)
    except BaseException:
        coroutine.close()
        raise
    waiter.result()


def _track_subscription(
    coroutine: Coroutine[Any, Any, None],
    loop: asyncio.AbstractEventLoop,
    tasks: set[asyncio.Task],
    logger: logging.Logger | None,
) -> asyncio.Task:
    try:
        task = loop.create_task(coroutine)
    except BaseException:
        coroutine.close()
        raise
    tasks.add(task)

    def subscription_done(done: asyncio.Task) -> None:
        tasks.discard(done)
        if logger is None or done.cancelled():
            return
        error = done.exception()
        if error is not None:
            logger.error("subscription update failed", exc_info=error)

    task.add_done_callback(subscription_done)
    return task


def _reject_waiter(waiter: concurrent.futures.Future[None], exc: BaseException) -> None:
    if not waiter.done():
        waiter.set_exception(exc)


def _relay_result(waiter: concurrent.futures.Future[None], done: asyncio.Task) -> None:
    if waiter.done():
        return
    if done.cancelled():
        waiter.cancel()
        return
    error = done.exception()
    if error is None:
        waiter.set_result(None)
    else:
        waiter.set_exception(error)
