from typing import Any, TypeVar
from queue import Queue

from .message import Message


T = TypeVar('T', bound='Actor')


class Actor:
    def __init__(self) -> None:
        self.DEBUG = 0
        self.mq = Queue()
        self._addr = {}
        self.name = self.__class__.__name__

    def run(self) -> None:
        ...

    def post(self, actor: T, message: Message) -> None:
        self.mq.put((actor, message))

    def __repr__(self) -> str:
        return f'Actor(name={self.name}, ...)'
    
    def register(self, actor: T) -> None:
        if actor.name not in self._addr:
            self._addr.update({actor.name: actor})

    def get_actor(self, actor: str) -> T:
        res = self._addr.get(actor)
        if res is None:
            raise Exception(f'self={self} actor={actor} addr={self._addr}')
        return res

    def debug(self, msg: Message, actor: T) -> None:
        if self.DEBUG:
            print(f'{self=}\n{actor=}\n{msg=}\n')
