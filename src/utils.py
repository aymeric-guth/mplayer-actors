from typing import Any, Union, Callable
from functools import wraps

def clamp(
    lo: int|float, 
    hi: int|float
) -> Callable[[int|float], int|float]:
    def inner(val: int|float) -> int|float:
        return max(lo, min(val, hi))
    return inner
