import settings
from arq import create_pool
from arq.connections import RedisSettings

redis_settings = RedisSettings(
    host=settings.ARQ_REDIS_HOST,
    port=settings.ARQ_REDIS_PORT,
    database=settings.ARQ_REDIS_DB,
)


async def enqueue_job(fn_name, *args, **kwargs):
    redis = await create_pool(redis_settings)
    await redis.enqueue_job(fn_name, *args, **kwargs)
