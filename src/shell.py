# ruff: noqa: E402
from bakit import init_bakit

from core.settings import APP_NAME, configure_settings

init_bakit(APP_NAME, configure_settings, env_overrides={"APP_LOG_LEVEL": "INFO"})

from bakit.shell import start_ipython_shell

from core import models


def shell():
    extra_ns = {}

    # Expose all models directly in the shell
    extra_ns.update(models.__dict__)

    start_ipython_shell(extra_ns=extra_ns)


if __name__ == "__main__":
    shell()
