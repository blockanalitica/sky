import logging
from datetime import UTC, datetime

from async_lru import alru_cache

from core.sources.blockchain import get_chain
from core.utils.db import fetch_one_sql

log = logging.getLogger(__name__)


async def _get_block_from_chain(block_number, network):
    chain = get_chain(network)
    info = chain.get_block_info(block_number)
    return {
        "block_number": block_number,
        "timestamp": int(info["timestamp"]),
        "block_hash": info["hash"].to_0x_hex(),
        "datetime": datetime.fromtimestamp(int(info["timestamp"]), tz=UTC),
    }


@alru_cache(maxsize=1)
async def get_block(block_number, network):
    sql = f"""
        SELECT
              timestamp
            , block_hash
        FROM blocks_block{network}
        WHERE block_number = %(block_number)s
    """
    block = await fetch_one_sql(sql, {"block_number": block_number}, db_alias="sink")

    # If sink is not up to date, get block from chain as a backup
    if not block:
        return await _get_block_from_chain(block_number, network)

    block["block_number"] = block_number
    block["datetime"] = datetime.fromtimestamp(block["timestamp"], tz=UTC)
    return block


@alru_cache(maxsize=1)
async def get_block_by_timestamp(timestamp, network):
    if not isinstance(timestamp, int):
        raise TypeError("timestamp must be an integer")

    sql = f"""
        SELECT
              block_number
            , timestamp
            , block_hash
        FROM blocks_block{network}
        WHERE timestamp <= %(timestamp)s
        ORDER BY timestamp DESC
        LIMIT 1
    """
    block = await fetch_one_sql(sql, {"timestamp": timestamp}, db_alias="sink")
    block["timestamp"] = timestamp
    block["datetime"] = datetime.fromtimestamp(timestamp, tz=UTC)
    return block
