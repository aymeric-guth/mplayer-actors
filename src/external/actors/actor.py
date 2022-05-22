from typing import TypeVar, Any, Optional, Union
import logging
from dataclasses import dataclass
import threading

from .base_actor import BaseActor, ActorGeneric
from .message import Message, MsgCtx
from .sig import Sig
from .actor_system import actor_system, send, create
from .errors import DispatchError, ActorException


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

            case Message(sig=Sig.CHILD_INIT, args=pid):
                self.child = pid
                if self.child:
                    send(self.child, Message(sig=Sig.INIT))
                raise DispatchError

            case _:
                ...

    def init(self) -> None:
        ...

    def terminate(self) -> None:
        send(to=0, what=Message(sig=Sig.EXIT))
        raise SystemExit('SIGQUIT')

    def poison(self) -> None:
        raise ActorException('Sig.POISON')

    def handler(self, err: str) -> None:
        self.logger.error(f'Actor={self!r} encountered a failure: {err}')
        send(0, Message(sig=Sig.SIGINT))

    def dispatch_handler(self, sender: int, message: Message|dict[str, Any]) -> None:
        ctx = MsgCtx(
            original_sender=sender,
            original_recipient=self.pid,
            message=message
        )
        send(0, Message(sig=Sig.DISPATCH_ERROR, args=ctx))

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


class ActorIO(Actor):
    def __init__(self, pid: int, parent: int, name:str='', **kwargs) -> None:
        super().__init__(pid, parent=parent, name=name)
        self.kwargs = kwargs.copy()

    def _run(self) -> None:
        raise NotImplementedError

    def err_handler(self, err: str) -> None:
        self.logger.error(f'Actor={self} encountered a failure: {err}')

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(pid={self.pid}, parent={actor_system.resolve_parent(self.parent)})'
