from threading import Thread, Lock
from functools import wraps

from .utils import SingletonMeta
from .message import Message
from .sig import Sig
from .base_actor import BaseActor
import sys


ActorGeneric = int|str|BaseActor|type


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


def sanity_check(func):
    @wraps(func)
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            raise
            # actor, *_ = args
            # actor_system.create_actor(actor.__class__)
            # actor_system.terminate(actor)
    return inner


class ActorSystem(metaclass=SingletonMeta):
    pid = 0
    pid_l = Lock()

    def __init__(self) -> None:
        self._registry: dict[int, BaseActor] = {}
        self._threads: dict[int, Thread] = {}
        self.pid = self.get_pid()
        # remontage d'un acteur qui a quité?

    @inject_caller
    def send(self, sender: ActorGeneric, receiver: ActorGeneric, msg: Message) -> None:
        '''
        (sender) envoie un message à un acteur (receiver)
        '''        
        r = self.get_actor(receiver)
        s = self.get_actor(sender)
        match [s, r]:
            case [None, None]:
                # sender = main thread, receiver = does not exists
                ...
            case [a, None]:
                # sender = actor, receiver = does not exists
                s.post(sender=None, msg=Message(sig=Sig.DISPATCH_ERROR))
            case [None, b]:
                # sender = main thread, receiver = actor
                r.post(sender=None, msg=msg)
            case [a, b]:
                # sender = actor, receiver = actor
                r.post(sender=s.pid, msg=msg)

    def get_actor(self, actor: ActorGeneric) -> BaseActor:
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
                if self.DEBUG: print(f'get_actor matched pid: {actor=}')
                return self._registry.get(actor)

            case actor if isinstance(actor, str):
                if self.DEBUG: print(f'get_actor matched name|classname: {actor=}')
                func = lambda a: actor == a.name

            case actor if isinstance(actor, type) and issubclass(actor, BaseActor):
                if self.DEBUG: print(f'get_actor matched class: {actor=}')
                func = lambda a: actor is a.__class__

            case actor if isinstance(actor, BaseActor):
                if self.DEBUG: print(f'get_actor matched instance: {actor=}')
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
        **kwargs
    ) -> BaseActor:
        pid = self.get_pid()
        actor = cls(pid=pid, name=name, parent=parent, **kwargs)
        t = Thread(target=actor.run, daemon=True)
        self._registry.update({pid: actor})
        self._threads.update({pid: t})
        t.start()
        return actor

    def terminate(self, actor: BaseActor) -> None:
        a = self.get_actor(actor)
        if a is not None:
            t = self._threads.get(a.pid)
            t.stop()
            t = None
            a = None

    def get_pid(self) -> int:
        with ActorSystem.pid_l:
            value = ActorSystem.pid
            ActorSystem.pid += 1
        return value

    def __del__(self) -> None:
        for pid, actor in self._registry.items():
            t = self._threads.get(pid)
            if t is not None:
                t.stop()


actor_system = ActorSystem()