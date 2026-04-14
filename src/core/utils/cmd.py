import asyncio
import functools

from settings import TORTOISE_ORM
from tortoise import Tortoise


def async_cmd(f):
    """
    A decorator that allows Click to run an async function.
    Usage:
        @click.command()
        @async_cmd
        async def cli(...):
            ...
    """

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


def with_db(f):
    @functools.wraps(f)
    async def wrapper(*args, **kwargs):
        await Tortoise.init(config=TORTOISE_ORM)
        try:
            return await f(*args, **kwargs)
        finally:
            await Tortoise.close_connections()

    return wrapper
