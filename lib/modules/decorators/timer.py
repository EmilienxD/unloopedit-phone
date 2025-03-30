"""
This module provides custom decorators for enhancing function behavior.
It includes a timer decorator for measuring execution time and a time limiter decorator for enforcing execution time limits.

Classes:
-------
    TimeLimitException: Custom exception raised when a function exceeds its time limit.

Decorators:
----------
    timer: Measures and prints the execution time of a function.
    time_limiter: Enforces a time limit on a function's execution.
"""

from time import time
from functools import wraps


def timer(func: callable):
    """
    Decorator that measures and prints the execution time of a function.

    Parameters:
    ----------
        func (callable): The function to be decorated.

    Returns:
    -------
        callable: The decorated function.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time()
        result = func(*args, **kwargs)
        m, s = divmod(round(time() - start_time), 60)
        print(f"\nTime taken by '{func.__name__}': {m} min {s} sec.\n")
        return result
    return wrapper

