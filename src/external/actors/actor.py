from typing import TypeVar, Any, Optional, Union
import logging
from dataclasses import dataclass
import threading

from .base_actor import BaseActor, ActorGeneric
from .message import Message, MsgCtx, Event, Request, Response
from .sig import Sig
from .actor_system import actor_system, send, create, ActorSystem
from .errors import DispatchError, ActorException, SystemMessage
from .subsystems.observable_properties import ObservableProperties
from ...utils import try_not, to_kebab_case, to_snake_case
from .utils import Observable

from .dispatcher import dispatch as dispatcher


T = TypeVar('T', bound='Actor')

@dispatcher
def f(a: int, b: int):
    ...

@dispatcher
def f(a: list[int], b: list[int]):
    ...

class Actor(BaseActor):
    def __init__(self, pid: int, parent: int, name:str='', **kwargs) -> None:
        super().__init__(pid, parent=parent, name=name)
        self.kwargs = kwargs.copy()
        self.obs = ObservableProperties()

    # def _dispatch(self, sender: int, msg: Message) -> None:
    #     match msg:
    #         case System:
    #             ...
    #         case SubSystem:
    #             ...
    #         case Event|Request|Response:
    #             ...
    #         case _:
    #             ...
    # def _dispatch(self, sender: int, msg: System) -> None:
    #     # implemented at framework level
    #     # generic behavior for creating, terminating, child allocation, 
    #     ...
    # def _dispatch(self, sender: int, msg: SubSystem) -> None:
    #     # implemented at ??? level
    #     # fine-grained control over SubSystem (logging level, cache duration, ...)
    #     ...
    # def _dispatch(self, sender: int, msg: Event | Request | Response) -> None:
    #     # implemented at application level
    #     # fine-grained control over application specific protocol
    #     ...

    # @dispatcher
    # def _dispatch(self, sender: int, msg: Message) -> None:
    #     ...

    
    # @dispatcher.of(BaseActor, int, Union[Event, Request, Response])
    # def _dispatch(self, sender: int, msg: Event | Request | Response) -> None:
    #     ...


    def dispatch(self, sender: int, msg: Message) -> None:
        # self.logger.error(f'BaseActor dispatch({sender=}, {msg=})')
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
            # case Message(sig=Sig.CHILD_INIT_DONE):
            #     self.on_child_init()
            case Message(sig=Sig.CHILD_DEINIT, args=pid):
                self.child = 0
            case Message(sig=Sig.SUBSCRIBE, args=name):
                self.register(who=sender, what=to_snake_case(name))
            case Message(sig=Sig.UNSUBSCRIBE, args=name):
                self.unregister(who=sender, what=to_snake_case(name))
            case Message(sig=Sig.LOGGING, args=level):
                self.log_lvl = level
            case _:
                return
        raise SystemMessage

    def init(self) -> None:
        ...

    def on_child_init(self) -> None:
        ...

    def terminate(self) -> None:
        raise SystemExit

    def register(self, who: int, what: str) -> None:
        try:
            prop = self.__class__.__dict__[what]
        except KeyError as err:
            raise DispatchError
        if isinstance(prop, Observable):
            self.obs.register(what, who)
            value = prop.__get__(self, self.__class__)
            self.obs.notify_one(receiver=who, name=what, value=value, frame_id=4)

    def unregister(self, who: int, what: str) -> None:
        try:
            prop = self.__class__.__dict__[what]
        except KeyError as err:
            raise DispatchError
        if isinstance(prop, Observable):
            self.obs.unregister(what, who)

    def publish(self, name: str, value: Any) -> None:
        try:
            prop = self.__class__.__dict__[to_snake_case(name)]
        except KeyError:
            ...
        else:
            prop.__set__(self, value)

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

    def logmsg(self, sender: Any, receiver: Any, msg: Any) -> None:
        self.logger.log(sender=repr(ActorSystem().get_actor(sender)), receiver=repr(self), msg=repr(msg))

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



# tunnel: actor1 -> actor2 -> actor2 -> actor1
# permet de présever le pid du sender original
# forward: actor1 -> actor2 -> child -> actor1
# permet de déléguer un message à un enfant en préservant le pid du sender original
