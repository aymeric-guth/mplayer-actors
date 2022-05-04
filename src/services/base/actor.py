from typing import TypeVar, Any

from .base_actor import BaseActor, ActorGeneric
from .message import Message
from .sig import Sig
from .actor_system import actor_system


T = TypeVar('T', bound='Actor')


def last_will(func):
    def inner(*args, **kwargs):
        try:
            # print(args, kwargs)
            return func(*args, **kwargs)
        except Exception as err:
            actor, *_ = args
            actor_system.send('Logger', Message(Sig.PUSH, args=f'Actor={actor} encountered a failure: {err}'))
            actor_system.post(actor, Message(sig=Sig.SIGINT, args=err))

    return inner


class Actor(BaseActor):
    def __init__(self, pid: int, name:str='', parent: T=None, **kwargs) -> None:
        super().__init__(pid, name)
        if parent is None:
            self.parent = None
        elif isinstance(parent, BaseActor):
            self.parent = parent.pid
        elif isinstance(parent, int):
            self.parent = parent
        else:
            raise SystemExit

        self.kwargs = kwargs.copy()

    def logger(self, sender: ActorGeneric, msg: Message) -> None:
        if self.LOG:
            s = actor_system.get_actor(sender)
            actor_system.send('Logger', Message(Sig.PUSH, f'sender={s!r} receiver={self!r} msg={msg!r}'))

    def log_msg(self, msg: str) ->None:
        if self.LOG:
            actor_system.send('Logger', Message(Sig.PUSH, msg))

    def handler(self, err) -> None:
        actor_system.send('Logger', Message(Sig.PUSH, args=f'Actor={self} encountered a failure: {err}'))
        actor_system.post(self, Message(sig=Sig.SIGINT, args=err))

    def introspect(self) -> dict[Any, Any]:
        return {
            'actor': repr(self),
            'log': self.LOG,
        }.copy()

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(pid={self.pid}, parent={self.parent}, kwargs={self.kwargs})'
