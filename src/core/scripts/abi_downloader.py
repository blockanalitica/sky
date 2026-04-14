import asyncclick as click

from core.sources.blockchain import get_chain_async


# TODO: move to bakit?
@click.command()
@click.option(
    "-n",
    "--network",
)
@click.option("-a", "--address", help="Contract address")
async def cmd(network, address):
    async with get_chain_async(network) as chain:
        await chain.get_contract(address)
