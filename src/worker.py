# ruff: noqa: E402
from bakit import init_bakit

from core.settings import APP_NAME, configure_settings

init_bakit(APP_NAME, configure_settings)

from bakit.arq.task_loader import collect_cron_jobs_and_functions
from bakit.arq.worker import build_worker

from core.utils.tasks import redis_settings

TASK_PACKAGES = [
    "core",
]

CRON_JOBS, FUNCTIONS = collect_cron_jobs_and_functions(TASK_PACKAGES)


ARQWorker = build_worker(
    {
        "redis_settings": redis_settings,
        "functions": FUNCTIONS,
        "cron_jobs": CRON_JOBS,
    }
)
