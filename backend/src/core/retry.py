"""
Shared exponential backoff retry utility.

Usage:
    @retry(max_attempts=3, base_delay=1.0, retryable_on=(ConnectionError, TimeoutError))
    def my_func(): ...

    # or inline:
    result = retry_call(my_func, args, max_attempts=3)
"""
import time
import random
import logging
import functools
from typing import Callable, Tuple, Type, Any, Optional

logger = logging.getLogger("portfolio_assistant.retry")


def _should_retry(
    exc: Exception,
    retryable_on: Tuple[Type[Exception], ...],
    exclude_on: Tuple[Type[Exception], ...] = (),
) -> bool:
    if exclude_on and isinstance(exc, exclude_on):
        return False
    return isinstance(exc, retryable_on)


def retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    multiplier: float = 2.0,
    max_delay: float = 30.0,
    jitter: bool = True,
    retryable_on: Tuple[Type[Exception], ...] = (Exception,),
    exclude_on: Tuple[Type[Exception], ...] = (),
):
    """
    Decorator — retries the wrapped function with exponential backoff.

    Delay schedule (base=1s, multiplier=2, jitter=True):
      attempt 1 fail → wait ~1s
      attempt 2 fail → wait ~2s
      attempt 3 fail → wait ~4s  → raise
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            delay = base_delay
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except Exception as exc:
                    if attempt == max_attempts or not _should_retry(exc, retryable_on, exclude_on):
                        logger.error(
                            "%s failed (attempt %d/%d, non-retryable or max reached): %s",
                            fn.__qualname__, attempt, max_attempts, exc,
                        )
                        raise
                    sleep = min(delay + (random.uniform(0, 0.5) if jitter else 0), max_delay)
                    logger.warning(
                        "%s failed (attempt %d/%d): %s — retrying in %.1fs",
                        fn.__qualname__, attempt, max_attempts, exc, sleep,
                    )
                    time.sleep(sleep)
                    delay = min(delay * multiplier, max_delay)
        return wrapper
    return decorator


def retry_call(
    fn: Callable,
    args: tuple = (),
    kwargs: dict = None,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    multiplier: float = 2.0,
    max_delay: float = 30.0,
    jitter: bool = True,
    retryable_on: Tuple[Type[Exception], ...] = (Exception,),
    exclude_on: Tuple[Type[Exception], ...] = (),
) -> Any:
    """Inline retry without decorator — useful for lambdas or dynamic calls."""
    kwargs = kwargs or {}
    delay = base_delay
    for attempt in range(1, max_attempts + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            if attempt == max_attempts or not _should_retry(exc, retryable_on, exclude_on):
                raise
            sleep = min(delay + (random.uniform(0, 0.5) if jitter else 0), max_delay)
            logger.warning(
                "%s failed (attempt %d/%d): %s — retrying in %.1fs",
                getattr(fn, "__qualname__", str(fn)), attempt, max_attempts, exc, sleep,
            )
            time.sleep(sleep)
            delay = min(delay * multiplier, max_delay)
