from typing import TypeVar, Any, Optional
import logging

from .base_actor import BaseActor, ActorGeneric
from .message import Message
from .sig import Sig
from .actor_system import actor_system


T = TypeVar('T', bound='Actor')


class Actor(BaseActor):
    def __init__(self, pid: int, parent: ActorGeneric, name:str='', **kwargs) -> None:
        super().__init__(pid, parent=parent, name=name)
        # self._parent: Optional[BaseActor] = actor_system.get_actor(parent)
        self.kwargs = kwargs.copy()

    def handler(self, err: str) -> None:
        self.logger.error(f'Actor={self} encountered a failure: {err}')
        actor_system.post(Message(sig=Sig.SIGINT))

    def introspect(self) -> dict[Any, Any]:
        return {
            'actor': repr(self),
            'log_lvl': self.log_lvl,
        }.copy()

    def terminate(self) -> None:
        raise SystemExit('SIGQUIT')

    # def __repr__(self) -> str:
    #     return f'{self.__class__.__name__}(pid={self.pid}, parent={self.parent})'#, kwargs={self.kwargs}

