from typing import Any, Optional, Union
from threading import Thread, Lock
import logging

from .utils import SingletonMeta
from .message import Message
from .sig import Sig
from .base_actor import BaseActor, ActorGeneric
import sys

# SIGQUIT

# QUIT

from signal import signal, SIGKILL, SIGQUIT, SIGTERM


def signal_handler(signum, frame):
    actor_system.logger.error(f'{signum=}')

# signal(SIGTERM, signal_handler)


class ActorSystem(BaseActor, metaclass=SingletonMeta):
    __pid: int = 0
    __pid_l: Lock = Lock()

    def __init__(self) -> None:
        super().__init__(pid=ActorSystem.__pid, name=self.__class__.__name__, parent=ActorSystem.__pid)
        self._registry: dict[int, BaseActor] = {ActorSystem.__pid: self}
        self._threads: dict[int, Thread] = {}
        self.log_lvl = logging.ERROR

    def send(self, receiver: Union[int, str, type], msg: Message|dict[str, Any]) -> None:
        sender = get_caller()
        recipient: Optional[BaseActor] = self._get_actor(receiver)
        if recipient is None:
            return sender.post(sender=self.pid, msg=Message(sig=Sig.DISPATCH_ERROR))
        else:
            return recipient.post(sender=sender.pid, msg=msg)            

    def _get_actor(self, actor: ActorGeneric) -> Optional[BaseActor]:
        '''
        renvoie l'instance d'un acteur
        valeurs possibles pour récupérer l'instance d'un acteur:
        pid (int)
        nom (str)
        nom de classe (str)
        classe (type)
        instance (BaseActor)
        '''

        match actor:
            case actor if isinstance(actor, int):
                return self._registry.get(actor)

            case actor if isinstance(actor, str):
                func = lambda a: actor == a.name

            case actor if isinstance(actor, type) and issubclass(actor, BaseActor):
                func = lambda a: actor is a.__class__

            case actor if isinstance(actor, BaseActor):
                func = lambda a: actor is a

            case actor if actor is None:
                return None

            case _:
                self.logger.error(f'Unhandled case: actor={actor!r}')
                raise SystemExit

        for k, v in self._registry.items():
            if func(v):
                return v
        else:
            return None

    def _create_actor(
        self, 
        cls: type, 
        *, 
        pid: int,
        parent: int,
        name: str='', 
        **kwargs
    ) -> int:
        # self.logger.error(f'parent={self.resolve_parent(parent)} requested Actor({cls.__name__}) creation')
        actor = cls(pid=pid, name=name, parent=parent, **kwargs)
        t = Thread(target=actor.run, daemon=True)
        self._registry.update({pid: actor})
        self._threads.update({pid: t})
        t.start()
        return actor.pid

    def create_actor(
        self, 
        cls: type,
        *,
        name: str='',
        **kwargs
    ) -> int:
        caller = self.get_caller()
        pid = self.get_pid()
        return self._create_actor(cls=cls, pid=pid, parent=caller.pid, name=name, **kwargs)

    def dispatch(self, sender: int, msg: Message) -> None:
        actor: Optional[ActorGeneric]

        match msg:
            case Message(sig=Sig.INIT):
                ...

            case Message(sig=Sig.SIGQUIT):
                for pid, actor in self._registry.items():
                    actor.post(sender=self.pid, msg=Message(sig=Sig.SIGQUIT))
                raise SystemExit

            case Message(sig=Sig.SIGINT):
                actor = self._get_actor(sender)
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
                try:
                    actor = self._registry.pop(sender)
                except KeyError:
                    actor = None
                try:
                    t = self._threads.pop(sender)
                except KeyError:
                    t = None
                if t is not None:
                    t.join()

            case Message(sig=Sig.ERROR):
                ...

            case _:
                self.logger.error(f'Unprocessable Message: msg={msg}')
                # self.post(Message(sig=Sig.SIGQUIT))

    def get_pid(self) -> int:
        with ActorSystem.__pid_l:
            ActorSystem.__pid += 1
            value = ActorSystem.__pid
        return value

    def get_caller(self) -> BaseActor:
        frame = sys._getframe(2)
        arguments = frame.f_code.co_argcount
        if arguments == 0:
            return self
        caller_calls_self = frame.f_code.co_varnames[0]
        return frame.f_locals[caller_calls_self]

    def resolve_parent(self, pid: int) -> str:
        actor = self._registry.get(pid)
        return 'None' if actor is None else actor.__repr__()

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


def get_caller() -> BaseActor:
    frame = sys._getframe(2)
    arguments = frame.f_code.co_argcount
    if arguments == 0:
        return ActorSystem()
    caller_calls_self = frame.f_code.co_varnames[0]
    if not isinstance(frame.f_locals[caller_calls_self], BaseActor):
        ActorSystem().logger.info(f'Non-Actor caller={frame.f_code.co_varnames}')
        return ActorSystem()
    return frame.f_locals[caller_calls_self]



actor_system = ActorSystem()