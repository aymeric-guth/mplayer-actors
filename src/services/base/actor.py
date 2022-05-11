from typing import TypeVar, Any, Optional
import logging

from .base_actor import BaseActor, ActorGeneric
from .message import Message
from .sig import Sig
from .actor_system import actor_system


T = TypeVar('T', bound='Actor')


class Actor(BaseActor):
    def __init__(self, pid: int, name:str='', parent: Optional[ActorGeneric]=None, **kwargs) -> None:
        super().__init__(pid, name)
        self._parent: Optional[BaseActor] = actor_system.get_actor(parent)
        self.kwargs = kwargs.copy()
        # self.log_lvl = logging.INFO

    def handler(self, err) -> None:
        self.logger.error(f'Actor={self} encountered a failure: {err}')
        actor_system.post(Message(sig=Sig.SIGINT, args=err))

    def introspect(self) -> dict[Any, Any]:
        return {
            'actor': repr(self),
            'log_lvl': self.log_lvl,
        }.copy()

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(pid={self.pid}, parent={actor_system.get_actor(self.parent)})'#, kwargs={self.kwargs}

    @property
    def parent(self) -> Optional[BaseActor]:
        return self._parent

    @parent.setter
    def parent(self, value) -> None:
        raise TypeError