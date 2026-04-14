import logging
import time

import asyncclick as click

from agents.models import Agent
from agents.pipeline.processor.urn_states import AgentUrnStatesProcessor

log = logging.getLogger(__name__)


async def run():
    agents = [
        {"slug": "spark", "name": "Spark", "ilk": "ALLOCATOR-SPARK-A"},
        {"slug": "grove", "name": "Grove", "ilk": "ALLOCATOR-BLOOM-A"},
        {"slug": "obex", "name": "Obex", "ilk": "ALLOCATOR-OBEX-A"},
    ]

    for agent in agents:
        await Agent.get_or_create(slug=agent["slug"], name=agent["name"], ilk=agent["ilk"])

    start = time.time()
    await AgentUrnStatesProcessor().sync()
    end = time.time()
    click.echo(f"Time taken: {end - start} seconds")


@click.command()
async def cmd():
    await run()
