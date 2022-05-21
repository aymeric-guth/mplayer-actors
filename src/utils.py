from typing import Any, Union, Callable
from functools import wraps

def clamp(
    lo: int|float, 
    hi: int|float
) -> Callable[[int|float], int|float]:
    def inner(val: int|float) -> int|float:
        return max(lo, min(val, hi))
    return inner


class SingletonMeta(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


def try_not(fnc, exc) -> Callable:
    def inner(*args, **kwargs) -> None:
        try:
            fnc(*args, **kwargs)
        except exc:
            ...
    return inner
