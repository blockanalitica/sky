import logging
from datetime import UTC, datetime

from bakit.utils.db import fetch_all_sql, fetch_one_sql
from chain_harvester_async.blocks import BlockStore
from hexbytes import HexBytes

from core.models import Block
from core.utils.cache import tracked_alru_cache

log = logging.getLogger(__name__)


class SkyBlockStore(BlockStore):
    @tracked_alru_cache(maxsize=1)
    async def get_blocks_by_numbers(self, chain_id, block_numbers):
        sql = f"""
            SELECT
                  number
                , timestamp
                , hash
            FROM {Block.db_table()}
            WHERE chain_id = %(chain_id)s
                AND number = ANY(%(block_numbers)s)
        """
        db_blocks = await fetch_all_sql(sql, {"chain_id": chain_id, "block_numbers": block_numbers})
        blocks = {}
        for block in db_blocks:
            blocks[block["number"]] = {
                "number": block["number"],
                "hash": HexBytes(block["hash"]),
                "timestamp": block["timestamp"],
                "datetime": datetime.fromtimestamp(block["timestamp"], tz=UTC),
            }
        return blocks

    async def save_blocks(self, chain_id, blocks):
        block_objects = []
        for block in blocks:
            block_objects.append(
                Block(
                    chain_id=chain_id,
                    number=block["number"],
                    hash=block["hash"],
                    timestamp=block["timestamp"],
                )
            )

        if block_objects:
            # We store the latest block if/when reorg happens
            await Block.bulk_create(
                block_objects,
                update_fields=["hash"],
                on_conflict=Block._meta.unique_together[0],
            )

    @tracked_alru_cache(maxsize=1)
    async def get_block_by_number(self, chain_id, block_number):
        sql = f"""
            SELECT
                  number
                , timestamp
                , hash
            FROM {Block.db_table()}
            WHERE chain_id = %(chain_id)s
                AND number = %(block_number)s
        """
        block = await fetch_one_sql(sql, {"chain_id": chain_id, "block_number": block_number})
        if not block:
            return None
        return {
            "number": block["number"],
            "hash": HexBytes(block["hash"]),
            "timestamp": block["timestamp"],
            "datetime": datetime.fromtimestamp(block["timestamp"], tz=UTC),
        }
