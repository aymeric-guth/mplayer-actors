from typing import Any, Optional, Union, Callable
from threading import Thread, Lock
import threading
import logging
import time
from functools import singledispatch, wraps

from ...utils import SingletonMeta
from .message import Message, MsgCtx, Event, Request, Response
from .errors import ActorNotFound
from .sig import Sig
from .base_actor import BaseActor, ActorGeneric
from .registry import ActorRegistry
import sys
from .subsystems import Logging
from ...utils import defer


def thread_handler(func):
    @wraps(func)
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        # except SystemExit as err:
        except Exception as err:
            ActorSystem().logger.error(f'{func.__name__} {err=}')
        finally:
            ...
            # ActorSystem().logger.error(f'{func.__name__} terminated')
    return inner


class ActorSystem(BaseActor, metaclass=SingletonMeta):
    __pid: int = 0
    __pid_l: Lock = Lock()

    def __init__(self) -> None:
        super().__init__(pid=ActorSystem.__pid, name=self.__class__.__name__, parent=ActorSystem.__pid)
        self._registry = ActorRegistry()
        self._threads: dict[int, Thread] = {}
        self._childs: list[int] = []
        self.log_lvl = logging.ERROR
        # self.log_lvl = logging.INFO

        self._registry.register(self.pid, self)
        _t = Thread(target=self.run, daemon=True)
        _t.start()
        self._threads.update({self.pid: _t})

    def _send(
        self, 
        sender: BaseActor,
        receiver: Union[int, str, type], 
        msg: Message|dict[str, Any]
    ) -> None:
        recipient: Optional[BaseActor] = self._registry.lookup(receiver)
        # self.logger.error(f'from={sender} to={recipient} what={msg}')
        if recipient is None:
            return self._post(
                sender=self.pid, 
                msg=Event(
                    type='system', 
                    name='recipient-unknown', 
                    args=MsgCtx(
                        original_sender=sender.pid,
                        original_recipient=receiver,
                        message=msg
                    )
                )
            )
            # return sender._post(self.pid, Message(sig=Sig.DISPATCH_ERROR))
        else:
            return recipient._post(sender=sender.pid, msg=msg)

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
        _t = Thread(target=actor.run, daemon=True)
        self._registry.register(pid, actor)
        self._threads.update({pid: _t})
        _t.start()
        self._send(self, actor.parent, Message(sig=Sig.CHILD_INIT, args=actor.pid))
        return actor.pid

    def dispatch(self, sender: int, msg: Message) -> None:
        actor: Optional[ActorGeneric]

        self.logger.log(sender=repr(ActorSystem().get_actor(sender)), receiver=repr(self), msg=repr(msg))
        match msg:
            case Message(sig=Sig.INIT):
                ...
            
            case Message(sig=Sig.CHILD_INIT, args=args):
                # self.logger.error(f'Initilizing child={self.resolve_parent(args)}')
                self._childs.append(args)
                send(to=args, what=Message(sig=Sig.INIT))

            case Message(sig=Sig.CHILD_DEINIT, args=args):
                self._childs.remove(args)

            case Message(sig=Sig.SIGKILL):
                while len(self._registry) > 1:
                    # self.logger.error(str(self._registry) + f'{len(self._registry)=}')
                    time.sleep(0.1)

                actor = self._registry.get(self.pid)
                if actor is not None:
                    self._registry.unregister(actor.pid)
                _t = self._threads.get(self.pid)
                if _t is not None:
                    del self._threads[self.pid]
                raise SystemExit

            case Message(sig=Sig.SIGQUIT):
                self.terminate()

            case Message(sig=Sig.SIGINT):
                actor = self._registry.get(sender)
                if actor is None:
                    return
                self._registry.unregister(actor.pid)
                pid = self.get_pid()
                cls = actor.__class__
                name = actor.name
                parent = actor.parent
                child = self.get_actor(actor.child)
                if child is not None and child.pid:
                    self._send(sender=child, receiver=self.pid, msg=Message(sig=Sig.EXIT))
                kwargs = getattr(actor, 'kwargs')
                if kwargs is not None:
                    kwargs = kwargs.copy()
                t = self._threads.get(pid)
                if t is not None:
                    t.join()
                    del self._threads[pid]
                self.logger.error(f'Trying to regenerate Actor(pid={pid}, cls={cls}, parent={parent}, name={name}, kwargs={kwargs})')   
                self._create_actor(cls, pid=pid, parent=parent, name=name, **kwargs)

            case Message(sig=Sig.EXIT):
                actor = self.get_actor(sender)
                if actor is not None:
                    self._send(self, actor.parent, Message(sig=Sig.CHILD_DEINIT, args=actor.pid))                       
                    self._registry.unregister(actor.pid)

                _t = self._threads.get(sender)
                if _t is not None:
                    del self._threads[sender]
                    _t.join()

            case Message(
                sig=Sig.DISPATCH_ERROR, 
                args=MsgCtx(
                    original_sender=sender, 
                    original_recipient=recipient, 
                    message=message
                )
            ):
                s = self.get_actor(sender)
                if s is None: 
                    return
                r = self._registry.lookup(recipient)
                if r is None: 
                    # renvoyer le message au sender?
                    return
                if not r.child: 
                    # renvoyer le message au sender?
                    return
                self._send(sender=s, receiver=r.child, msg=message)                

            case Message(sig=Sig.CHILD_INIT_DONE):
                ...

            case Event(type='system', name='recipient-unknown', args=msg):
                actor = self.get_actor(msg.original_sender)
                if actor is None:
                    return

                match msg:
                    case MsgCtx(original_sender=sender, original_recipient=recipient, message=args) if isinstance(recipient, int):
                        self._send(sender=self, receiver=actor.pid, msg=Message(sig=Sig.DISPATCH_ERROR))
                    case MsgCtx(original_sender=sender, original_recipient=recipient, message=args) if isinstance(recipient, str) or isinstance(recipient, type):
                        # self.logger.error(f'{msg=} {actor=}, {recipient=}, {args=}')
                        defer(lambda: self._send(sender=actor, receiver=recipient, msg=args), logger=ActorSystem().logger)

            case _:
                self.logger.error(f'Unprocessable Message={msg} from={self.get_actor(sender)}')
                # send(self.pid, Message(sig=Sig.SIGQUIT))

    def get_pid(self) -> int:
        with ActorSystem.__pid_l:
            ActorSystem.__pid += 1
            value = ActorSystem.__pid
        return value

    def resolve_parent(self, pid: int) -> str:
        actor = self._registry.get(pid)
        return 'None' if actor is None else actor.__repr__()

    def get_actor(self, pid: int) -> Optional[BaseActor]:
        return self._registry.get(pid)

    def terminate(self) -> None:
        for pid in self._childs:
            self._send(self, pid, Message(sig=Sig.EXIT))
        self._post(self.pid, Message(sig=Sig.SIGKILL))

    def sysexit_handler(self) -> None:
        raise SystemExit


