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
