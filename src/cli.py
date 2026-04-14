# ruff: noqa: E402
import asyncclick as click
from bakit import init_bakit

from core.settings import APP_NAME, configure_settings

init_bakit(APP_NAME, configure_settings, env_overrides={"APP_LOG_LEVEL": "DEBUG"})

from bakit.cli import BakitGroup, autodiscover_and_attach


@click.group(cls=BakitGroup)
def cli():
    """CLI"""


autodiscover_and_attach(__file__, cli)


if __name__ == "__main__":
    cli(_anyio_backend="asyncio")
