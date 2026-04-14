import contextlib
import logging
from contextlib import asynccontextmanager, contextmanager

from settings import TORTOISE_ORM
from tortoise import Tortoise
from tortoise.connection import connections
from tortoise.exceptions import IntegrityError

log = logging.getLogger(__name__)


async def chunk_generator(iterator, chunk_size):
    """
    Yield successive chunks from the async iterator.
    :param iterator: The input async iterator
    :param chunk_size: The target chunk size
    """
    current_chunk = []

    async for item in iterator:
        current_chunk.append(item)

        if len(current_chunk) >= chunk_size:
            yield current_chunk
            current_chunk = []

    # Yield the final chunk if it's not empty
    if current_chunk:
        yield current_chunk


def _convert_named_placeholders(sql, sql_vars):
    sql_vars = sql_vars or []
    if isinstance(sql_vars, dict):
        # Convert named placeholders (%(key)s) to $1, $2, ...
        param_count = 1
        for key in sql_vars:
            sql = sql.replace(f"%({key})s", f"${param_count}")
            param_count += 1
        sql_vars = list(sql_vars.values())
    return sql, sql_vars


async def fetch_one_sql(sql, sql_vars=None, db_alias="default"):
    sql, sql_vars = _convert_named_placeholders(sql, sql_vars)
    conn = connections.get(db_alias)
    rows = await conn.execute_query_dict(sql, sql_vars)
    return rows[0] if rows else {}


async def fetch_all_sql(sql, sql_vars=None, db_alias="default"):
    sql, sql_vars = _convert_named_placeholders(sql, sql_vars)
    conn = connections.get(db_alias)
    rows = await conn.execute_query_dict(sql, sql_vars)
    return rows


@asynccontextmanager
async def streaming_fetch_all_sql(sql, sql_vars=None, db_alias="default", prefetch=2000):
    """
    Example usage:
        async with streaming_fetch_all_sql(sql) as cursor:
            async for record in cursor:
                print(record)
    """
    sql_vars = sql_vars or []
    sql, sql_vars = _convert_named_placeholders(sql, sql_vars)
    db_client = connections.get(db_alias)

    async with db_client.acquire_connection() as con, con.transaction():
        cursor = con.cursor(sql, *sql_vars, prefetch=prefetch)
        yield cursor


@contextmanager
def suppress_duplicate_error():
    try:
        yield
    except IntegrityError as e:
        if "duplicate key value violates unique constraint" not in str(e):
            raise


@contextlib.asynccontextmanager
async def db_connect():
    """Context manager for initializing and closing database connections.

    Usage:
        async with db_connect():
            # Your database operations here
            await Model.all()
    """
    try:
        await Tortoise.init(config=TORTOISE_ORM)
        yield
    finally:
        await Tortoise.close_connections()