def __get_caller(frame_idx: int=2) -> BaseActor:
    frame = sys._getframe(frame_idx)
    instance = frame.f_locals.get('self')
    if instance is None:
        return ActorSystem()
    actor = ActorSystem().get_actor(instance.pid)
    if actor is None:
        # Unhandled case: Actor is not present in ActorRegistry
        # ActorSystem().logger.frameinfo(frame)
        # ActorSystem().logger.error(instance)
        # ActorSystem().logger.error(ActorSystem()._registry)
        # ActorSystem().logger.frameinfo(sys._getframe(frame_idx-1))
        raise SystemExit
    return actor

def _get_caller(frame_idx: int=2) -> BaseActor:
    frame = sys._getframe(frame_idx)
    instance = frame.f_locals.get('self')
    if instance is None:
        return ActorSystem()
    actor = ActorSystem().get_actor(instance.pid)
    if actor is None:
        # Unhandled case: Actor is not present in ActorRegistry
        # ActorSystem().logger.frameinfo(frame)
        # ActorSystem().logger.error(instance)
        # ActorSystem().logger.error(ActorSystem()._registry)
        # ActorSystem().logger.frameinfo(sys._getframe(frame_idx-1))
        raise SystemExit
    return actor


def send(to: Union[int, str, type], what: Any) -> None:
    caller = __get_caller()
    # ActorSystem().logger.error(f'from={caller} to={ActorSystem()._registry.lookup(to)} what={what}')
    # ActorNotFound
    return (
        ActorSystem()
        ._send(
            sender=caller, 
            receiver=to, 
            msg=what
        )
    )


def forward(sender: int, receiver: int, msg: Any) -> None:
    op = ActorSystem().get_actor(sender)
    s = __get_caller()
    target = ActorSystem()._registry.lookup(receiver)
    if op is not None and target is not None: # null check
        if s.pid == target.parent: # parent - child check
            return ActorSystem()._send(sender=op, receiver=target.pid, msg=msg)
    return send(sender, Message(Sig.DISPATCH_ERROR))


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