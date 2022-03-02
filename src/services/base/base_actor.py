from typing import TypeVar
import traceback
import sys
from queue import Queue

from .message import Message


T = TypeVar('T', bound='BaseActor')
ActorGeneric = int|str|T|type


class BaseActor:
    def __init__(self, pid: int, name:str='') -> None:
        self._pid = pid
        if name:
            self._name = name
        else:
            self._name = self.__class__.__name__
        self.DEBUG = 0
        self.mq = Queue()

    def run(self) -> None:
        while 1:
            (sender, msg) = self.mq.get()
            if self.DEBUG == 1:
                self.logger(sender, msg)
            try:
                self.dispatch(sender, msg)
            except Exception as err:
                self.handler(f'{err} {sys.exc_info()[2]}')
                raise SystemExit
            else:
                self.mq.task_done()

    def dispatch(self, sender: ActorGeneric, msg: Message) -> None:
        ...
    
    def handler(self, err) -> None:
        ...

    def post(self, sender: ActorGeneric, msg: Message) -> None:
        self.mq.put((sender, msg))

    def logger(self, sender: ActorGeneric, msg: Message) -> None:
        ...

    def __hash__(self) -> int:
        return self.pid

    @property
    def pid(self) -> int:
        return self._pid

    @pid.setter
    def pid(self, value) -> None:
        raise TypeError

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        raise TypeError

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(pid={self.pid})'
        # return f'{self.__class__.__name__}(pid={self.pid}, name={self.name}, ...)'
