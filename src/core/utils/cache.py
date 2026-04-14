import logging
from functools import wraps

from async_lru import alru_cache
from bakit.utils import metrics

log = logging.getLogger(__name__)


def tracked_alru_cache(*cache_args, **cache_kwargs):
    """Decorator that wraps alru_cache and tracks hit/miss statistics.

    Works for:
        - async standalone functions
        - async instance methods
        - async class methods

    Metric naming:
        - function: get_price.cache.hit
        - instance method: TokenService.get_token.cache.hit
        - class method: TokenService.get_chain_name.cache.hit
    """

    def decorator(func):
        cached_func = alru_cache(*cache_args, **cache_kwargs)(func)

        @wraps(func)
        async def wrapper(*args, **kwargs):
            before = cached_func.cache_info().hits
            result = await cached_func(*args, **kwargs)
            after = cached_func.cache_info().hits

            # Detect whether this is actually a bound method
            qualname_parts = func.__qualname__.split(".")
            is_method = len(qualname_parts) > 1

            if is_method:
                class_name = qualname_parts[-2]
                metric_name = f"{class_name}.{func.__name__}"
            else:
                metric_name = func.__name__

            if after > before:
                log.debug(f"{metric_name}.cache.hit")
                metrics.increment(f"{metric_name}.cache.hit")
            else:
                log.debug(f"{metric_name}.cache.miss")
                metrics.increment(f"{metric_name}.cache.miss")

            return result

        wrapper.cache_clear = cached_func.cache_clear
        wrapper.cache_info = cached_func.cache_info

        return wrapper

    return decorator
