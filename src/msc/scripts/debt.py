import logging
import time

import asyncclick as click

from core.sources.blockchain import get_chain_async
from msc.models import MSCItemSnapshot
from msc.pipeline.processors.debt import MSCDebtSnapshotManager

log = logging.getLogger(__name__)


async def run(should_delete=True):
    async with get_chain_async("ethereum") as chain:
        if should_delete:
            await MSCItemSnapshot.all().delete()
        start = time.time()
        await MSCDebtSnapshotManager(chain).sync()
        end = time.time()
        click.echo(f"Time taken: {end - start} seconds")


@click.command()
@click.option(
    "--delete/--no-delete",
    "should_delete",
    default=True,
    help="Delete existing MSC item snapshots before syncing.",
)
async def cmd(should_delete):
    await run(should_delete=should_delete)
