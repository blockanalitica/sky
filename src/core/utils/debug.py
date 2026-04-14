import logging
import time
from contextlib import asynccontextmanager

log = logging.getLogger(__name__)


@asynccontextmanager
async def log_time(label):
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000
        log.info(f"{label} took {elapsed_ms:.1f} ms")
