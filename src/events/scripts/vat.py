import logging
import time

import asyncclick as click

from core.sources.blockchain import get_chain_async
from core.utils.processors import delete_key
from events.pipeline.processors.vat import EventVatProcessor

log = logging.getLogger(__name__)


async def run():
    async with get_chain_async("ethereum") as chain:
        start = time.time()
        await delete_key(EventVatProcessor.redis_key)
        to_block = await chain.get_latest_block()
        await EventVatProcessor(chain, to_block=to_block).sync()
        end = time.time()
        click.echo(f"Time taken: {end - start} seconds")


@click.command()
async def cmd():
    await run()
