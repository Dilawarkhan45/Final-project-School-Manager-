"""A small retry decorator."""

from __future__ import annotations

import functools
import logging
import time
from typing import Callable, ParamSpec, TypeVar

logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


def retry(
    attempts: int = 3,
    delay: float = 0.5,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Call the function again if it raises, up to `attempts` times in total."""

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            for attempt in range(1, attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as error:
                    logger.warning(
                        "%s failed (attempt %d/%d): %s", func.__name__, attempt, attempts, error
                    )
                    time.sleep(delay)
            return func(*args, **kwargs)  # last attempt: let any error escape

        return wrapper

    return decorator
