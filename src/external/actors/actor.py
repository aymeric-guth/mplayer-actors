from typing import TypeVar, Any, Optional, Union
import logging
from dataclasses import dataclass
import threading

from .base_actor import BaseActor, ActorGeneric
from .message import Message, MsgCtx
from .sig import Sig
from .actor_system import actor_system, send, create, ActorSystem
from .errors import DispatchError, ActorException
from .subsystems.observable_properties import ObservableProperties, Observable
from ...utils import try_not, to_kebab_case, to_snake_case


T = TypeVar('T', bound='Actor')



class Actor(BaseActor):
    def __init__(self, pid: int, parent: int, name:str='', **kwargs) -> None:
        super().__init__(pid, parent=parent, name=name)
        self.kwargs = kwargs.copy()
        self.obs = ObservableProperties()

    def dispatch(self, sender: int, msg: Message) -> None:
        match msg:
            case Message(sig=Sig.INIT):
                self.init()
            case Message(sig=Sig.EXIT):
                self.terminate()
            case Message(sig=Sig.POISON):
                self.poison()
            case Message(sig=Sig.CHILD_INIT, args=pid):
                self.child = pid
                send(to=self.child, what=Message(sig=Sig.INIT))
            case Message(sig=Sig.CHILD_DEINIT, args=pid):
                self.child = 0
            case Message(sig=Sig.SUBSCRIBE, args=name):
                self.register(sender, name)
            case Message(sig=Sig.UNSUBSCRIBE, args=name):
                self.unregister(sender, name)
            case _:
                return
        raise DispatchError

    def init(self) -> None:
        ...

    def terminate(self) -> None:
        # send(to=0, what=Message(sig=Sig.EXIT))
        raise SystemExit

    def register(self, sender: int, name: str) -> None:
        try:
            prop = getattr(self, to_snake_case(name))
        except Exception:
            return
        if isinstance(prop, Observable):
            self.obs.register(to_snake_case(name), sender)

    def unregister(self, sender: int, name: str) -> None:
        try:
            prop = getattr(self, to_snake_case(name))
        except Exception:
            return
        if isinstance(prop, Observable):
            self.obs.unregister(to_snake_case(name), sender)

    def poison(self) -> None:
        raise ActorException('Sig.POISON')

    def handler(self, err: str) -> None:
        self.logger.error(f'Actor={self!r} encountered a failure: {err}')
        send(to=0, what=Message(sig=Sig.SIGINT))

    def sysexit_handler(self) -> None:
        send(to=0, what=Message(sig=Sig.EXIT))
        raise SystemExit

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
