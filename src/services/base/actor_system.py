from typing import Any
from threading import Thread, Lock
from queue import Queue
from functools import wraps
from venv import create

from .utils import SingletonMeta
from .message import Message
from .sig import Sig
from .base_actor import BaseActor, ActorGeneric
import sys


def inject_caller(func):
    @wraps(func)
    def inner(self, *args, **kwargs):
        frame = sys._getframe(1)
        arguments = frame.f_code.co_argcount
        if arguments == 0:
            return func(self, None, *args, **kwargs)
        caller_calls_self = frame.f_code.co_varnames[0]
        caller = frame.f_locals[caller_calls_self]
        return func(self, caller, *args, **kwargs)

    return inner


class ActorSystem(BaseActor, metaclass=SingletonMeta):
    pid = 0
    pid_l = Lock()

    def __init__(self, pid: int=0, name: str='') -> None:
        super().__init__(pid, name)
        self.LOG = 0
        self._registry: dict[int, BaseActor] = {}
        self._threads: dict[int, Thread] = {}
        self.mq: Queue[tuple[BaseActor, Message]] = Queue()
        # remontage d'un acteur qui a quité?

    @inject_caller
    def send(self, sender: ActorGeneric, receiver: ActorGeneric, msg: Message) -> None:
        '''
        (sender) envoie un message à un acteur (receiver)
        '''        
        s = self.get_actor(sender)
        r = self.get_actor(receiver)
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
                print(f'Unhandled case: {actor=}')
                raise Exception

        for k, v in self._registry.items():
            if func(v):
                return v
        else:
            return None

    @inject_caller
    def create_actor(
        self, 
        parent: BaseActor, 
        cls: type, 
        *, 
        name='', 
        pid: int=-1,
        **kwargs
    ) -> BaseActor:
        if pid <= -1:
            pid = ActorSystem.get_pid()
        actor = cls(pid=pid, name=name, parent=parent, **kwargs)
        t = Thread(target=actor.run, daemon=True)
        self._registry.update({pid: actor})
        self._threads.update({pid: t})
        t.start()
        # self.send('Logger', Message(Sig.PUSH, f'Successfully regenerated {actor}'))
        return actor

    def dispatch(self, sender: BaseActor, msg: Message) -> None:
        match msg:
            case Message(sig=Sig.SIGINT):
                pid = sender.pid
                cls = sender.__class__
                parent = sender.parent
                kwargs = sender.kwargs.copy()
                name = sender.name

                t = self._threads.get(pid)
                t._stop()
                self.send('Logger', Message(Sig.PUSH, f'Trying to regenerate Actor(pid={pid}, cls={cls}, parent={parent}, name={name}, kwargs={kwargs})'))
                return self.create_actor(cls, name=name, pid=pid, **kwargs)

    @staticmethod
    def get_pid() -> int:
        with ActorSystem.pid_l:
            value = ActorSystem.pid
            ActorSystem.pid += 1
        return value


actor_system = ActorSystem(pid=ActorSystem.get_pid())