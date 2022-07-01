from typing import Any
from functools import singledispatchmethod

from ...utils import SingletonMeta

from actors import Actor, Message, Sig, send, DispatchError



class Dummy(Actor):
    def __init__(self, pid: int, parent: int, name='', **kwargs) -> None:
        super().__init__(pid, parent, name, **kwargs)

    @singledispatchmethod
    def dispatch(self, sender: int, msg: Message) -> None:
        raise NotImplementedError

    @dispatch.register
    def _(self, sender: int, msg: dict[str, Any]) -> None:
        raise NotImplementedError
