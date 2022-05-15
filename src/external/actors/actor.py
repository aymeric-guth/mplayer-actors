from typing import TypeVar, Any, Optional
import logging

from .base_actor import BaseActor, ActorGeneric
from .message import Message
from .sig import Sig
from .actor_system import actor_system


T = TypeVar('T', bound='Actor')


class Actor(BaseActor):
    def __init__(self, pid: int, parent: int, name:str='', **kwargs) -> None:
        super().__init__(pid, parent=parent, name=name)
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

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(pid={self.pid})'
        # return f'{self.__class__.__name__}(pid={self.pid}, parent={actor_system.resolve_parent(self.parent)})'

    def log_mq(self, sender: Optional[int], msg: Message) -> None:
        if not isinstance(sender, int):
            self.logger.error(f'### MQ ###\nGot unexpected Sender={sender}, type={type(sender)}\nmsg={msg}')
        elif self.pid == sender:
            self.logger.info(f'### MQ ###\nself={self!r}\n{msg=}')
        else:
            self.logger.info(f'### MQ ###\nreceiver={self!r}\nsender={actor_system.resolve_parent(sender).__repr__()}\n{msg=}')

    def log_post(self, sender: Optional[int], msg: Message) -> None:
        if not isinstance(sender, int):
            self.logger.error(f'### POST ###\nGot unexpected Sender={sender}, type={type(sender)}\nmsg={msg}')
        elif self.pid == sender:
            self.logger.info(f'### POST ###\nself={self!r}\n{msg=}')
        else:
            self.logger.info(f'### POST ###\nreceiver={self!r}\nsender={actor_system.resolve_parent(sender).__repr__()}\n{msg=}')