from typing import Any, Optional, Union
from threading import Thread, Lock
import logging

from .utils import SingletonMeta
from .message import Message
from .sig import Sig
from .base_actor import BaseActor, ActorGeneric
from .registry import ActorRegistry
import sys
from .subsystems import Logging

# SIGQUIT

# QUIT

from signal import signal, SIGKILL, SIGQUIT, SIGTERM


def signal_handler(signum, frame):
    actor_system.logger.error(f'{signum=}')

# signal(SIGTERM, signal_handler)


class ActorSystem(BaseActor, metaclass=SingletonMeta):
    __pid: int = 0
    __pid_l: Lock = Lock()
    __l: Lock = Lock()

    def __init__(self) -> None:
        super().__init__(pid=ActorSystem.__pid, name=self.__class__.__name__, parent=ActorSystem.__pid)
        self._registry = ActorRegistry()
        self._registry.register(ActorSystem.__pid, self)
        self._threads: dict[int, Thread] = {}
        self.log_lvl = logging.INFO

    def send(self, receiver: Union[int, str, type], msg: Message|dict[str, Any]) -> None:
        sender = get_caller()
        recipient: Optional[BaseActor] = self._registry.lookup(receiver)
        if recipient is None:
            return sender.post(sender=self.pid, msg=Message(sig=Sig.DISPATCH_ERROR))
        else:
            return recipient.post(sender=sender.pid, msg=msg)

    def _send(
        self, 
        sender: BaseActor,
        receiver: Union[int, str, type], 
        msg: Message|dict[str, Any]
    ) -> None:
        recipient: Optional[BaseActor] = self._registry.lookup(receiver)
        if recipient is None:
            return sender.post(sender=self.pid, msg=Message(sig=Sig.DISPATCH_ERROR))
        else:
            return recipient.post(sender=sender.pid, msg=msg)

    def _create_actor(
        self, 
        cls: type, 
        *, 
        pid: int,
        parent: int,
        name: str='', 
        **kwargs
    ) -> int:
        actor = cls(pid=pid, name=name, parent=parent, **kwargs)
        t = Thread(target=actor.run, daemon=True)
        self._registry.register(pid, actor)
        self._threads.update({pid: t})
        t.start()
        self._send(self, actor.pid, Message(sig=Sig.INIT))
        return actor.pid

    def create_actor(
        self, 
        cls: type,
        *,
        name: str='',
        **kwargs
    ) -> int:
        caller = get_caller(frame_idx=3)
        pid = self.get_pid()
        return self._create_actor(cls=cls, pid=pid, parent=caller.pid, name=name, **kwargs)

    def dispatch(self, sender: int, msg: Message) -> None:
        actor: Optional[ActorGeneric]

        match msg:
            case Message(sig=Sig.INIT):
                ...

            case Message(sig=Sig.SIGQUIT):
                for pid, actor in self._registry:
                    actor.post(sender=self.pid, msg=Message(sig=Sig.SIGQUIT))
                raise SystemExit

            case Message(sig=Sig.SIGINT):
                actor = self._registry.get(sender)
                if actor is None:
                    return

                pid = self.get_pid()
                cls = actor.__class__
                name = actor.name
                parent = actor.parent
                kwargs = getattr(actor, 'kwargs')
                if kwargs is not None:
                    kwargs = kwargs.copy()
                t = self._threads.get(pid)
                if t is not None:
                    t._stop()
                self.logger.warning(f'Trying to regenerate Actor(pid={pid}, cls={cls}, parent={parent}, name={name}, kwargs={kwargs})')
                self._create_actor(cls, pid=pid, parent=parent, name=name, **kwargs)

            case Message(sig=Sig.EXIT):
                self._registry.unregister(sender)
                try:
                    t = self._threads.pop(sender)
                except KeyError:
                    t = None
                if t is not None:
                    t.join()

            case _:
                self._logger._log(sender=self.resolve_parent(sender), receiver=self.__repr__(), msg=f'Unprocessable Message: msg={msg}')
                send(self.pid, Message(sig=Sig.SIGQUIT))

    def get_pid(self) -> int:
        with ActorSystem.__pid_l:
            ActorSystem.__pid += 1
            value = ActorSystem.__pid
        return value

    def resolve_parent(self, pid: int) -> str:
        actor = self._registry.get(pid)
        return 'None' if actor is None else actor.__repr__()

    @property
    def logger(self) -> Logging:
        return self._logger

    @logger.setter
    def logger(self, value: Any) -> None:
        raise TypeError('Property is immutable')

    def get_actor(self, pid: int) -> Optional[BaseActor]:
        return self._registry.get(pid)


    @logger.setter
    def logger(self, value: Any) -> None:
        raise TypeError('Property is immutable')

def get_caller(frame_idx: int=2) -> BaseActor:
    frame = sys._getframe(frame_idx)
    arguments = frame.f_code.co_argcount
    if arguments == 0:
        return ActorSystem()
    caller_calls_self = frame.f_code.co_varnames[0]
    if not isinstance(frame.f_locals[caller_calls_self], BaseActor):
        return ActorSystem()
    return frame.f_locals[caller_calls_self]


def __get_caller(frame_idx: int=2) -> BaseActor:
    frame = sys._getframe(frame_idx)
    # ActorSystem().logger.frameinfo(frame)
    instance = frame.f_locals.get('self')
    if instance is None:
        return ActorSystem()
    actor = ActorSystem().get_actor(instance.pid)
    if actor is None:
        # Unhandled case: Actor is not present in ActorRegistry
        raise SystemExit
    return actor


def send(receiver: Union[int, str, type], msg: Message|dict[str, Any]) -> None:
    return (
        ActorSystem()
        ._send(
            sender=__get_caller(), 
            receiver=receiver, msg=msg
        )
    )


def create(cls: type, *, name: str='', **kwargs) -> int:
    return (
        ActorSystem()
        ._create_actor(
            cls=cls, 
            pid=ActorSystem().get_pid(), 
            parent=__get_caller().pid, 
            name=name, 
            **kwargs
        )
    )


actor_system = ActorSystem()