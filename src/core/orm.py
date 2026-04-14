# ruff: noqa: E402
from bakit import init_bakit

from core.settings import APP_NAME, configure_settings

init_bakit(APP_NAME, configure_settings)

from bakit import settings

TORTOISE_ORM = settings.TORTOISE_ORM
