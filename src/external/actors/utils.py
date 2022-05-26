from typing import Callable, Any
from functools import wraps

from .actor_system import send
from .message import Event, Message, Sig


def observer(actor: str):
    def inner(func: Callable):
        @wraps(func)
        def _(*args, **kwargs):
            (self, *value) = args
            name = func.__name__
            func(self, *value)
            res = getattr(self, f'_{name}')
            send(to=actor, what=Message(sig=Sig.WATCHER, args={name: res}))
            # send(to=actor, what=Event(type='property-change', name=name, args=res))
        return _
    return inner

class Observable:
    def __init__(
        self, 
        name=None, 
        setter=lambda x: 0. if x is None else x
    ) -> None:
        self.name = name
        self.setter = setter

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name

    def __get__(self, instance: object, owner: type) -> object:
        if instance is None:
            return self
        return instance.__dict__[self.name]

    def __set__(self, instance: object, value: Any) -> None:
        instance.__dict__[self.name] = self.setter(value)
        try:
            obs = instance.__dict__['obs']
        except Exception as err:
            raise SystemExit
        obs.notify(self.name, instance.__dict__[self.name])
