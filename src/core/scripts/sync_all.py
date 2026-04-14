import time

import asyncclick as click
from tortoise import Tortoise

from agents.scripts.urns import run as run_agents
from events.scripts.ssr import run as run_event_ssr
from events.scripts.vat import run as run_event_vat
from msc.scripts.debt import run as run_msc


async def delete_all_models():
    for model in Tortoise.apps["core"].values():
        await model.all().delete()


@click.command()
@click.option(
    "--delete/--no-delete",
    "should_delete",
    default=False,
    help="Delete all existing model data before syncing.",
)
async def cmd(should_delete):
    start = time.time()

    if should_delete:
        click.echo("Deleting all model data...")
        await delete_all_models()

    click.echo("Running events processors...")
    await run_event_vat()
    await run_event_ssr()

    click.echo("Running agents processors...")
    await run_agents()

    click.echo("Running msc processors...")
    await run_msc()

    end = time.time()
    click.echo(f"All processors finished in {end - start} seconds")
