import logging

import asyncclick as click
from bakit.utils.db import fetch_all_sql
from chain_harvester.utils import chunks, normalize_to_decimal
from eth_utils import to_bytes

from agents.models import Agent, AgentUrnEventState
from core.constants import VAT_ADDRESS
from core.sources.blockchain import get_chain_async

log = logging.getLogger(__name__)


@click.command()
@click.option("--ilk", type=str)
async def cmd(ilk):
    latest = await AgentUrnEventState.all().order_by("-block_number").first()
    if latest is None:
        click.echo("No AgentUrnEventState rows found; run `agents urns` first.")
        return
    max_block = latest.block_number
    click.echo(f"MAX BLOCK: {max_block}")

    agents = await Agent.all()
    sql = f"""
        SELECT DISTINCT ON (urn)
                  urn
                , ink
                , art
        FROM {AgentUrnEventState.db_table()}
        WHERE ilk=%(ilk)s
        ORDER BY urn, order_index DESC
        """

    for agent in agents:
        current_ilk = agent.ilk
        calls = []
        data = await fetch_all_sql(sql, {"ilk": current_ilk})
        for item in data:
            urn = item["urn"]
            ink = item["ink"]
            art = item["art"]
            calls.append(
                (
                    VAT_ADDRESS,
                    [
                        "urns(bytes32,address)((uint256,uint256))",
                        to_bytes(text=current_ilk),
                        urn,
                    ],
                    [f"{current_ilk}::{urn.lower()}", None],
                )
            )

        async with get_chain_async("ethereum") as chain:
            for chunk in chunks(calls, 5000):
                log.info(f"Checking {current_ilk}")
                data = await chain.multicall(chunk, block_identifier=max_block)
                for key, values in data.items():
                    ilk, urn = key.split("::")
                    ink, art = values
                    vault = (
                        await AgentUrnEventState.filter(ilk=ilk, urn=urn)
                        .order_by("-order_index")
                        .first()
                    )
                    chain_ink = normalize_to_decimal(ink, 18)
                    chain_art = normalize_to_decimal(art, 18)

                    if vault.ink != chain_ink:
                        log.info(f"Wrong ink for {ilk} {urn} {vault.ink} {chain_ink}")

                    if vault.art != chain_art:
                        log.info(f"Wrong art for {ilk} {urn} {vault.art} {chain_art}")
