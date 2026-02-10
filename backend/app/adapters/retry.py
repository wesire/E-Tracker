"""Retry utility with exponential backoff."""

import asyncio
import logging
from functools import wraps
from typing import Any, Callable, Type, Tuple

logger = logging.getLogger(__name__)


def with_retry(
    max_attempts: int = 3,
    backoff_factor: int = 2,
    initial_delay: float = 1.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
):
    """Decorator to retry async functions with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        backoff_factor: Multiplier for delay between retries
        initial_delay: Initial delay in seconds
        exceptions: Tuple of exception types to catch and retry
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = initial_delay
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay}s..."
                        )
                        await asyncio.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}: {e}"
                        )

            raise last_exception

        return wrapper

    return decorator
