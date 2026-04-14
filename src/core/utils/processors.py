from datetime import UTC, datetime

import redis.asyncio as redis
from bakit import settings


class BaseProcessor:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_datetime = datetime.now(UTC)
        self.current_date = self.current_datetime.date()


class BaseSnapshotsManager:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_datetime = datetime.now(tz=UTC)
        self.current_date = self.current_datetime.date()


class NetworkProcessor(BaseProcessor):
    def __init__(self, chain_async, to_block=None, network=None, from_block=None, *args, **kwargs):
        self.from_block = from_block
        self.to_block = to_block
        self.chain_async = chain_async
        self.network = network or chain_async.chain
        super().__init__()


async def get_redis_client():
    pool = redis.ConnectionPool(
        host=settings.ARQ_REDIS_HOST,
        port=settings.ARQ_REDIS_PORT,
        db=settings.ARQ_REDIS_DB,
        decode_responses=True,
    )
    return redis.Redis(connection_pool=pool)


async def get_latest_block(key):
    redis = await get_redis_client()
    result = await redis.get(key)
    if result:
        return int(result)
    return None


async def determine_last_processed_block(
    redis_key,
    model,
    first_block,
    block_field="block_number",
    order_field="order_index",
    default_block=0,
):
    """
    Determine the next `.from_block` for a processor using the stored Redis
    checkpoint, the latest cached entry, and a network-specific minimum.
    """
    redis_latest_block = await get_latest_block(redis_key) or default_block
    last_processed_block = default_block

    obj = await model.all().order_by(f"-{order_field}").first()
    if obj:
        last_processed_block = getattr(obj, block_field)

    return max(redis_latest_block, last_processed_block, first_block)


async def save_latest_block(key, block_number):
    redis = await get_redis_client()
    await redis.set(key, block_number)


async def delete_key(key):
    redis = await get_redis_client()
    await redis.delete(key)
