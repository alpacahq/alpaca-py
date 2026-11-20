import asyncio
import logging
from typing import Any, Coroutine


def send_subscription(
    coroutine: Coroutine[Any, Any, None],
    loop: asyncio.AbstractEventLoop,
    tasks: set[asyncio.Task],
    logger: logging.Logger,
) -> None:
    """Schedule a stream-loop send, or wait for it when called from another thread."""
    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        current_loop = None
    if current_loop is not None and current_loop is loop:
        # A handler runs on this loop; waiting for its own future deadlocks it.
        try:
            task = loop.create_task(coroutine)
        except BaseException:
            coroutine.close()
            raise
        tasks.add(task)

        def subscription_done(task: asyncio.Task) -> None:
            tasks.discard(task)
            if not task.cancelled() and task.exception() is not None:
                logger.error("subscription update failed", exc_info=task.exception())

        task.add_done_callback(subscription_done)
    else:

        async def tracked_send() -> None:
            # Register on the stream loop so close() can cancel cross-thread
            # sends too, without mutating its task set from another thread.
            task = asyncio.current_task()
            assert task is not None
            tasks.add(task)
            try:
                await coroutine
            finally:
                tasks.discard(task)

        send = tracked_send()
        try:
            future = asyncio.run_coroutine_threadsafe(send, loop)
        except BaseException:
            send.close()
            coroutine.close()
            raise
        # Cancellation before tracked_send starts never reaches its await.
        # This private future completes after the scheduled task is done, so
        # closing the original coroutine here is safe even on that path.
        future.add_done_callback(lambda _: coroutine.close())
        future.result()
