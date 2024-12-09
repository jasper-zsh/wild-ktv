import asyncio
import logging

def call_async(coro, logger=logging):
    def cb(*args):
        logger.info(f'async callback: {args}')
    task = asyncio.create_task(coro)
    task.add_done_callback(cb)
    return task