from typing import TypeVar, Any, Optional, Union
import logging

from .base_actor import BaseActor, ActorGeneric
from .message import Message
from .sig import Sig
from .actor_system import actor_system, send, create
from .errors import DispatchError


T = TypeVar('T', bound='Actor')


class Actor(BaseActor):
    def __init__(self, pid: int, parent: int, name:str='', **kwargs) -> None:
        super().__init__(pid, parent=parent, name=name)
        self.kwargs = kwargs.copy()

    def dispatch(self, sender: int, msg: Message) -> None:
        match msg:
            case Message(sig=Sig.INIT):
                self.init()
                raise DispatchError

            case Message(sig=Sig.EXIT):
                self.terminate()
                raise DispatchError

            case Message(sig=Sig.POISON):
                self.poison()
                raise DispatchError

            case _:
                ...

    def terminate(self) -> None:
        raise SystemExit('SIGQUIT')

    def init(self) -> None:
        ...

    def poison(self) -> None:
        ...

    def handler(self, err: str) -> None:
        self.logger.error(f'Actor={self} encountered a failure: {err}')

    def introspect(self) -> dict[Any, Any]:
        return {
            'actor': repr(self),
            'log_lvl': self.log_lvl,
        }.copy()

    def __repr__(self) -> str:
        # return f'{self.__class__.__name__}(pid={self.pid})'
        return f'{self.__class__.__name__}(pid={self.pid}, parent={actor_system.resolve_parent(self.parent)})'

    def __str__(self) -> str:
        return f'{self.__class__.__name__}(pid={self.pid}, parent={actor_system.resolve_parent(self.parent)})'


class ActorIO(BaseActor):
    def __init__(self, pid: int, parent: int, name:str='', **kwargs) -> None:
        super().__init__(pid, parent=parent, name=name)
        self.kwargs = kwargs.copy()

    def err_handler(self, err: str) -> None:
        self.logger.error(f'Actor={self} encountered a failure: {err}')
        # actor_system.post(Message(sig=Sig.SIGINT))

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(pid={self.pid}, parent={actor_system.resolve_parent(self.parent)})'
