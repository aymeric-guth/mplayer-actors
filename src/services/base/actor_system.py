from typing import Any, Optional 
from threading import Thread, Lock
import logging

from .utils import SingletonMeta
from .message import Message
from .sig import Sig
from .base_actor import BaseActor, ActorGeneric
import sys


class ActorSystem(BaseActor, metaclass=SingletonMeta):
    __pid: int = 0
    __pid_l: Lock = Lock()

    def __init__(self) -> None:
        super().__init__(pid=ActorSystem.__pid, name=self.__class__.__name__, parent=self)
        self._registry: dict[int, BaseActor] = {}
        self._threads: dict[int, Thread] = {}
        self.log_lvl = logging.ERROR

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

    def get_actor(self, actor: ActorGeneric) -> Optional[BaseActor]:
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
        parent: BaseActor,
        name: str='', 
        **kwargs
    ) -> BaseActor:
        self.logger.info(f'parent={parent} requested Actor({cls.__name__}) creation')
        actor = cls(pid=pid, name=name, parent=parent, **kwargs)
        t = Thread(target=actor.run, daemon=True)
        self._registry.update({pid: actor})
        self._threads.update({pid: t})
        t.start()
        return actor

    def create_actor(
        self, 
        cls: type,
        *,
        name: str='',
        **kwargs
    ) -> BaseActor:
        caller = self.get_caller()
        pid = self.get_pid()
        return self._create_actor(cls=cls, pid=pid, parent=caller, name=name, **kwargs)

    def dispatch(self, sender: ActorGeneric, msg: Message) -> None:
        self.logger.error(f'{msg=}')
        # s = self.get_actor(sender)
        # if s is None: return

        match msg:
            case Message(sig=Sig.INIT):
                ...

            case Message(sig=Sig.SIGQUIT):
                for pid, actor in self._registry.items():
                    actor.post(msg=Message(sig=Sig.SIGQUIT), sender=self)
                raise SystemExit

            case Message(sig=Sig.SIGINT):
                pid = sender.pid
                cls = sender.__class__
                name = sender.name
                parent = sender.parent
                kwargs = getattr(sender, 'kwargs')
                if kwargs is not None:
                    kwargs = kwargs.copy()

                t = self._threads.get(pid)
                if t is not None:
                    t._stop()
                self.logger.warning(f'Trying to regenerate Actor(pid={pid}, cls={cls}, parent={parent}, name={name}, kwargs={kwargs})')
                self._create_actor(cls, pid=pid, parent=parent, name=name, **kwargs)

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

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(pid={self.pid})'


actor_system = ActorSystem()