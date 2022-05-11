from typing import Any, Optional 
from threading import Thread, Lock
from queue import Queue
from functools import wraps
import logging

from .utils import SingletonMeta
from .message import Message
from .sig import Sig
from .base_actor import BaseActor, ActorGeneric
import sys


class ActorSystem(BaseActor, metaclass=SingletonMeta):
    pid: int = 0
    pid_l: Lock = Lock()
    # rid: int = 0
    # rid_l: Lock = Lock()

    def __init__(self, pid: int=0, name: str='') -> None:
        super().__init__(pid, name)
        self.LOG = 0
        self._registry: dict[int, BaseActor] = {}
        self._threads: dict[int, Thread] = {}
        self.mq: Queue[tuple[BaseActor, Message]] = Queue()
        self.init_logger(__name__)
        self.log_lvl = logging.INFO

    def send(self, receiver: ActorGeneric, msg: Message) -> None:
        '''
        (sender) envoie un message à un acteur (receiver)
        '''
        caller = self.get_caller()
        s: Optional[BaseActor] = self.get_actor(caller)
        r: Optional[BaseActor] = self.get_actor(receiver)
        match [s, r]:
            case [None, None]:
                # sender = main thread, receiver = does not exists
                ...
            case [a, None]:
                # sender = actor, receiver = does not exists
                if isinstance(receiver, type):
                    actor = self.create_actor(receiver)
                    actor.post(sender=s, msg=msg)
                else:
                    s.post(sender=None, msg=Message(sig=Sig.DISPATCH_ERROR))
            case [None, b]:
                # sender = main thread, receiver = actor
                r.post(sender=None, msg=msg)
            case [a, b]:
                # sender = actor, receiver = actor
                r.post(sender=s.pid, msg=msg)

    def get_actor(self, actor: ActorGeneric) -> BaseActor|None:
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
                if self.LOG: print(f'get_actor matched pid: {actor=}')
                return self._registry.get(actor)

            case actor if isinstance(actor, str):
                if self.LOG: print(f'get_actor matched name|classname: {actor=}')
                func = lambda a: actor == a.name

            case actor if isinstance(actor, type) and issubclass(actor, BaseActor):
                if self.LOG: print(f'get_actor matched class: {actor=}')
                func = lambda a: actor is a.__class__

            case actor if isinstance(actor, BaseActor):
                if self.LOG: print(f'get_actor matched instance: {actor=}')
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

    def create_actor(
        self, 
        cls: type, 
        *, 
        name='', 
        pid: int=-1,
        **kwargs
    ) -> BaseActor:
        caller = self.get_caller()
        if pid <= -1:
            pid = ActorSystem.get_pid()
        parent = self.get_actor(caller)
        actor = cls(pid=pid, name=name, parent=parent, **kwargs)
        self.logger.warning(f'parent={parent} requested create_actor({cls})')
        t = Thread(target=actor.run, daemon=True)
        self._registry.update({pid: actor})
        self._threads.update({pid: t})
        t.start()
        return actor

    def dispatch(self, sender: ActorGeneric, msg: Message) -> None:
        s = self.get_actor(sender)
        if s is None: return
        match msg:
            case Message(sig=Sig.SIGINT):
                pid = s.pid
                cls = s.__class__
                name = s.name
                parent = getattr(s, 'parent')
                kwargs = getattr(s, 'kwargs')
                if kwargs is not None:
                    kwargs = kwargs.copy()

                t = self._threads.get(pid)
                if t is not None:
                    t._stop()
                self.logger.warning(f'Trying to regenerate Actor(pid={pid}, cls={cls}, parent={parent}, name={name}, kwargs={kwargs})')
                self.create_actor(cls, name=name, pid=pid, **kwargs)

    @staticmethod
    def get_pid() -> int:
        with ActorSystem.pid_l:
            value = ActorSystem.pid
            ActorSystem.pid += 1
        return value

    def get_caller(self) -> Optional[ActorGeneric]:
        frame = sys._getframe(2)
        arguments = frame.f_code.co_argcount
        if arguments == 0:
            return None
        caller_calls_self = frame.f_code.co_varnames[0]
        return frame.f_locals[caller_calls_self]


actor_system = ActorSystem(pid=ActorSystem.get_pid())