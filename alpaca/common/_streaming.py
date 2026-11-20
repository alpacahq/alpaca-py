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
        task = loop.create_task(coroutine)
        tasks.add(task)

        def subscription_done(task: asyncio.Task) -> None:
            tasks.discard(task)
            if not task.cancelled() and task.exception() is not None:
                logger.error("subscription update failed", exc_info=task.exception())

        task.add_done_callback(subscription_done)
    else:
        asyncio.run_coroutine_threadsafe(coroutine, loop).result()
